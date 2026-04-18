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
from app.schemas.graph import build_execution_graph_from_trace


def _json_safe(value: Any) -> Any:
    """Normalize payload values into JSON-safe objects."""
    return jsonable_encoder(
        value,
        custom_encoder={Decimal: lambda item: str(item), UUID: lambda item: str(item)},
    )


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _as_numeric_mapping(value: Any) -> dict[str, int | float]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, int | float] = {}
    for key, raw_value in value.items():
        if isinstance(raw_value, bool):
            continue
        if isinstance(raw_value, (int, float)):
            normalized[str(key)] = raw_value
            continue
        try:
            normalized[str(key)] = float(raw_value) if "." in str(raw_value) else int(raw_value)
        except (TypeError, ValueError):
            continue
    return normalized


def _as_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped) if "." in stripped else int(stripped)
        except ValueError:
            return None
    return None


def _normalize_transition_log(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    transitions: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        transition: dict[str, Any] = {
            "node": _as_string(item.get("node")),
            "status": _as_string(item.get("status")),
        }
        at_value = _as_string(item.get("at"))
        if at_value is not None:
            transition["at"] = at_value
        if isinstance(item.get("details"), dict):
            transition["details"] = item.get("details")
        transitions.append(transition)
    return transitions


def _normalize_top_citations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    citations: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        citations.append(
            {
                "citation": _as_string(item.get("citation")),
                "source": _as_string(item.get("source")),
                "score": item.get("score"),
                "rank": item.get("rank"),
            }
        )
    return citations


def _build_operator_summary(trace: dict[str, Any]) -> str | None:
    parts: list[str] = []

    incident_decision = trace.get("incident_decision") if isinstance(trace.get("incident_decision"), dict) else {}
    incident_label = _as_string(incident_decision.get("decision"))
    if incident_label:
        parts.append(f"Sự cố: {incident_label}")

    plan_decision = trace.get("plan_decision") if isinstance(trace.get("plan_decision"), dict) else {}
    plan_label = _as_string(plan_decision.get("decision"))
    if plan_label:
        parts.append(f"Kế hoạch: {plan_label}")

    validation = plan_decision.get("validation") if isinstance(plan_decision.get("validation"), dict) else {}
    error_count = len(_as_string_list(validation.get("errors")))
    warning_count = len(_as_string_list(validation.get("warnings")))
    if error_count > 0:
        parts.append(f"{error_count} lỗi guard")
    elif warning_count > 0:
        parts.append(f"{warning_count} cảnh báo guard")

    retrieval_trace = trace.get("retrieval_trace") if isinstance(trace.get("retrieval_trace"), dict) else {}
    total_evidence = retrieval_trace.get("total_evidence")
    if isinstance(total_evidence, (int, float)):
        parts.append(f"{int(total_evidence)} evidence")

    citations = retrieval_trace.get("top_citations")
    if isinstance(citations, list) and citations:
        parts.append(f"{len(citations)} citations")

    return " · ".join(parts) if parts else None


def normalize_agent_run_trace(trace: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize trace payloads into a stable shape for frontend consumers."""
    result = dict(trace or {})

    incident_decision = result.get("incident_decision") if isinstance(result.get("incident_decision"), dict) else {}
    result["incident_decision"] = {
        "decision": _as_string(incident_decision.get("decision")),
        "reason": _as_string(incident_decision.get("reason")),
    }

    plan_decision = result.get("plan_decision") if isinstance(result.get("plan_decision"), dict) else {}
    validation = plan_decision.get("validation") if isinstance(plan_decision.get("validation"), dict) else {}
    result["plan_decision"] = {
        "decision": _as_string(plan_decision.get("decision")),
        "reason": _as_string(plan_decision.get("reason")),
        "action_plan_id": _as_string(plan_decision.get("action_plan_id")),
        "validation": {
            "is_valid": validation.get("is_valid") if isinstance(validation.get("is_valid"), bool) else None,
            "errors": _as_string_list(validation.get("errors")),
            "warnings": _as_string_list(validation.get("warnings")),
        },
    }

    retrieval_trace = result.get("retrieval_trace") if isinstance(result.get("retrieval_trace"), dict) else {}
    total_evidence = retrieval_trace.get("total_evidence")
    result["retrieval_trace"] = {
        "total_evidence": int(number) if (number := _as_number(total_evidence)) is not None else 0,
        "source_counts": _as_numeric_mapping(retrieval_trace.get("source_counts")),
        "top_citations": _normalize_top_citations(retrieval_trace.get("top_citations")),
    }

    result["planning_transition_log"] = _normalize_transition_log(result.get("planning_transition_log"))
    result["operator_summary"] = _build_operator_summary(result)
    graph_metadata: dict[str, Any] = {}
    for key in ("run_type", "trigger_source", "action_plan_id", "region_id", "incident_id", "risk_assessment_id"):
        value = result.get(key)
        if value is not None:
            graph_metadata[key] = value
    execution_graph = build_execution_graph_from_trace(result, metadata=graph_metadata)
    if execution_graph is not None:
        result["execution_graph"] = execution_graph.model_dump(mode="json")
    return _json_safe(result)


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
    return normalize_agent_run_trace(result)


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
