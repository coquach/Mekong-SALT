"""Incident management services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.salinity_units import dsm_to_gl
from app.core.exceptions import AppException
from app.models.enums import AuditEventType, IncidentStatus, RiskLevel
from app.models.incident import Incident
from app.models.risk import RiskAssessment
from app.repositories.incident import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.audit_service import write_audit_log
from app.services.db import append_domain_event_and_dispatch
from app.services.notify import get_domain_event_notification_dispatcher

INCIDENT_RISK_LEVELS = {RiskLevel.WARNING, RiskLevel.DANGER, RiskLevel.CRITICAL}

_RISK_LEVEL_LABELS_VI = {
    RiskLevel.WARNING.value: "cảnh báo",
    RiskLevel.DANGER.value: "nguy hiểm",
    RiskLevel.CRITICAL.value: "khẩn cấp",
}


async def _emit_incident_opened_notification_event(
    session: AsyncSession,
    *,
    incident: Incident,
) -> None:
    await append_domain_event_and_dispatch(
        session,
        event_type="notification.incident_created",
        source="incident-service",
        summary=f"Đã mở sự cố độ mặn {_localize_risk_level_label(incident.severity.value)}",
        payload={
            "event": "incident_created",
            "subject": f"Đã mở sự cố độ mặn {_localize_risk_level_label(incident.severity.value)}",
            "message": f"Sự cố '{incident.title}' đã được mở từ nguồn '{incident.source}'.",
            "channels": ["dashboard", "sms_mock", "zalo_mock", "email_mock"],
            "details": {
                "severity": incident.severity.value,
                "title": incident.title,
                "source": incident.source,
            },
        },
        aggregate_type="incident",
        aggregate_id=incident.id,
        region_id=incident.region_id,
        incident_id=incident.id,
        dispatcher=get_domain_event_notification_dispatcher(),
    )


@dataclass(slots=True)
class IncidentDecisionResult:
    """Decision outcome for incident creation or reuse."""

    incident: Incident | None
    decision: str
    reason: str


async def create_incident(
    session: AsyncSession,
    payload: IncidentCreate,
    *,
    actor_name: str = "system",
) -> Incident:
    """Create a manual incident."""
    incident = Incident(
        region_id=payload.region_id,
        station_id=payload.station_id,
        risk_assessment_id=payload.risk_assessment_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=IncidentStatus.OPEN,
        source=payload.source,
        evidence=payload.evidence,
        opened_at=datetime.now(UTC),
        created_by=actor_name,
    )
    await IncidentRepository(session).add(incident)
    await write_audit_log(
        session,
        event_type=AuditEventType.INCIDENT,
        actor_name=actor_name,
        region_id=incident.region_id,
        incident_id=incident.id,
        summary=f"Đã tạo sự cố: {incident.title}",
        payload={"severity": incident.severity.value, "source": incident.source},
    )
    await _emit_incident_opened_notification_event(session, incident=incident)
    await session.commit()
    await session.refresh(incident)
    return incident


def _localize_risk_level_label(value: str) -> str:
    text = str(value).strip().lower()
    return _RISK_LEVEL_LABELS_VI.get(text, text)


async def ensure_incident_for_assessment(
    session: AsyncSession,
    assessment: RiskAssessment,
    *,
    actor_name: str = "risk-engine",
) -> IncidentDecisionResult:
    """Create or reuse an active incident for a significant risk assessment."""
    if assessment.risk_level not in INCIDENT_RISK_LEVELS:
        return IncidentDecisionResult(
            incident=None,
            decision="skipped",
            reason=f"Mức rủi ro '{assessment.risk_level.value}' thấp hơn ngưỡng tạo sự cố.",
        )

    repo = IncidentRepository(session)
    if assessment.id is not None:
        existing = await repo.get_open_for_assessment(assessment.id)
        if existing is not None:
            return IncidentDecisionResult(
                incident=existing,
                decision="existing",
                reason="Đã có sự cố đang mở gắn với đánh giá rủi ro này.",
            )
    existing = await repo.get_open_by_region_and_severity(
        assessment.region_id,
        assessment.risk_level,
    )
    if existing is not None:
        return IncidentDecisionResult(
            incident=existing,
            decision="existing",
            reason="Đã tồn tại sự cố đang mở cùng vùng và cùng mức độ.",
        )

    incident = Incident(
        region_id=assessment.region_id,
        station_id=assessment.station_id,
        risk_assessment_id=assessment.id,
        title=f"{assessment.risk_level.value.title()} salinity incident",
        description=assessment.summary,
        severity=assessment.risk_level,
        status=IncidentStatus.OPEN,
        source="risk_engine",
        evidence={
            "risk_assessment_id": str(assessment.id),
            "salinity_dsm": str(assessment.salinity_dsm) if assessment.salinity_dsm is not None else None,
            "salinity_gl": (
                str(dsm_to_gl(assessment.salinity_dsm))
                if assessment.salinity_dsm is not None
                else None
            ),
            "trend_direction": assessment.trend_direction.value,
            "trend_delta_dsm": str(assessment.trend_delta_dsm) if assessment.trend_delta_dsm is not None else None,
            "trend_delta_gl": (
                str(dsm_to_gl(assessment.trend_delta_dsm))
                if assessment.trend_delta_dsm is not None
                else None
            ),
            "rationale": assessment.rationale,
        },
        opened_at=datetime.now(UTC),
        created_by=actor_name,
    )
    await repo.add(incident)
    await write_audit_log(
        session,
        event_type=AuditEventType.INCIDENT,
        actor_name=actor_name,
        region_id=incident.region_id,
        incident_id=incident.id,
        summary=f"Đã mở sự cố từ đánh giá rủi ro {assessment.id}.",
        payload=incident.evidence,
    )
    await _emit_incident_opened_notification_event(session, incident=incident)
    return IncidentDecisionResult(
        incident=incident,
        decision="created",
        reason="Mức rủi ro đạt ngưỡng và chưa có sự cố đang mở phù hợp.",
    )


async def list_incidents(
    session: AsyncSession,
    *,
    status: IncidentStatus | None = None,
    region_id: UUID | None = None,
    limit: int = 100,
) -> list[Incident]:
    """List incidents for API views."""
    return await IncidentRepository(session).list_recent(
        status=status,
        region_id=region_id,
        limit=limit,
    )


async def get_incident(session: AsyncSession, incident_id: UUID) -> Incident:
    """Load an incident or raise a 404."""
    incident = await IncidentRepository(session).get(incident_id)
    if incident is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="incident_not_found",
            message=f"Không tìm thấy sự cố '{incident_id}'.",
        )
    return incident


async def update_incident_status(
    session: AsyncSession,
    incident_id: UUID,
    payload: IncidentUpdate,
    *,
    actor_name: str = "system",
) -> Incident:
    """Update an incident lifecycle state."""
    incident = await get_incident(session, incident_id)
    incident.status = payload.status
    now = datetime.now(UTC)
    if payload.status in {IncidentStatus.INVESTIGATING, IncidentStatus.PENDING_PLAN}:
        incident.acknowledged_at = incident.acknowledged_at or now
    if payload.status in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}:
        incident.resolved_at = now
    await write_audit_log(
        session,
        event_type=AuditEventType.INCIDENT,
        actor_name=actor_name,
        region_id=incident.region_id,
        incident_id=incident.id,
        summary=f"Đã cập nhật trạng thái sự cố sang {payload.status.value}.",
        payload={"note": payload.note},
    )
    await session.commit()
    await session.refresh(incident)
    return incident
