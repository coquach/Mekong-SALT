"""Reusable execution graph schemas and normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.schemas.base import ORMBaseSchema

ExecutionGraphNodeStatus = Literal["pending", "active", "completed", "skipped", "failed", "blocked"]
ExecutionGraphStatus = Literal["pending", "running", "completed", "blocked", "failed"]


class ExecutionGraphNodeRead(ORMBaseSchema):
    """Normalized state for one graph node."""

    id: str
    label: str
    kind: str = "task"
    status: ExecutionGraphNodeStatus = "pending"
    step_index: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    summary: str | None = None
    details: dict[str, Any] | None = None


class ExecutionGraphEdgeRead(ORMBaseSchema):
    """Directed edge between two graph nodes."""

    source: str
    target: str
    label: str | None = None
    status: str | None = None


class ExecutionGraphRead(ORMBaseSchema):
    """Graph snapshot suitable for FE rendering."""

    graph_type: str
    status: ExecutionGraphStatus = "pending"
    current_node: str | None = None
    summary: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    nodes: list[ExecutionGraphNodeRead] = Field(default_factory=list)
    edges: list[ExecutionGraphEdgeRead] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_execution_graph_from_trace(
    trace: Mapping[str, Any] | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> ExecutionGraphRead | None:
    """Build a graph snapshot from planning or lifecycle trace payloads."""
    if not isinstance(trace, Mapping):
        return None

    if _looks_like_lifecycle_trace(trace):
        transitions = _as_transition_list(trace.get("transition_log"))
        if transitions:
            return _build_sequential_graph(
                graph_type="lifecycle",
                stage_definitions=_LIFECYCLE_STAGES,
                transitions=transitions,
                summary=_as_string(trace.get("feedback_summary") or trace.get("reason")),
                metadata={**_graph_metadata(trace), **(metadata or {})},
            )

    planning_transitions = _as_transition_list(trace.get("planning_transition_log"))
    if planning_transitions:
        plan_decision = trace.get("plan_decision") if isinstance(trace.get("plan_decision"), Mapping) else {}
        return _build_sequential_graph(
            graph_type="planning",
            stage_definitions=_PLANNING_STAGES,
            transitions=planning_transitions,
            summary=_as_string(
                trace.get("operator_summary")
                or plan_decision.get("reason")
                or _latest_transition_summary(planning_transitions)
            ),
            metadata={**_graph_metadata(trace), **(metadata or {})},
        )

    return None


def build_execution_graph_from_details(
    details: Mapping[str, Any] | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> ExecutionGraphRead | None:
    """Build a graph snapshot from a decision log details payload."""
    if not isinstance(details, Mapping):
        return None
    if "transition_log" not in details:
        return None

    transitions = _as_transition_list(details.get("transition_log"))
    if not transitions:
        return None

    return _build_sequential_graph(
        graph_type="lifecycle",
        stage_definitions=_LIFECYCLE_STAGES,
        transitions=transitions,
        summary=_as_string(details.get("feedback_summary") or details.get("summary") or details.get("reason")),
        metadata={**_graph_metadata(details), **(metadata or {})},
    )


def build_execution_graph_from_batch(
    batch: Mapping[str, Any] | None,
    executions: Sequence[Mapping[str, Any]] | None,
    *,
    feedback: Mapping[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExecutionGraphRead | None:
    """Build a graph snapshot from an execution batch and its step records."""
    if not isinstance(batch, Mapping):
        return None

    execution_items = [item for item in (executions or []) if isinstance(item, Mapping)]
    if not execution_items and not isinstance(feedback, Mapping):
        return None

    nodes: list[ExecutionGraphNodeRead] = []
    edges: list[ExecutionGraphEdgeRead] = []

    for index, execution in enumerate(execution_items):
        step_index = _as_int(execution.get("step_index"))
        node_id = f"step-{step_index}" if step_index is not None else f"execution-{index + 1}"
        label = _as_string(execution.get("action_type")) or f"Step {index + 1}"
        result_payload = execution.get("result_payload") if isinstance(execution.get("result_payload"), Mapping) else None
        details = _as_json_safe_mapping(result_payload)
        node_status = _normalize_execution_status(_as_string(execution.get("status")))
        summary = _as_string(execution.get("result_summary")) or _as_string((result_payload or {}).get("title"))
        started_at = _as_datetime(execution.get("started_at"))
        completed_at = _as_datetime(execution.get("completed_at"))

        nodes.append(
            ExecutionGraphNodeRead(
                id=node_id,
                label=label,
                kind="execution",
                status=node_status,
                step_index=step_index,
                started_at=started_at,
                completed_at=completed_at,
                summary=summary,
                details=details,
            )
        )

        if len(nodes) > 1:
            previous = nodes[-2]
            edges.append(
                ExecutionGraphEdgeRead(
                    source=previous.id,
                    target=node_id,
                    label="next",
                    status=node_status,
                )
            )

    if isinstance(feedback, Mapping):
        feedback_status = _as_string(feedback.get("outcome_class") or feedback.get("status"))
        nodes.append(
            ExecutionGraphNodeRead(
                id="feedback",
                label="Feedback",
                kind="feedback",
                status=_normalize_feedback_status(feedback_status),
                summary=_as_string(feedback.get("summary")),
                details=_as_json_safe_mapping(feedback),
            )
        )
        if len(nodes) > 1:
            edges.append(
                ExecutionGraphEdgeRead(
                    source=nodes[-2].id,
                    target="feedback",
                    label="feedback",
                    status=_normalize_feedback_status(feedback_status),
                )
            )

    if not nodes:
        return None

    graph_status = _derive_graph_status(nodes)
    current_node = _derive_current_node(nodes, graph_status)
    started_at = _first_datetime(node.started_at for node in nodes)
    completed_at = _last_datetime(node.completed_at for node in nodes)

    return ExecutionGraphRead(
        graph_type="execution_batch",
        status=graph_status,
        current_node=current_node,
        summary=_as_string(batch.get("status")),
        started_at=started_at,
        completed_at=completed_at,
        nodes=nodes,
        edges=edges,
        metadata={**_graph_metadata(batch), **(metadata or {})},
    )


def _build_sequential_graph(
    *,
    graph_type: str,
    stage_definitions: Sequence[Mapping[str, Any]],
    transitions: Sequence[Mapping[str, Any]],
    summary: str | None,
    metadata: dict[str, Any] | None,
) -> ExecutionGraphRead:
    transition_map = {
        _as_string(item.get("node")): item
        for item in transitions
        if isinstance(item, Mapping) and _as_string(item.get("node")) is not None
    }

    nodes: list[ExecutionGraphNodeRead] = []
    edges: list[ExecutionGraphEdgeRead] = []
    for index, stage in enumerate(stage_definitions):
        stage_id = _as_string(stage.get("id")) or f"stage-{index + 1}"
        transition = transition_map.get(stage_id)
        raw_status = _as_string(transition.get("status")) if isinstance(transition, Mapping) else None
        details = _as_json_safe_mapping((transition or {}).get("details") if isinstance(transition, Mapping) else None)
        node_status = _normalize_transition_status(raw_status, has_transition=transition is not None)
        detail_payload = details or {}
        summary_text = _as_string(
            detail_payload.get("reason") or detail_payload.get("summary") or detail_payload.get("policy_reason")
            or _derive_stage_summary(
                stage_id=stage_id,
                label=_as_string(stage.get("label")),
                kind=_as_string(stage.get("kind")),
                details=detail_payload,
                transition=transition,
            )
        )
        started_at = _as_datetime((transition or {}).get("started_at") if isinstance(transition, Mapping) else None)
        completed_at = _as_datetime((transition or {}).get("at") if isinstance(transition, Mapping) else None)

        nodes.append(
            ExecutionGraphNodeRead(
                id=stage_id,
                label=_as_string(stage.get("label")) or stage_id.replace("_", " "),
                kind=_as_string(stage.get("kind")) or "stage",
                status=node_status,
                step_index=index + 1,
                started_at=started_at,
                completed_at=completed_at,
                summary=summary_text,
                details=details or None,
            )
        )

        if index > 0:
            edges.append(
                ExecutionGraphEdgeRead(
                    source=nodes[index - 1].id,
                    target=stage_id,
                    label="next",
                    status=node_status,
                )
            )

    graph_status = _derive_graph_status(nodes)
    current_node = _derive_current_node(nodes, graph_status)
    started_at = _first_datetime(node.started_at for node in nodes)
    completed_at = _last_datetime(node.completed_at for node in nodes)

    return ExecutionGraphRead(
        graph_type=graph_type,
        status=graph_status,
        current_node=current_node,
        summary=summary,
        started_at=started_at,
        completed_at=completed_at,
        nodes=nodes,
        edges=edges,
        metadata=metadata or {},
    )


def _derive_graph_status(nodes: Sequence[ExecutionGraphNodeRead]) -> ExecutionGraphStatus:
    statuses = [node.status for node in nodes]
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "active" for status in statuses):
        return "running"
    if statuses and all(status in {"completed", "skipped"} for status in statuses):
        return "completed"
    return "pending"


def _derive_current_node(nodes: Sequence[ExecutionGraphNodeRead], graph_status: ExecutionGraphStatus) -> str | None:
    if graph_status == "completed":
        return None
    for node in reversed(nodes):
        if node.status in {"active", "blocked", "failed"}:
            return node.id
    for node in nodes:
        if node.status == "pending":
            return node.id
    return nodes[-1].id if nodes else None


def _looks_like_lifecycle_trace(trace: Mapping[str, Any]) -> bool:
    lifecycle_keys = {"approval_status", "execution_status", "feedback_status", "memory_write_status"}
    return any(key in trace for key in lifecycle_keys) or "transition_log" in trace


def _normalize_transition_status(raw_status: str | None, *, has_transition: bool) -> ExecutionGraphNodeStatus:
    if raw_status is None:
        return "pending"

    normalized = raw_status.strip().lower()
    if normalized in {"awaiting_human_approval", "blocked", "waiting"}:
        return "blocked"
    if normalized.startswith("skipped") or normalized in {"not_applicable", "insufficient_new_observation"}:
        return "skipped"
    if normalized in {"failed", "error", "rejected", "not_created"}:
        return "failed"
    if normalized in {"completed", "classified", "approved", "executed", "written", "created", "succeeded", "improved", "no_change", "partial_success", "inconclusive"}:
        return "completed"
    if normalized in {"running", "started", "active"}:
        return "active"
    return "completed" if has_transition else "pending"


def _normalize_execution_status(raw_status: str | None) -> ExecutionGraphNodeStatus:
    if raw_status is None:
        return "pending"
    normalized = raw_status.strip().lower()
    if normalized in {"failed", "error", "cancelled", "canceled"}:
        return "failed"
    if normalized in {"pending", "running", "started", "active"}:
        return "active"
    if normalized in {"skipped", "not_applicable"}:
        return "skipped"
    return "completed"


def _normalize_feedback_status(raw_status: str | None) -> ExecutionGraphNodeStatus:
    if raw_status is None:
        return "completed"
    normalized = raw_status.strip().lower()
    if normalized in {"failed_execution", "failed_plan"}:
        return "failed"
    if normalized in {"inconclusive"}:
        return "blocked"
    return "completed"


def _graph_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in (
        "run_type",
        "trigger_source",
        "action_plan_id",
        "plan_id",
        "region_id",
        "incident_id",
        "risk_assessment_id",
        "batch_id",
        "execution_batch_id",
        "objective",
        "feedback_outcome_class",
        "feedback_status",
    ):
        value = payload.get(key)
        if value is not None:
            metadata[key] = value
    return metadata


def _as_transition_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _latest_transition_summary(transitions: Sequence[Mapping[str, Any]]) -> str | None:
    for transition in reversed(transitions):
        details = transition.get("details") if isinstance(transition.get("details"), Mapping) else None
        if not isinstance(details, Mapping):
            continue
        summary = _as_string(details.get("summary") or details.get("reason") or details.get("policy_reason"))
        if summary is not None:
            return summary
    return None


def _derive_stage_summary(
    *,
    stage_id: str,
    label: str | None,
    kind: str | None,
    details: Mapping[str, Any] | None,
    transition: Mapping[str, Any] | None,
) -> str | None:
    stage_label = label or stage_id.replace("_", " ")
    detail_map = details if isinstance(details, Mapping) else {}
    status = _as_string(transition.get("status") if isinstance(transition, Mapping) else None)
    if stage_id == "observe":
        objective = _as_string(detail_map.get("objective") or detail_map.get("goal") or detail_map.get("summary"))
        if objective is not None:
            objective_text = objective.rstrip(".?!")
            return f"Quan sát bối cảnh đầu vào để bám mục tiêu: {objective_text}."
        return "Quan sát dữ liệu đầu vào và xác định bối cảnh ra quyết định."

    if stage_id == "assess_risk":
        risk_level = _as_string(detail_map.get("risk_level"))
        risk_summary = _as_string(detail_map.get("summary") or detail_map.get("reason"))
        risk_level_label = {
            "safe": "an toàn",
            "warning": "cảnh báo",
            "danger": "nguy hiểm",
            "critical": "rất nguy cấp",
        }.get(risk_level, risk_level)
        pieces: list[str] = []
        if risk_level_label is not None:
            pieces.append(f"Rủi ro được đánh giá ở mức {risk_level_label}.")
        if risk_summary is not None:
            pieces.append(risk_summary if risk_summary.endswith(".") else f"{risk_summary}.")
        if pieces:
            return " ".join(pieces)
        return "Đánh giá rủi ro từ độ mặn, xu hướng và độ tin cậy của dữ liệu."

    if stage_id == "retrieve_context":
        evidence_count = _as_int(detail_map.get("evidence_count") or detail_map.get("total_evidence"))
        gate_targets = _as_int(detail_map.get("gate_targets"))
        retrieved_keys = detail_map.get("retrieved_context_keys")
        key_count = len(retrieved_keys) if isinstance(retrieved_keys, Sequence) and not isinstance(retrieved_keys, (str, bytes, bytearray)) else None
        pieces = ["Truy xuất ngữ cảnh hỗ trợ cho bước lập kế hoạch."]
        if evidence_count is not None:
            pieces.append(f"Thu được {evidence_count} bằng chứng.")
        if gate_targets is not None:
            pieces.append(f"Có {gate_targets} gate mục tiêu để cân nhắc.")
        if key_count is not None:
            pieces.append(f"{key_count} nhóm ngữ cảnh đã được kéo về.")
        return " ".join(pieces)

    if stage_id == "draft_plan":
        step_count = _as_int(detail_map.get("step_count"))
        confidence_score = detail_map.get("confidence_score")
        pieces = ["Soạn kế hoạch dựa trên ngữ cảnh vừa truy xuất."]
        if step_count is not None:
            pieces.append(f"Phác thảo {step_count} bước hành động.")
        if confidence_score is not None:
            pieces.append(f"Độ tự tin của kế hoạch là {confidence_score}.")
        return " ".join(pieces)

    if stage_id == "validate_plan":
        is_valid = detail_map.get("is_valid")
        error_count = _as_int(detail_map.get("error_count") or detail_map.get("errors_count"))
        warning_count = _as_int(detail_map.get("warning_count") or detail_map.get("warnings_count"))
        if isinstance(is_valid, bool):
            if is_valid:
                return "Xác thực kế hoạch và không phát hiện lỗi an toàn đáng chú ý."
            return "Xác thực kế hoạch và phát hiện vấn đề cần chỉnh sửa trước khi tiếp tục."
        pieces = [f"Xác thực kế hoạch cho bước {stage_label.lower()}."]
        if error_count is not None:
            pieces.append(f"Có {error_count} lỗi.")
        if warning_count is not None:
            pieces.append(f"Có {warning_count} cảnh báo.")
        return " ".join(pieces)

    if label is not None:
        if status == "completed":
            return f"Đã hoàn tất bước {label.lower()}."
        if status == "active":
            return f"Đang xử lý bước {label.lower()}."
        return f"Thực hiện bước {label.lower()} trong luồng suy luận."

    if kind is not None:
        return f"Đang xử lý {kind} của luồng suy luận."

    return None


def _as_json_safe_mapping(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return dict(value)


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _first_datetime(values: Iterable[datetime | None]) -> datetime | None:
    for value in values:
        if value is not None:
            return value
    return None


def _last_datetime(values: Iterable[datetime | None]) -> datetime | None:
    collected = [value for value in values if value is not None]
    return collected[-1] if collected else None


_PLANNING_STAGES: list[dict[str, str]] = [
    {"id": "observe", "label": "Quan sát", "kind": "input"},
    {"id": "assess_risk", "label": "Đánh giá rủi ro", "kind": "analysis"},
    {"id": "retrieve_context", "label": "Truy xuất ngữ cảnh", "kind": "retrieval"},
    {"id": "draft_plan", "label": "Soạn kế hoạch", "kind": "generation"},
    {"id": "validate_plan", "label": "Xác thực kế hoạch", "kind": "validation"},
]

_LIFECYCLE_STAGES: list[dict[str, str]] = [
    {"id": "classify_risk", "label": "Phân loại rủi ro", "kind": "analysis"},
    {"id": "approval_gate", "label": "Cổng phê duyệt", "kind": "decision"},
    {"id": "execute", "label": "Thực thi mô phỏng", "kind": "execution"},
    {"id": "feedback", "label": "Phản hồi", "kind": "feedback"},
    {"id": "memory_write", "label": "Ghi nhớ", "kind": "persistence"},
]