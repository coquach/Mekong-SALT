"""Audit logging helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.enums import AuditEventType
from app.repositories.ops import AuditLogRepository


async def write_audit_log(
    session: AsyncSession,
    *,
    event_type: AuditEventType,
    summary: str,
    actor_name: str | None = None,
    region_id: UUID | None = None,
    incident_id: UUID | None = None,
    action_plan_id: UUID | None = None,
    action_execution_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    """Create an audit event in the current transaction."""
    log = AuditLog(
        event_type=event_type,
        actor_name=actor_name or "system",
        actor_role=None,
        region_id=region_id,
        incident_id=incident_id,
        action_plan_id=action_plan_id,
        action_execution_id=action_execution_id,
        occurred_at=datetime.now(UTC),
        summary=summary,
        payload=payload,
    )
    return await AuditLogRepository(session).add(log)


async def list_audit_logs(
    session: AsyncSession,
    *,
    incident_id: UUID | None = None,
    plan_id: UUID | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    """Return recent audit logs."""
    return await AuditLogRepository(session).list_recent(
        incident_id=incident_id,
        plan_id=plan_id,
        limit=limit,
    )
