"""Schemas for agent runs and observation snapshots."""

from datetime import datetime
from uuid import UUID

from app.schemas.base import EntityReadSchema, ORMBaseSchema


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


class AgentRunCollection(ORMBaseSchema):
    """Collection payload for agent run listing."""

    items: list[AgentRunRead]
    count: int
