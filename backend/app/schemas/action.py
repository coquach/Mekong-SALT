"""Schemas for plans and executions."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import ActionPlanStatus, ActionType, ExecutionStatus
from app.schemas.decision import DecisionLogRead
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class ActionPlanBase(ORMBaseSchema):
    """Shared action plan fields."""

    region_id: UUID
    risk_assessment_id: UUID
    incident_id: UUID | None = None
    status: ActionPlanStatus = ActionPlanStatus.DRAFT
    objective: str = Field(max_length=255)
    generated_by: str = Field(default="system", max_length=100)
    model_provider: str | None = Field(default=None, max_length=100)
    summary: str
    assumptions: dict[str, Any] | None = None
    plan_steps: list[dict[str, Any]] = Field(default_factory=list)
    validation_result: dict[str, Any] | None = None


class ActionPlanRead(EntityReadSchema, ActionPlanBase):
    """Schema for returning an action plan."""


class ActionExecutionBase(ORMBaseSchema):
    """Shared action execution fields."""

    plan_id: UUID
    region_id: UUID
    action_type: ActionType
    status: ExecutionStatus = ExecutionStatus.PENDING
    simulated: bool = True
    step_index: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None
    idempotency_key: str | None = Field(default=None, max_length=120)
    requested_by: str | None = Field(default=None, max_length=255)


class ActionExecutionRead(EntityReadSchema, ActionExecutionBase):
    """Schema for returning an action execution."""


class ExecutionBatchRead(ORMBaseSchema):
    """Execution batch read model for one simulated transaction."""

    id: str
    plan_id: UUID
    region_id: UUID
    status: str
    simulated: bool = True
    requested_by: str | None = None
    idempotency_key: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    step_count: int


class ExecutionBatchCollection(ORMBaseSchema):
    """Collection payload for execution batch listing."""

    items: list[ExecutionBatchRead]
    count: int


class ExecutionBatchDetail(ORMBaseSchema):
    """Execution batch detail with step-level executions."""

    batch: ExecutionBatchRead
    executions: list[ActionExecutionRead]
    count: int


class SimulatedExecutionRequest(ORMBaseSchema):
    """Request payload for safe simulated execution."""

    action_plan_id: UUID
    idempotency_key: str | None = Field(default=None, max_length=120)


class ExecutionSimulateRequest(ORMBaseSchema):
    """Request payload when the plan ID is carried in the route path."""

    idempotency_key: str | None = Field(default=None, max_length=120)


class FeedbackEvaluation(ORMBaseSchema):
    """Feedback summary after simulated execution."""

    status: Literal["improved", "not_improved", "no_change", "insufficient_new_observation"]
    baseline_salinity_dsm: Decimal | None = None
    latest_salinity_dsm: Decimal | None = None
    delta_dsm: Decimal | None = None
    summary: str


class SimulatedExecutionResponse(ORMBaseSchema):
    """Response payload for simulated execution flow."""

    plan: ActionPlanRead
    executions: list[ActionExecutionRead]
    feedback: FeedbackEvaluation
    decision_logs: list[DecisionLogRead]
    idempotent_replay: bool = False


class SimulatedExecutionBatchResponse(ORMBaseSchema):
    """Response payload for batch-oriented simulated execution."""

    batch: ExecutionBatchRead
    executions: list[ActionExecutionRead]
    feedback: FeedbackEvaluation
    decision_logs: list[DecisionLogRead]
    idempotent_replay: bool = False


class ActionLogEntry(ORMBaseSchema):
    """Combined execution and decision log entry."""

    execution: ActionExecutionRead
    decision_log: DecisionLogRead | None = None


class ActionLogCollection(ORMBaseSchema):
    """Collection payload for action log queries."""

    items: list[ActionLogEntry]
    count: int
