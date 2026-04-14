"""Helpers for persisting agent run traces and observation snapshots."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentRun, ObservationSnapshot
from app.repositories.agent_run import AgentRunRepository, ObservationSnapshotRepository


def _json_safe(value: Any) -> Any:
    """Normalize payload values into JSON-safe objects."""
    return jsonable_encoder(
        value,
        custom_encoder={Decimal: lambda item: str(item), UUID: lambda item: str(item)},
    )


async def start_agent_run(
    session: AsyncSession,
    *,
    run_type: str,
    trigger_source: str,
    payload: dict[str, Any],
    region_id: UUID | None = None,
    station_id: UUID | None = None,
) -> AgentRun:
    """Create and flush a new agent run in started status."""
    run = AgentRun(
        run_type=run_type,
        trigger_source=trigger_source,
        status="started",
        payload=_json_safe(payload),
        started_at=datetime.now(UTC),
        region_id=region_id,
        station_id=station_id,
    )
    await AgentRunRepository(session).add(run)
    return run


async def capture_observation_snapshot(
    session: AsyncSession,
    *,
    run: AgentRun,
    source: str,
    payload: dict[str, Any],
    region_id: UUID | None,
    station_id: UUID | None,
    reading_id: UUID | None,
    weather_snapshot_id: UUID | None,
) -> ObservationSnapshot:
    """Persist a pre-decision observation snapshot linked to a run."""
    snapshot = ObservationSnapshot(
        agent_run_id=run.id,
        captured_at=datetime.now(UTC),
        source=source,
        region_id=region_id,
        station_id=station_id,
        reading_id=reading_id,
        weather_snapshot_id=weather_snapshot_id,
        payload=_json_safe(payload),
    )
    await ObservationSnapshotRepository(session).add(snapshot)
    return snapshot


def merge_trace(existing_trace: dict[str, Any] | None, update: dict[str, Any]) -> dict[str, Any]:
    """Merge a trace update into the run trace payload."""
    result = dict(existing_trace or {})
    result.update(update)
    return _json_safe(result)


def finish_agent_run(
    run: AgentRun,
    *,
    status: str,
    trace: dict[str, Any],
    error_message: str | None = None,
    risk_assessment_id: UUID | None = None,
    incident_id: UUID | None = None,
    action_plan_id: UUID | None = None,
) -> None:
    """Complete a run with final status and decision trace."""
    run.status = status
    run.trace = merge_trace(run.trace, trace)
    run.error_message = error_message
    run.finished_at = datetime.now(UTC)
    if risk_assessment_id is not None:
        run.risk_assessment_id = risk_assessment_id
    run.incident_id = incident_id
    run.action_plan_id = action_plan_id
