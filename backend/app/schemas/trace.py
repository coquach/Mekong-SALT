"""Schemas for agent runs and observation snapshots."""

from datetime import datetime
from uuid import UUID

from pydantic import model_validator

from app.schemas.base import EntityReadSchema, ORMBaseSchema
from app.schemas.graph import ExecutionGraphRead, build_execution_graph_from_trace


class ObservationSnapshotRead(EntityReadSchema):
    """Read payload for a captured observation snapshot."""

    agent_run_id: UUID
    captured_at: datetime
    source: str
    region_id: UUID | None = None
    station_id: UUID | None = None
    reading_id: UUID | None = None
    weather_snapshot_id: UUID | None = None
    payload: dict


class AgentRunRead(EntityReadSchema):
    """Read payload for one traceable agent run."""

    run_type: str
    trigger_source: str
    status: str
    payload: dict
    trace: dict | None = None
    error_message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    region_id: UUID | None = None
    station_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    incident_id: UUID | None = None
    action_plan_id: UUID | None = None
    observation_snapshot: ObservationSnapshotRead | None = None
    execution_graph: ExecutionGraphRead | None = None

    @model_validator(mode="after")
    def _sync_execution_graph(self) -> "AgentRunRead":
        if self.execution_graph is None:
            self.execution_graph = build_execution_graph_from_trace(self.trace)
        return self


class AgentRunCollection(ORMBaseSchema):
    """Collection payload for agent run listing."""

    items: list[AgentRunRead]
    count: int
