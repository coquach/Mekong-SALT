"""Schemas for memory case browsing and retrieval."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.base import EntityReadSchema, ORMBaseSchema


class MemoryCaseRead(EntityReadSchema):
    """Read model for a persisted memory case."""

    region_id: UUID
    station_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    incident_id: UUID | None = None
    action_plan_id: UUID | None = None
    action_execution_id: UUID | None = None
    decision_log_id: UUID | None = None
    objective: str | None = None
    severity: str | None = None
    outcome_class: str
    outcome_status_legacy: str | None = None
    summary: str
    context_payload: dict[str, Any] | None = None
    action_payload: dict[str, Any] | None = None
    outcome_payload: dict[str, Any] | None = None
    keywords: list[str] | None = None
    occurred_at: datetime


class MemoryCaseCollection(ORMBaseSchema):
    """Collection payload for memory case browsing."""

    items: list[MemoryCaseRead]
    count: int