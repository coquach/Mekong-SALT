"""Human-friendly notification summary formatting."""

from __future__ import annotations

from typing import Any


_OUTCOME_LABELS_VI = {
    "success": "thành công",
    "partial_success": "thành công một phần",
    "failed_execution": "thực thi thất bại",
    "failed_plan": "kế hoạch thất bại",
    "inconclusive": "chưa đủ dữ liệu để kết luận",
}

_SEVERITY_LABELS_VI = {
    "warning": "cảnh báo",
    "danger": "nguy hiểm",
    "critical": "khẩn cấp",
    "info": "thông tin",
}


def build_human_summary(payload: dict[str, Any] | None, message: str) -> str | None:
    """Return a short plain-language summary when the raw message is too technical."""
    data = payload or {}
    event = str(data.get("event") or "").strip().lower()
    summary = str(data.get("summary") or "").strip()
    message_text = str(message or "").strip()

    if event == "execution_summary":
        parts: list[str] = []
        outcome = str(data.get("outcome_class") or "").strip().lower()
        if outcome:
            parts.append(f"Kết quả mô phỏng: {_OUTCOME_LABELS_VI.get(outcome, outcome)}.")
        action_summary = str(data.get("action_summary") or "").strip()
        if action_summary:
            parts.append(f"Các bước chính: {action_summary}.")
        if outcome in {"success", "partial_success"}:
            parts.append(
                "Điều này cho thấy hệ thống đã phản ứng đúng trình tự, xử lý tình huống sớm và giữ nhịp vận hành ổn định hơn."
            )
        elif outcome == "inconclusive":
            parts.append(
                "Điều này cho thấy luồng phản ứng đã chạy xong, nhưng cần thêm dữ liệu để chứng minh hiệu quả cuối cùng một cách chắc chắn hơn."
            )
        elif outcome in {"failed_execution", "failed_plan"}:
            parts.append(
                "Điều này cho thấy phương án hiện tại chưa đủ ổn định, nên cần rà lại trước khi áp dụng rộng hơn."
            )
        if data.get("replan_recommended") is True:
            parts.append("Hệ thống đề xuất xem xét lập lại kế hoạch.")
        if parts:
            return " ".join(parts)

    if event == "risk_alert":
        parts = ["Hệ thống vừa phát hiện một cảnh báo rủi ro."]
        severity = str(data.get("severity") or "").strip().lower()
        if severity:
            parts.append(f"Mức độ: {_SEVERITY_LABELS_VI.get(severity, severity)}.")
        if data.get("station_code"):
            parts.append(f"Trạm liên quan: {data['station_code']}.")
        if data.get("region_code"):
            parts.append(f"Khu vực: {data['region_code']}.")
        return " ".join(parts)

    if event == "plan_created":
        return "Kế hoạch mới đã được tạo và đang chờ người dùng xem xét."

    if event == "incident_created":
        return "Hệ thống đã mở một sự cố mới để theo dõi và xử lý."

    if summary and summary != message_text:
        return summary

    return None