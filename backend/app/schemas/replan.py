"""Schemas for feedback-driven replan requests."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from app.schemas.base import ORMBaseSchema


class ReplanRequestedEventPayload(ORMBaseSchema):
    """Durable payload for a background replan request event."""

    summary: str
    incident_id: UUID
    region_id: UUID
    station_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    action_plan_id: UUID
    execution_batch_id: UUID | None = None
    objective: str
    feedback_outcome_class: Literal[
        "success",
        "partial_success",
        "failed_execution",
        "failed_plan",
        "inconclusive",
    ]
    feedback_status: Literal[
        "improved",
        "not_improved",
        "no_change",
        "insufficient_new_observation",
    ]
    feedback_summary: str
    replan_reason: str | None = None
    requested_at: datetime
    attempt: int = 1
    trigger_source: str
    goal_id: UUID | None = None
    goal_name: str | None = None
    dedupe_key: str | None = None

