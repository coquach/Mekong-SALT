"""Schemas for monitoring goals and run-once execution."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.agent import AgentPlanResponse
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class GoalThresholds(ORMBaseSchema):
    """Threshold configuration for a monitoring goal."""

    warning_threshold_dsm: Decimal = Field(gt=0)
    critical_threshold_dsm: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.critical_threshold_dsm <= self.warning_threshold_dsm:
            raise ValueError("critical_threshold_dsm must be greater than warning_threshold_dsm")
        return self


class MonitoringGoalBase(ORMBaseSchema):
    """Shared fields for monitoring goal payloads."""

    name: str = Field(min_length=3, max_length=150)
    description: str | None = None
    region_id: UUID
    station_id: UUID | None = None
    objective: str = Field(min_length=3, max_length=255)
    provider: Literal["mock", "gemini", "ollama"] | None = None
    thresholds: GoalThresholds
    evaluation_interval_minutes: int = Field(ge=1, le=10080)
    is_active: bool = True


class MonitoringGoalCreate(MonitoringGoalBase):
    """Payload for creating a monitoring goal."""


class MonitoringGoalUpdate(ORMBaseSchema):
    """Payload for updating a monitoring goal."""

    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = None
    region_id: UUID | None = None
    station_id: UUID | None = None
    objective: str | None = Field(default=None, min_length=3, max_length=255)
    provider: Literal["mock", "gemini", "ollama"] | None = None
    thresholds: GoalThresholds | None = None
    evaluation_interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    is_active: bool | None = None


class MonitoringGoalRead(EntityReadSchema):
    """Monitoring goal read model."""

    name: str
    description: str | None = None
    region_id: UUID
    station_id: UUID | None = None
    objective: str
    provider: Literal["mock", "gemini", "ollama"] | None = None
    thresholds: GoalThresholds
    evaluation_interval_minutes: int
    is_active: bool
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    last_run_plan_id: UUID | None = None


class MonitoringGoalCollection(ORMBaseSchema):
    """Collection response payload for goal listing."""

    items: list[MonitoringGoalRead]
    count: int


class GoalRunOnceRequest(ORMBaseSchema):
    """Optional overrides when running one immediate goal cycle."""

    objective: str | None = Field(default=None, min_length=3, max_length=255)
    incident_id: UUID | None = None
    provider: Literal["mock", "gemini", "ollama"] | None = None


class GoalRunOnceResponse(ORMBaseSchema):
    """One-shot execution result for a monitoring goal."""

    goal: MonitoringGoalRead
    result: AgentPlanResponse
