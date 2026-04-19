"""Best-effort realtime graph stream helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID

from app.core.config import get_settings
from app.db.redis import RedisManager
from app.schemas.graph import ExecutionGraphRead


def _json_safe_identifier(value: UUID | str | None) -> str | None:
    if value is None:
        return None
    return str(value)


async def publish_graph_transition(
    redis_manager: RedisManager | None,
    *,
    graph_type: str,
    node: str,
    status: str,
    graph_snapshot: ExecutionGraphRead | None,
    details: Mapping[str, Any] | None = None,
    summary: str | None = None,
    run_id: UUID | str | None = None,
    plan_id: UUID | str | None = None,
    incident_id: UUID | str | None = None,
    execution_batch_id: UUID | str | None = None,
) -> None:
    """Publish a single graph transition payload to the shared SSE channel."""
    if redis_manager is None:
        return

    payload = {
        "event_type": "graph.transition",
        "graph_type": graph_type,
        "node": node,
        "status": status,
        "at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "details": dict(details or {}),
        "run_id": _json_safe_identifier(run_id),
        "plan_id": _json_safe_identifier(plan_id),
        "incident_id": _json_safe_identifier(incident_id),
        "execution_batch_id": _json_safe_identifier(execution_batch_id),
        "graph_snapshot": (
            _make_live_graph_snapshot(graph_snapshot, graph_type=graph_type).model_dump(mode="json")
            if graph_snapshot is not None
            else None
        ),
    }
    await redis_manager.publish_signal(
        get_settings().graph_stream_channel,
        payload=payload,
    )

def _make_live_graph_snapshot(
    graph_snapshot: ExecutionGraphRead,
    *,
    graph_type: str,
) -> ExecutionGraphRead:
    """Promote the current node to active for a more explicit live display."""
    live_graph = graph_snapshot.model_copy(deep=True)
    if graph_type == "execution_batch":
        if live_graph.completed_at is not None or live_graph.status == "completed":
            return live_graph
        if live_graph.nodes:
            latest_index = len(live_graph.nodes) - 1
            latest_node = live_graph.nodes[latest_index]
            if latest_node.status == "completed":
                live_graph.nodes[latest_index] = latest_node.model_copy(update={"status": "active"})
            live_graph = live_graph.model_copy(update={
                "status": "running",
                "current_node": live_graph.nodes[latest_index].id,
            })
        return live_graph

    if live_graph.status == "completed":
        return live_graph

    current_node_id = live_graph.current_node
    if current_node_id is None:
        return live_graph

    for index, node in enumerate(live_graph.nodes):
        if node.id != current_node_id or node.status != "pending":
            continue
        live_graph.nodes[index] = node.model_copy(update={"status": "active"})
        break

    if live_graph.status == "pending":
        live_graph = live_graph.model_copy(update={"status": "running"})
    return live_graph
