"""Email delivery helpers for demo notifications."""

from __future__ import annotations

import asyncio
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Any

from app.services.notify.summary import build_human_summary
from app.services.notify.zalo import (
    _localize_event_label,
    _localize_severity_label,
    _localize_status_label,
)


DEFAULT_EMAIL_SUBJECT_PREFIX = "Mekong-SALT"


@dataclass(slots=True)
class EmailDeliveryResult:
    """Structured result for a best-effort email delivery call."""

    ok: bool
    message_id: str | None = None
    smtp_response: str | None = None
    error_message: str | None = None


class EmailDeliveryError(RuntimeError):
    """Raised when the demo delivery to email fails."""


def build_email_text(subject: str | None, message: str, payload: dict[str, Any] | None = None) -> str:
    """Build a compact Vietnamese text body for email delivery."""
    lines: list[str] = []
    if subject:
        lines.append(f"Tiêu đề: {subject.strip()}")
    lines.append(f"Nội dung: {message.strip()}")

    extras: list[str] = []
    if payload:
        event = payload.get("event")
        if event:
            extras.append(f"Sự kiện: {_localize_event_label(event)}")
        severity = payload.get("severity")
        if severity:
            extras.append(f"Mức độ: {_localize_severity_label(severity)}")
        status = payload.get("status") or payload.get("outcome_class")
        if status:
            extras.append(f"Trạng thái: {_localize_status_label(status)}")
        if payload.get("station_code"):
            extras.append(f"Trạm: {payload['station_code']}")
        if payload.get("region_code"):
            extras.append(f"Vùng: {payload['region_code']}")
        if payload.get("summary") and payload.get("summary") != message:
            extras.append(f"Tóm tắt: {str(payload['summary']).strip()}")
        if payload.get("plan_summary"):
            extras.append(f"Tóm tắt kế hoạch: {str(payload['plan_summary']).strip()}")
        if payload.get("assessment_summary"):
            extras.append(f"Tóm tắt đánh giá: {str(payload['assessment_summary']).strip()}")
        if payload.get("action_summary"):
            extras.append(f"Tóm lược hành động: {str(payload['action_summary']).strip()}")
        human_summary = build_human_summary(payload, message)
        if human_summary:
            extras.append(f"Diễn giải ngắn: {human_summary}")

    if extras:
        lines.append("")
        lines.append("Chi tiết:")
        lines.extend(f"- {item}" for item in extras)

    body = "\n".join(line for line in lines if line)
    return body[:4_000]


def build_email_message(
    *,
    from_address: str,
    recipient_email: str,
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
) -> EmailMessage:
    """Create an RFC-compliant plain-text email message."""
    email_subject = (subject or message or DEFAULT_EMAIL_SUBJECT_PREFIX).strip()
    text_body = build_email_text(subject, message, payload)
    email_message = EmailMessage()
    email_message["Subject"] = email_subject
    email_message["From"] = from_address
    email_message["To"] = recipient_email
    email_message["Date"] = formatdate(localtime=True)
    email_message["Message-ID"] = make_msgid()

    if payload:
        event = payload.get("event")
        severity = payload.get("severity")
        status = payload.get("status") or payload.get("outcome_class")
        if event:
            email_message["X-Mekong-SALT-Event"] = str(_localize_event_label(event))
        if severity:
            email_message["X-Mekong-SALT-Severity"] = str(_localize_severity_label(severity))
        if status:
            email_message["X-Mekong-SALT-Status"] = str(_localize_status_label(status))
        if payload.get("incident_id"):
            email_message["X-Mekong-SALT-Incident"] = str(payload["incident_id"])

    email_message.set_content(text_body, subtype="plain", charset="utf-8")
    return email_message


async def send_email_message(
    *,
    smtp_host: str,
    smtp_port: int,
    from_address: str,
    recipient_email: str,
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    use_tls: bool = True,
    use_ssl: bool = False,
    timeout_seconds: int = 10,
) -> EmailDeliveryResult:
    """Send a plain-text email through SMTP."""
    return await asyncio.to_thread(
        _send_email_message_sync,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        from_address=from_address,
        recipient_email=recipient_email,
        subject=subject,
        message=message,
        payload=payload,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        use_tls=use_tls,
        use_ssl=use_ssl,
        timeout_seconds=timeout_seconds,
    )


def _send_email_message_sync(
    *,
    smtp_host: str,
    smtp_port: int,
    from_address: str,
    recipient_email: str,
    subject: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    use_tls: bool = True,
    use_ssl: bool = False,
    timeout_seconds: int = 10,
) -> EmailDeliveryResult:
    email_message = build_email_message(
        from_address=from_address,
        recipient_email=recipient_email,
        subject=subject,
        message=message,
        payload=payload,
    )
    timeout = max(int(timeout_seconds), 1)

    try:
        smtp_factory = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_factory(smtp_host, smtp_port, timeout=timeout) as client:
            client.ehlo()
            if use_tls and not use_ssl:
                context = ssl.create_default_context()
                client.starttls(context=context)
                client.ehlo()
            if smtp_username:
                client.login(smtp_username, smtp_password or "")
            refused = client.send_message(email_message)
            if refused:
                raise EmailDeliveryError(f"SMTP refused recipients: {refused!r}")
    except EmailDeliveryError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime safety
        raise EmailDeliveryError(str(exc)) from exc

    return EmailDeliveryResult(
        ok=True,
        message_id=str(email_message["Message-ID"]) if email_message["Message-ID"] else None,
        smtp_response="sent",
    )
