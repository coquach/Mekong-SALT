"""Zalo Official Account delivery helpers for demo notifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.services.notify.summary import build_human_summary


DEFAULT_ZALO_MESSAGE_ENDPOINT = "https://openapi.zalo.me/v3.0/oa/message/cs"
DEFAULT_ZALO_TEMPLATE_MESSAGE_ENDPOINT = "https://openapi.zalo.me/v3.0/oa/message/template"

_EVENT_LABELS_VI = {
    "incident_created": "sự cố được mở",
    "plan_created": "kế hoạch được tạo",
    "execution_alert": "cảnh báo thực thi",
    "execution_summary": "tổng kết thực thi",
    "risk_alert": "cảnh báo rủi ro",
    "demo_zalo_notification": "thông báo demo Zalo",
}
_SEVERITY_LABELS_VI = {
    "warning": "cảnh báo",
    "danger": "nguy hiểm",
    "critical": "khẩn cấp",
    "info": "thông tin",
}
_STATUS_LABELS_VI = {
    "draft": "bản nháp",
    "validated": "đã thẩm định",
    "pending_approval": "chờ duyệt",
    "approved": "đã duyệt",
    "rejected": "bị từ chối",
    "simulated": "mô phỏng",
    "closed": "đã đóng",
    "open": "đang mở",
    "investigating": "đang điều tra",
    "pending_plan": "chờ kế hoạch",
    "executing": "đang thực thi",
    "resolved": "đã xử lý",
    "pending": "đang chờ",
    "running": "đang chạy",
    "succeeded": "thành công",
    "failed": "thất bại",
    "cancelled": "đã hủy",
    "success": "thành công",
    "partial_success": "thành công một phần",
    "failed_plan": "kế hoạch thất bại",
    "failed_execution": "thực thi thất bại",
    "inconclusive": "chưa kết luận",
}


@dataclass(slots=True)
class ZaloDeliveryResult:
    """Structured result for a best-effort Zalo delivery call."""

    ok: bool
    status_code: int | None = None
    message_id: str | None = None
    response_payload: dict[str, Any] | None = None
    error_message: str | None = None


class ZaloDeliveryError(RuntimeError):
    """Raised when the demo delivery to Zalo OA fails."""


def build_zalo_text(subject: str | None, message: str, payload: dict[str, Any] | None = None) -> str:
    """Build a compact Vietnamese text body for Zalo delivery."""
    lines = []
    if subject:
        lines.append(subject.strip())
    lines.append(message.strip())
    extras: list[str] = []
    if payload:
        event = payload.get("event")
        if event:
            extras.append(f"Sự kiện: {_localize_event_label(event)}")
        severity = payload.get("severity")
        if severity:
            extras.append(f"Mức độ: {_localize_severity_label(severity)}")
        if payload.get("station_code"):
            extras.append(f"Trạm: {payload['station_code']}")
        if payload.get("region_code"):
            extras.append(f"Vùng: {payload['region_code']}")
        human_summary = build_human_summary(payload, message)
        if human_summary:
            extras.append(f"Diễn giải ngắn: {human_summary}")
    if extras:
        lines.append("")
        lines.append("Chi tiết:")
        lines.extend(f"- {item}" for item in extras)

    body = "\n".join(line for line in lines if line)
    return body[:900]


async def send_zalo_message(
    *,
    access_token: str,
    recipient_user_id: str,
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
    endpoint: str = DEFAULT_ZALO_MESSAGE_ENDPOINT,
    timeout_seconds: int = 10,
) -> ZaloDeliveryResult:
    """Send a customer-service message through Zalo OA."""
    text = build_zalo_text(subject, message, payload)
    request_payload = {
        "recipient": {"user_id": recipient_user_id},
        "message": {"text": text},
    }
    timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5))
    headers = {
        "access_token": access_token,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint, headers=headers, json=request_payload)

    try:
        response_payload = response.json()
    except Exception:
        response_payload = None

    if response.status_code >= 400:
        message_text = "Gửi Zalo OA thất bại."
        if isinstance(response_payload, dict):
            message_text = str(
                response_payload.get("message")
                or response_payload.get("error")
                or message_text
            )
        raise ZaloDeliveryError(
            f"{message_text} (status={response.status_code})"
        )

    message_id = None
    if isinstance(response_payload, dict):
        data = response_payload.get("data")
        if isinstance(data, dict):
            message_id = str(data.get("message_id") or data.get("id") or "") or None
        elif response_payload.get("message_id") is not None:
            message_id = str(response_payload.get("message_id"))

    return ZaloDeliveryResult(
        ok=True,
        status_code=response.status_code,
        message_id=message_id,
        response_payload=response_payload if isinstance(response_payload, dict) else None,
    )


def build_zalo_template_data(
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a conservative template payload from the notification content."""
    template_data: dict[str, Any] = {
        "subject": subject.strip() if subject else "",
        "message": message.strip(),
    }
    if payload:
        for key, value in payload.items():
            if value is None:
                continue
            if key == "event":
                template_data[key] = _localize_event_label(value)
                continue
            if key == "severity":
                template_data[key] = _localize_severity_label(value)
                continue
            if key in {"status", "outcome_class"}:
                template_data[key] = _localize_status_label(value)
                continue
            if isinstance(value, (str, int, float, bool)):
                template_data[key] = value
                continue
            template_data[key] = str(value)
    return template_data


async def send_zalo_template_message(
    *,
    access_token: str,
    template_id: str,
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
    recipient_phone_number: str,
    endpoint: str = DEFAULT_ZALO_TEMPLATE_MESSAGE_ENDPOINT,
    timeout_seconds: int = 10,
) -> ZaloDeliveryResult:
    """Send a ZNS/ZBS template message through the Zalo OA API."""
    request_payload = {
        "recipient": recipient_phone_number,
        "template_id": template_id,
        "template_data": build_zalo_template_data(subject, message, payload),
    }
    timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5))
    headers = {
        "access_token": access_token,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint, headers=headers, json=request_payload)

    try:
        response_payload = response.json()
    except Exception:
        response_payload = None

    if response.status_code >= 400:
        message_text = "Gửi Zalo template thất bại."
        if isinstance(response_payload, dict):
            message_text = str(
                response_payload.get("message")
                or response_payload.get("error")
                or message_text
            )
        raise ZaloDeliveryError(
            f"{message_text} (status={response.status_code})"
        )

    message_id = None
    if isinstance(response_payload, dict):
        data = response_payload.get("data")
        if isinstance(data, dict):
            message_id = str(data.get("message_id") or data.get("id") or "") or None
        elif response_payload.get("message_id") is not None:
            message_id = str(response_payload.get("message_id"))

    return ZaloDeliveryResult(
        ok=True,
        status_code=response.status_code,
        message_id=message_id,
        response_payload=response_payload if isinstance(response_payload, dict) else None,
    )


def _localize_event_label(value: Any) -> str:
    text = str(value).strip()
    return _EVENT_LABELS_VI.get(text, text)


def _localize_severity_label(value: Any) -> str:
    text = str(value).strip()
    return _SEVERITY_LABELS_VI.get(text.lower(), text)


def _localize_status_label(value: Any) -> str:
    text = str(value).strip()
    return _STATUS_LABELS_VI.get(text.lower(), text)
