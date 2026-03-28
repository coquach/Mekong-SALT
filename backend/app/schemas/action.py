"""Schemas for plans and executions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import ActionPlanStatus, ActionType, ExecutionStatus
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class ActionPlanBase(ORMBaseSchema):
    """Shared action plan fields."""

    region_id: UUID
    risk_assessment_id: UUID
    status: ActionPlanStatus = ActionPlanStatus.DRAFT
    objective: str = Field(max_length=255)
    generated_by: str = Field(default="system", max_length=100)
    model_provider: str | None = Field(default=None, max_length=100)
    summary: str
    assumptions: dict[str, Any] | None = None
    plan_steps: list[dict[str, Any]] = Field(default_factory=list)
    validation_result: dict[str, Any] | None = None


class ActionPlanCreate(ActionPlanBase):
    """Schema for creating an action plan."""


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


class ActionExecutionCreate(ActionExecutionBase):
    """Schema for creating an action execution."""


class ActionExecutionRead(EntityReadSchema, ActionExecutionBase):
    """Schema for returning an action execution."""

