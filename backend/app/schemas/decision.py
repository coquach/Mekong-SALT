"""Schemas for decision logs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import DecisionActorType
from app.schemas.base import EntityReadSchema, ORMBaseSchema
from app.schemas.graph import ExecutionGraphRead, build_execution_graph_from_details


class DecisionLogBase(ORMBaseSchema):
    """Shared decision log fields."""

    region_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    action_plan_id: UUID | None = None
    action_execution_id: UUID | None = None
    logged_at: datetime
    actor_type: DecisionActorType = DecisionActorType.SYSTEM
    actor_name: str = Field(default="system", max_length=255)
    summary: str
    outcome: str = Field(max_length=100)
    details: dict[str, Any] | None = None
    store_as_memory: bool = False


class DecisionLogCreate(DecisionLogBase):
    """Schema for creating a decision log."""


class DecisionLogRead(EntityReadSchema, DecisionLogBase):
    """Schema for returning a decision log."""

    execution_graph: ExecutionGraphRead | None = None

    @model_validator(mode="after")
    def _sync_execution_graph(self) -> "DecisionLogRead":
        if self.execution_graph is None:
            self.execution_graph = build_execution_graph_from_details(self.details)
        return self

