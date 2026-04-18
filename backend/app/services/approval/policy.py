"""Approval gate policy rules for lifecycle and approval workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.models.enums import RiskLevel


@dataclass(frozen=True, slots=True)
class ApprovalGatePolicy:
    """Resolved policy decision for one risk level."""

    risk_level: RiskLevel | None
    risk_classification: str
    requires_human_approval: bool
    reason: str


def build_approval_explanation(
    *,
    risk_level: RiskLevel | None,
    plan_summary: str,
    risk_summary: str | None = None,
    validation_errors: Iterable[str] = (),
    validation_warnings: Iterable[str] = (),
) -> str:
    """Build a short human-readable explanation for plan approval review."""
    policy = resolve_approval_gate_policy(risk_level)
    risk_label = risk_level.value if risk_level is not None else "unknown"
    summary_text = plan_summary.strip() or "Chưa có mô tả kế hoạch."
    risk_text = risk_summary.strip() if risk_summary else "Chưa có tóm tắt rủi ro chi tiết."
    error_items = [item.strip() for item in validation_errors if str(item).strip()]
    warning_items = [item.strip() for item in validation_warnings if str(item).strip()]

    parts = [
        f"Mức rủi ro hiện tại là {risk_label} ({policy.risk_classification}).",
        f"Tóm tắt rủi ro: {risk_text}",
        f"Kế hoạch đề xuất: {summary_text}",
    ]

    if error_items:
        parts.append(
            "Có lỗi an toàn cần xử lý trước khi duyệt: " + "; ".join(error_items[:3]) + "."
        )
    elif warning_items:
        parts.append(
            "Có cảnh báo cần lưu ý: " + "; ".join(warning_items[:3]) + "."
        )

    if policy.requires_human_approval:
        parts.append(
            "Theo chính sách, kế hoạch này cần người điều hành xác nhận trước khi chạy mô phỏng."
        )
    else:
        parts.append(
            "Kế hoạch có thể được duyệt nếu bạn đồng ý với phương án mô phỏng hiện tại."
        )

    parts.append(
        "Chọn Phê duyệt nếu bạn chấp nhận rủi ro đã nêu và muốn tiếp tục mô phỏng; chọn Từ chối nếu cần thêm bằng chứng, muốn chờ dữ liệu mới, hoặc không đồng ý với hướng xử lý này."
    )
    return " ".join(parts)


def classify_risk_level(risk_level: RiskLevel | None) -> str:
    """Map a risk level into a coarse lifecycle class."""
    if risk_level in {RiskLevel.CRITICAL, RiskLevel.DANGER}:
        return "high"
    if risk_level is RiskLevel.WARNING:
        return "moderate"
    if risk_level is RiskLevel.SAFE:
        return "low"
    return "unknown"


def resolve_approval_gate_policy(risk_level: RiskLevel | None) -> ApprovalGatePolicy:
    """Resolve HITL gating policy from risk level."""
    risk_classification = classify_risk_level(risk_level)
    requires_human_approval = risk_level in {RiskLevel.DANGER, RiskLevel.CRITICAL}
    if risk_level is None:
        requires_human_approval = True

    if requires_human_approval:
        reason = "High or unknown risk requires human approval before execution."
    else:
        reason = "Risk is below high threshold and may be auto-approved by workflow policy."

    return ApprovalGatePolicy(
        risk_level=risk_level,
        risk_classification=risk_classification,
        requires_human_approval=requires_human_approval,
        reason=reason,
    )
