"""Schemas for feedback lifecycle APIs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import model_validator

from app.core.salinity_units import dsm_to_gl
from app.schemas.action import FeedbackEvaluation
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class FeedbackSnapshotRead(EntityReadSchema):
    """Feedback before/after snapshot payload."""

    batch_id: UUID
    plan_id: UUID
    execution_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    station_id: UUID | None = None
    reading_id: UUID | None = None
    snapshot_kind: Literal["before", "after"]
    captured_at: datetime
    reading_recorded_at: datetime | None = None
    salinity_dsm: Decimal | None = None
    salinity_gl: Decimal | None = None
    water_level_m: Decimal | None = None
    source: str
    payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalize_salinity_units(self) -> "FeedbackSnapshotRead":
        if self.salinity_gl is None and self.salinity_dsm is not None:
            self.salinity_gl = dsm_to_gl(self.salinity_dsm)
        return self


class OutcomeEvaluationRead(EntityReadSchema):
    """Persisted outcome taxonomy evaluation payload."""

    batch_id: UUID
    plan_id: UUID
    execution_id: UUID | None = None
    before_snapshot_id: UUID | None = None
    after_snapshot_id: UUID | None = None
    evaluated_at: datetime
    outcome_class: Literal[
        "success",
        "partial_success",
        "failed_execution",
        "failed_plan",
        "inconclusive",
    ]
    status_legacy: Literal[
        "improved",
        "not_improved",
        "no_change",
        "insufficient_new_observation",
    ]
    baseline_salinity_dsm: Decimal | None = None
    baseline_salinity_gl: Decimal | None = None
    latest_salinity_dsm: Decimal | None = None
    latest_salinity_gl: Decimal | None = None
    delta_dsm: Decimal | None = None
    delta_gl: Decimal | None = None
    summary: str
    replan_recommended: bool
    replan_reason: str | None = None
    evaluator_name: str
    payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalize_salinity_units(self) -> "OutcomeEvaluationRead":
        if self.baseline_salinity_gl is None and self.baseline_salinity_dsm is not None:
            self.baseline_salinity_gl = dsm_to_gl(self.baseline_salinity_dsm)
        if self.latest_salinity_gl is None and self.latest_salinity_dsm is not None:
            self.latest_salinity_gl = dsm_to_gl(self.latest_salinity_dsm)
        if self.delta_gl is None and self.delta_dsm is not None:
            self.delta_gl = dsm_to_gl(self.delta_dsm)
        return self


class FeedbackLifecycleRead(ORMBaseSchema):
    """Combined feedback lifecycle response payload."""

    evaluation: OutcomeEvaluationRead
    before_snapshot: FeedbackSnapshotRead | None = None
    after_snapshot: FeedbackSnapshotRead | None = None
    feedback: FeedbackEvaluation
