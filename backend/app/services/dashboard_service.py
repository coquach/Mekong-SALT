"""Dashboard aggregation service."""

from __future__ import annotations

from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.salinity_units import dsm_to_gl
from app.models.agent_run import AgentRun
from app.models.action import ActionExecution, ActionPlan
from app.models.enums import ActionPlanStatus, IncidentStatus, NotificationChannel, NotificationStatus
from app.models.incident import Incident
from app.models.notification import Notification
from app.models.risk import RiskAssessment
from app.models.sensor import SensorReading
from app.schemas.dashboard import (
    DashboardEarthEngineLatest,
    DashboardSummary,
    DashboardTimeline,
    DashboardTimelineItem,
)


async def get_dashboard_summary(session: AsyncSession) -> DashboardSummary:
    """Build a compact operational dashboard summary."""
    open_incidents = await session.scalar(
        select(func.count()).select_from(Incident).where(
            Incident.status.not_in([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
        )
    )
    pending_approvals = await session.scalar(
        select(func.count()).select_from(ActionPlan).where(
            ActionPlan.status == ActionPlanStatus.PENDING_APPROVAL
        )
    )
    active_notifications = await session.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SENT]),
        )
    )
    today_start = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    simulated_executions_today = await session.scalar(
        select(func.count()).select_from(ActionExecution).where(
            ActionExecution.started_at >= today_start
        )
    )

    latest_reading = (
        await session.scalars(
            select(SensorReading)
            .options(selectinload(SensorReading.station))
            .order_by(SensorReading.recorded_at.desc(), SensorReading.created_at.desc())
            .limit(1)
        )
    ).first()
    latest_risk = (
        await session.scalars(
            select(RiskAssessment)
            .order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.created_at.desc())
            .limit(1)
        )
    ).first()

    return DashboardSummary(
        open_incidents=int(open_incidents or 0),
        pending_approvals=int(pending_approvals or 0),
        active_notifications=int(active_notifications or 0),
        latest_risk_level=latest_risk.risk_level.value if latest_risk is not None else None,
        latest_salinity_dsm=str(latest_reading.salinity_dsm) if latest_reading is not None else None,
        latest_salinity_gl=(
            str(dsm_to_gl(latest_reading.salinity_dsm))
            if latest_reading is not None
            else None
        ),
        latest_station_code=latest_reading.station.code if latest_reading is not None and latest_reading.station is not None else None,
        simulated_executions_today=int(simulated_executions_today or 0),
    )


async def get_dashboard_timeline(session: AsyncSession, *, limit: int = 72) -> DashboardTimeline:
    """Return recent risk assessments as a chart-friendly timeline."""
    assessments = list(
        (
            await session.scalars(
                select(RiskAssessment)
                .options(selectinload(RiskAssessment.station))
                .order_by(desc(RiskAssessment.assessed_at), desc(RiskAssessment.created_at))
                .limit(limit)
            )
        ).all()
    )

    # Oldest -> newest ordering is easier for FE chart rendering.
    assessments.reverse()
    items = [
        DashboardTimelineItem(
            assessed_at=assessment.assessed_at,
            station_code=assessment.station.code if assessment.station is not None else None,
            risk_level=assessment.risk_level.value,
            salinity_dsm=str(assessment.salinity_dsm) if assessment.salinity_dsm is not None else None,
            salinity_gl=(
                str(dsm_to_gl(assessment.salinity_dsm))
                if assessment.salinity_dsm is not None
                else None
            ),
        )
        for assessment in assessments
    ]
    return DashboardTimeline(items=items, count=len(items))


async def get_latest_earth_engine_context(
    session: AsyncSession,
    *,
    station_id: UUID | None = None,
    region_id: UUID | None = None,
    limit: int = 200,
) -> DashboardEarthEngineLatest:
    """Return latest captured Earth Engine context from planning snapshots."""
    statement = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.observation_snapshot),
            selectinload(AgentRun.station),
            selectinload(AgentRun.region),
        )
        .where(AgentRun.run_type == "plan_generation")
        .order_by(desc(AgentRun.started_at), desc(AgentRun.created_at))
        .limit(limit)
    )
    if station_id is not None:
        statement = statement.where(AgentRun.station_id == station_id)
    if region_id is not None:
        statement = statement.where(AgentRun.region_id == region_id)

    runs = list((await session.scalars(statement)).all())
    for run in runs:
        snapshot = run.observation_snapshot
        if snapshot is None:
            continue
        payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
        context = payload.get("earth_engine_context")
        if not isinstance(context, dict):
            continue

        return DashboardEarthEngineLatest(
            run_id=run.id,
            captured_at=snapshot.captured_at,
            region_id=run.region_id,
            region_code=(run.region.code if run.region is not None else None),
            station_id=run.station_id,
            station_code=(run.station.code if run.station is not None else None),
            source=(
                str(context["source"])
                if context.get("source") is not None
                else None
            ),
            earth_engine_context=context,
        )

    return DashboardEarthEngineLatest()
