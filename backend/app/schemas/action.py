"""Schemas for plans and executions."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.core.salinity_units import dsm_to_gl
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
    batch_id: UUID | None = None
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

    execution_job_id: UUID | None = None

    @model_validator(mode="after")
    def _sync_execution_job_aliases(self) -> "ActionExecutionRead":
        if self.execution_job_id is None:
            self.execution_job_id = self.batch_id
        return self


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
    execution_job_id: str | None = None
    execution_job_status: str | None = None
    execution_job_started_at: datetime | None = None
    execution_job_completed_at: datetime | None = None

    @model_validator(mode="after")
    def _sync_execution_job_aliases(self) -> "ExecutionBatchRead":
        if self.execution_job_id is None:
            self.execution_job_id = self.id
        if self.execution_job_status is None:
            self.execution_job_status = self.status
        if self.execution_job_started_at is None:
            self.execution_job_started_at = self.started_at
        if self.execution_job_completed_at is None:
            self.execution_job_completed_at = self.completed_at
        return self


class ExecutionJobRead(ExecutionBatchRead):
    """Execution job semantic alias of execution batch payload."""


class ExecutionBatchCollection(ORMBaseSchema):
    """Collection payload for execution batch listing."""

    items: list[ExecutionBatchRead]
    count: int


class ExecutionJobCollection(ORMBaseSchema):
    """Collection payload for execution job listing."""

    items: list[ExecutionJobRead]
    count: int


class ExecutionBatchDetail(ORMBaseSchema):
    """Execution batch detail with step-level executions."""

    batch: ExecutionBatchRead
    executions: list[ActionExecutionRead]
    count: int


class ExecutionJobDetail(ORMBaseSchema):
    """Execution job detail with step-level execution records."""

    execution_job: ExecutionJobRead
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

    outcome_class: Literal[
        "success",
        "partial_success",
        "failed_execution",
        "failed_plan",
        "inconclusive",
    ]
    # Backward compatibility field for current clients. Keep until FE migration completes.
    status: Literal["improved", "not_improved", "no_change", "insufficient_new_observation"]
    baseline_salinity_dsm: Decimal | None = None
    baseline_salinity_gl: Decimal | None = None
    latest_salinity_dsm: Decimal | None = None
    latest_salinity_gl: Decimal | None = None
    delta_dsm: Decimal | None = None
    delta_gl: Decimal | None = None
    summary: str
    replan_recommended: bool = False
    replan_reason: str | None = None

    @model_validator(mode="after")
    def normalize_salinity_units(self) -> "FeedbackEvaluation":
        if self.baseline_salinity_gl is None and self.baseline_salinity_dsm is not None:
            self.baseline_salinity_gl = dsm_to_gl(self.baseline_salinity_dsm)
        if self.latest_salinity_gl is None and self.latest_salinity_dsm is not None:
            self.latest_salinity_gl = dsm_to_gl(self.latest_salinity_dsm)
        if self.delta_gl is None and self.delta_dsm is not None:
            self.delta_gl = dsm_to_gl(self.delta_dsm)
        return self


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
