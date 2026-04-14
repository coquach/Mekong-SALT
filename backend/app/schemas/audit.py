"""Schemas for audit logs and action outcomes."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import AuditEventType
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class AuditLogRead(EntityReadSchema):
    """Audit event response payload."""

    event_type: AuditEventType
    actor_name: str
    actor_role: str | None = None
    region_id: UUID | None = None
    incident_id: UUID | None = None
    action_plan_id: UUID | None = None
    action_execution_id: UUID | None = None
    occurred_at: datetime
    summary: str
    payload: dict[str, Any] | None = None


class AuditLogCollection(ORMBaseSchema):
    """Audit list response."""

    items: list[AuditLogRead]
    count: int


class ActionOutcomeRead(EntityReadSchema):
    """Action outcome response payload."""

    execution_id: UUID
    recorded_at: datetime
    pre_metrics: dict[str, Any] | None = None
    post_metrics: dict[str, Any] | None = None
    status: str
    summary: str

