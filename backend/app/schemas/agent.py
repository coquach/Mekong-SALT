"""Schemas for agent-assisted planning."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import ActionType
from app.schemas.action import ActionPlanRead
from app.schemas.base import ORMBaseSchema
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead


class AgentPlanRequest(ORMBaseSchema):
    """Request payload for agent-assisted plan generation."""

    station_id: UUID | None = None
    station_code: str | None = None
    region_id: UUID | None = None
    region_code: str | None = None
    incident_id: UUID | None = None
    objective: str | None = Field(default=None, max_length=255)
    provider: Literal["mock", "gemini", "ollama"] | None = None


class PlanStep(ORMBaseSchema):
    """Structured plan step produced by the planning provider."""

    step_index: int = Field(ge=1, le=20)
    action_type: ActionType
    priority: int = Field(default=1, ge=1, le=5)
    title: str = Field(max_length=255)
    instructions: str
    rationale: str
    simulated: bool = True


class GeneratedActionPlan(ORMBaseSchema):
    """Structured JSON output required from the planning provider."""

    objective: str = Field(max_length=255)
    summary: str
    context_summary: str | None = None
    risk_summary: str | None = None
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    reasoning_summary: str | None = None
    steps: list[PlanStep] = Field(min_length=1, max_length=10)


class PlanValidationResult(ORMBaseSchema):
    """Policy guard result for a generated plan."""

    is_valid: bool
    policy_version: str = "v1"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    normalized_steps: list[dict[str, Any]] = Field(default_factory=list)


class AgentPlanResponse(ORMBaseSchema):
    """Response payload for the plan generation endpoint."""

    assessment: RiskAssessmentRead
    reading: SensorReadingRead
    weather_snapshot: WeatherSnapshotRead | None = None
    plan: ActionPlanRead
    agent_run_id: UUID | None = None
