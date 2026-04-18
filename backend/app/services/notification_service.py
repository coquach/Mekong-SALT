"""Notification delivery services."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import AuditEventType, NotificationChannel, NotificationStatus
from app.models.domain_event import DomainEvent
from app.models.notification import Notification
from app.repositories.ops import NotificationRepository
from app.schemas.notification import NotificationCreate
from app.services.audit_service import write_audit_log
from app.services.domain_event_service import DomainEventNotificationDispatcher
from app.services.notify.email import EmailDeliveryError, send_email_message
from app.services.notify.zalo import (
    DEFAULT_ZALO_MESSAGE_ENDPOINT,
    DEFAULT_ZALO_TEMPLATE_MESSAGE_ENDPOINT,
    ZaloDeliveryError,
    send_zalo_template_message,
    send_zalo_message,
)


_DEFAULT_CHANNEL_RECIPIENTS: tuple[tuple[NotificationChannel, str], ...] = (
    (NotificationChannel.DASHBOARD, "dashboard"),
    (NotificationChannel.EMAIL_MOCK, "ops@example.local"),
)

_CHANNEL_LABELS_VI = {
    NotificationChannel.DASHBOARD.value: "bảng điều khiển",
    NotificationChannel.SMS_MOCK.value: "SMS mô phỏng",
    NotificationChannel.ZALO_MOCK.value: "Zalo mô phỏng",
    NotificationChannel.EMAIL_MOCK.value: "email",
}


class MockDomainEventNotificationDispatcher(DomainEventNotificationDispatcher):
    """Map domain events to existing mock channel fanout behavior."""

    async def dispatch(self, session: AsyncSession, event: DomainEvent) -> None:
        if not event.event_type.startswith("notification."):
            return

        payload = dict(event.payload or {})
        subject = str(payload.get("subject") or payload.get("summary") or "Thông báo Mekong-SALT")
        message = str(payload.get("message") or payload.get("summary") or "")
        incident_id = event.incident_id
        execution_id = _parse_uuid(payload.get("execution_id"))
        details = payload.get("details")
        if not isinstance(details, dict):
            details = {}
        details.setdefault("event", event.event_type.removeprefix("notification."))
        details.setdefault("dedupe_key", f"{event.sequence}:{event.event_type}")

        await create_operational_notifications(
            session,
            incident_id=incident_id,
            execution_id=execution_id,
            subject=subject,
            message=message,
            payload=details,
            actor_name="domain-event-dispatcher",
            channel_recipients=_channel_recipients_from_event_payload(payload),
        )


def get_domain_event_notification_dispatcher() -> DomainEventNotificationDispatcher:
    """Return the default domain-event-to-notification dispatcher."""
    return MockDomainEventNotificationDispatcher()


async def create_notification(
    session: AsyncSession,
    payload: NotificationCreate,
    *,
    execution_id: UUID | None = None,
    actor_name: str = "notification-service",
) -> Notification:
    """Create a notification record and attempt live delivery when enabled."""
    settings = get_settings()
    payload_body = dict(payload.payload or {})
    dedupe_key = _build_notification_dedupe_key(
        channel=payload.channel,
        recipient=payload.recipient,
        payload=payload_body,
        incident_id=payload.incident_id,
        execution_id=execution_id,
    )
    if dedupe_key is not None:
        payload_body["dedupe_key"] = dedupe_key
        existing_notification = await _find_recent_duplicate_notification(
            session,
            dedupe_key=dedupe_key,
            channel=payload.channel,
            recipient=payload.recipient,
            incident_id=payload.incident_id,
            execution_id=execution_id,
        )
        if existing_notification is not None:
            return existing_notification

    notification = Notification(
        incident_id=payload.incident_id,
        execution_id=execution_id,
        channel=payload.channel,
        status=NotificationStatus.PENDING,
        recipient=payload.recipient,
        subject=payload.subject,
        message=payload.message,
        payload=payload_body,
    )

    delivery_mode = "mock"
    delivery_error: str | None = None
    delivery_message_id: str | None = None
    if payload.channel is NotificationChannel.ZALO_MOCK:
        delivery = await _attempt_zalo_delivery(
            settings=settings,
            subject=payload.subject,
            message=payload.message,
            payload=payload.payload or {},
        )
        delivery_mode = delivery.mode
        delivery_message_id = delivery.message_id
        delivery_error = delivery.error_message
        notification.status = NotificationStatus.SENT if delivery.ok else NotificationStatus.FAILED
        if delivery.ok:
            notification.sent_at = datetime.now(UTC)
        notification.payload = _merge_delivery_payload(
            payload=payload_body,
            mode=delivery.mode,
            provider="mock" if delivery.mode == "mock" else "zalo",
            message_id=delivery.message_id,
            error_message=delivery.error_message,
        )
    elif payload.channel is NotificationChannel.EMAIL_MOCK:
        delivery = await _attempt_email_delivery(
            settings=settings,
            subject=payload.subject,
            message=payload.message,
            payload=payload.payload or {},
            recipient_email=payload.recipient,
        )
        delivery_mode = delivery.mode
        delivery_message_id = delivery.message_id
        delivery_error = delivery.error_message
        notification.status = NotificationStatus.SENT if delivery.ok else NotificationStatus.FAILED
        if delivery.ok:
            notification.sent_at = datetime.now(UTC)
        notification.payload = _merge_delivery_payload(
            payload=payload_body,
            mode=delivery.mode,
            provider="mock" if delivery.mode == "mock" else "email",
            message_id=delivery.message_id,
            error_message=delivery.error_message,
        )
    else:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(UTC)

    await NotificationRepository(session).add(notification)
    await write_audit_log(
        session,
        event_type=AuditEventType.NOTIFICATION,
        actor_name=actor_name,
        incident_id=payload.incident_id,
        action_execution_id=execution_id,
        summary=(
            (
                f"Không gửi được thông báo qua kênh {_localize_channel_label(payload.channel)} ({_localize_delivery_mode_label(delivery_mode)})."
                if delivery_error
                else f"Đã gửi thông báo qua kênh {_localize_channel_label(payload.channel)} ({_localize_delivery_mode_label(delivery_mode)})."
            )
            if payload.channel in {NotificationChannel.ZALO_MOCK, NotificationChannel.EMAIL_MOCK}
            else f"Đã tạo thông báo mô phỏng qua kênh {_localize_channel_label(payload.channel)}."
        ),
        payload={
            "recipient": payload.recipient,
            "subject": payload.subject,
            "delivery_mode": delivery_mode,
            "delivery_message_id": delivery_message_id,
            "delivery_error": delivery_error,
        },
    )
    return notification


async def create_operational_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID | None,
    subject: str,
    message: str,
    payload: dict | None = None,
    execution_id: UUID | None = None,
    actor_name: str = "notification-service",
    channel_recipients: tuple[tuple[NotificationChannel, str], ...] | None = None,
) -> list[Notification]:
    """Create operational notifications and trigger delivery-only email sends."""
    notifications: list[Notification] = []
    for channel, recipient in (channel_recipients or _DEFAULT_CHANNEL_RECIPIENTS):
        if channel is NotificationChannel.EMAIL_MOCK:
            await _deliver_email_notification(
                settings=get_settings(),
                session=session,
                subject=subject,
                message=message,
                payload=payload or {},
                recipient_email=recipient,
                incident_id=incident_id,
                execution_id=execution_id,
                actor_name=actor_name,
            )
            continue
        notification = await create_notification(
            session,
            NotificationCreate(
                incident_id=incident_id,
                channel=channel,
                recipient=recipient,
                subject=subject,
                message=message,
                payload=payload or {},
            ),
            execution_id=execution_id,
            actor_name=actor_name,
        )
        notifications.append(notification)
    return notifications


@dataclass(slots=True)
class _ZaloDeliveryOutcome:
    ok: bool
    mode: str
    message_id: str | None = None
    error_message: str | None = None


async def _attempt_zalo_delivery(
    *,
    settings: Any,
    subject: str | None,
    message: str,
    payload: dict[str, Any],
) -> _ZaloDeliveryOutcome:
    if not getattr(settings, "zalo_notifications_enabled", False):
        return _ZaloDeliveryOutcome(ok=True, mode="mock")

    delivery_mode = str(getattr(settings, "zalo_delivery_mode", "template") or "template").strip().lower()
    access_token = getattr(settings, "zalo_oa_access_token", None)
    recipient_phone_number = getattr(settings, "zalo_oa_recipient_phone_number", None)
    recipient_user_id = getattr(settings, "zalo_oa_recipient_user_id", None)
    endpoint = getattr(settings, "zalo_oa_message_endpoint", None) or DEFAULT_ZALO_MESSAGE_ENDPOINT
    template_endpoint = (
        getattr(settings, "zalo_oa_template_message_endpoint", None) or DEFAULT_ZALO_TEMPLATE_MESSAGE_ENDPOINT
    )
    template_id = getattr(settings, "zalo_oa_template_id", None)
    timeout_seconds = int(getattr(settings, "zalo_oa_timeout_seconds", 10) or 10)

    if access_token is None:
        return _ZaloDeliveryOutcome(
            ok=False,
            mode=delivery_mode,
            error_message="Đã bật Zalo nhưng thiếu access token.",
        )

    try:
        access_token_value = (
            access_token.get_secret_value() if hasattr(access_token, "get_secret_value") else str(access_token)
        )
        if delivery_mode == "template":
            if not template_id:
                return _ZaloDeliveryOutcome(
                    ok=False,
                    mode="template",
                    error_message="Đã bật chế độ template Zalo nhưng thiếu template ID.",
                )
            if recipient_phone_number is None:
                return _ZaloDeliveryOutcome(
                    ok=False,
                    mode="template",
                    error_message="Chế độ template Zalo cần số điện thoại người nhận.",
                )
            result = await send_zalo_template_message(
                access_token=access_token_value,
                template_id=str(template_id),
                recipient_phone_number=str(recipient_phone_number),
                subject=subject,
                message=message,
                payload=payload,
                endpoint=str(template_endpoint),
                timeout_seconds=timeout_seconds,
            )
        else:
            if recipient_user_id is None:
                return _ZaloDeliveryOutcome(
                    ok=False,
                    mode="text",
                    error_message="Chế độ text Zalo cần UID người nhận.",
                )
            result = await send_zalo_message(
                access_token=access_token_value,
                recipient_user_id=str(recipient_user_id),
                subject=subject,
                message=message,
                payload=payload,
                endpoint=str(endpoint),
                timeout_seconds=timeout_seconds,
            )
    except ZaloDeliveryError as exc:
        return _ZaloDeliveryOutcome(ok=False, mode=delivery_mode, error_message=str(exc))
    except Exception as exc:  # pragma: no cover - network/runtime safety
        return _ZaloDeliveryOutcome(ok=False, mode=delivery_mode, error_message=str(exc))

    return _ZaloDeliveryOutcome(ok=True, mode=delivery_mode, message_id=result.message_id)


@dataclass(slots=True)
class _EmailDeliveryOutcome:
    ok: bool
    mode: str
    message_id: str | None = None
    error_message: str | None = None


async def _attempt_email_delivery(
    *,
    settings: Any,
    subject: str | None,
    message: str,
    payload: dict[str, Any],
    recipient_email: str,
) -> _EmailDeliveryOutcome:
    if not getattr(settings, "email_notifications_enabled", False):
        return _EmailDeliveryOutcome(ok=True, mode="mock")

    smtp_host = getattr(settings, "email_smtp_host", None)
    email_from_address = getattr(settings, "email_from_address", None)
    smtp_username = getattr(settings, "email_smtp_username", None)
    smtp_password = getattr(settings, "email_smtp_password", None)
    smtp_port = int(getattr(settings, "email_smtp_port", 587) or 587)
    use_tls = bool(getattr(settings, "email_use_tls", True))
    use_ssl = bool(getattr(settings, "email_use_ssl", False))
    timeout_seconds = int(getattr(settings, "email_timeout_seconds", 10) or 10)

    if smtp_host is None:
        return _EmailDeliveryOutcome(
            ok=False,
            mode="smtp",
            error_message="Đã bật email nhưng thiếu SMTP host.",
        )

    from_address = str(email_from_address or smtp_username or "").strip()
    if not from_address:
        return _EmailDeliveryOutcome(
            ok=False,
            mode="smtp",
            error_message="Đã bật email nhưng thiếu địa chỉ người gửi.",
        )

    try:
        smtp_password_value = None
        if smtp_password is not None:
            smtp_password_value = (
                smtp_password.get_secret_value()
                if hasattr(smtp_password, "get_secret_value")
                else str(smtp_password)
            )
        result = await send_email_message(
            smtp_host=str(smtp_host),
            smtp_port=smtp_port,
            from_address=from_address,
            recipient_email=str(recipient_email),
            subject=subject,
            message=message,
            payload=payload,
            smtp_username=str(smtp_username) if smtp_username else None,
            smtp_password=smtp_password_value,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout_seconds=timeout_seconds,
        )
    except EmailDeliveryError as exc:
        return _EmailDeliveryOutcome(ok=False, mode="smtp", error_message=str(exc))
    except Exception as exc:  # pragma: no cover - network/runtime safety
        return _EmailDeliveryOutcome(ok=False, mode="smtp", error_message=str(exc))

    return _EmailDeliveryOutcome(ok=True, mode="smtp", message_id=result.message_id)


async def _deliver_email_notification(
    *,
    settings: Any,
    session: AsyncSession,
    subject: str | None,
    message: str,
    payload: dict[str, Any],
    recipient_email: str,
    incident_id: UUID | None,
    execution_id: UUID | None,
    actor_name: str,
) -> _EmailDeliveryOutcome:
    delivery = await _attempt_email_delivery(
        settings=settings,
        subject=subject,
        message=message,
        payload=payload,
        recipient_email=recipient_email,
    )
    await write_audit_log(
        session,
        event_type=AuditEventType.NOTIFICATION,
        actor_name=actor_name,
        incident_id=incident_id,
        action_execution_id=execution_id,
        summary=(
            f"Không gửi được thông báo email ({_localize_delivery_mode_label(delivery.mode)})."
            if not delivery.ok
            else f"Đã gửi thông báo email ({_localize_delivery_mode_label(delivery.mode)})."
        ),
        payload={
            "recipient": recipient_email,
            "subject": subject,
            "delivery_mode": delivery.mode,
            "delivery_message_id": delivery.message_id,
            "delivery_error": delivery.error_message,
        },
    )
    return delivery


def _merge_delivery_payload(
    *,
    payload: dict[str, Any] | None,
    mode: str,
    provider: str,
    message_id: str | None,
    error_message: str | None,
) -> dict[str, Any]:
    merged = dict(payload or {})
    delivery = dict(merged.get("delivery") or {})
    delivery.update(
        {
            "provider": provider,
            "mode": mode,
            "message_id": message_id,
            "error_message": error_message,
            "delivered_at": datetime.now(UTC).isoformat() if error_message is None else None,
        }
    )
    merged["delivery"] = delivery
    return merged


def _build_notification_dedupe_key(
    *,
    channel: NotificationChannel,
    recipient: str,
    payload: dict[str, Any],
    incident_id: UUID | None,
    execution_id: UUID | None,
) -> str | None:
    explicit_key = payload.get("dedupe_key")
    if explicit_key is None:
        return None
    return (
        f"{channel.value}:{recipient}:{explicit_key}:"
        f"{incident_id if incident_id is not None else '-'}:"
        f"{execution_id if execution_id is not None else '-'}"
    )


async def _find_recent_duplicate_notification(
    session: AsyncSession,
    *,
    dedupe_key: str,
    channel: NotificationChannel,
    recipient: str,
    incident_id: UUID | None,
    execution_id: UUID | None,
) -> Notification | None:
    recent_notifications = await NotificationRepository(session).list_recent(limit=200)
    for notification in recent_notifications:
        if notification.channel is not channel:
            continue
        if notification.recipient != recipient:
            continue
        if notification.incident_id != incident_id:
            continue
        if notification.execution_id != execution_id:
            continue
        if notification.status is not NotificationStatus.SENT:
            continue
        payload = notification.payload or {}
        delivery = payload.get("delivery") if isinstance(payload.get("delivery"), dict) else {}
        if payload.get("dedupe_key") == dedupe_key or delivery.get("dedupe_key") == dedupe_key:
            return notification
    return None


def _extract_uuid(payload: dict | None, key: str) -> UUID | None:
    raw = (payload or {}).get(key)
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _parse_uuid(raw: Any) -> UUID | None:
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _channel_recipients_from_event_payload(
    payload: dict[str, Any],
) -> tuple[tuple[NotificationChannel, str], ...]:
    _ = payload
    return _DEFAULT_CHANNEL_RECIPIENTS


def _localize_channel_label(channel: NotificationChannel) -> str:
    return _CHANNEL_LABELS_VI.get(channel.value, channel.value)


def _localize_delivery_mode_label(value: str) -> str:
    mode = str(value).strip().lower()
    if mode == "mock":
        return "mô phỏng"
    if mode == "smtp":
        return "SMTP"
    return mode


async def list_notifications(session: AsyncSession, *, limit: int = 100) -> list[Notification]:
    """List recent notifications."""
    notifications = await NotificationRepository(session).list_recent(limit=limit)
    return [
        notification
        for notification in notifications
        if notification.channel is not NotificationChannel.EMAIL_MOCK
    ]


async def mark_notification_read(
    session: AsyncSession,
    *,
    notification_id: UUID,
    actor_name: str = "operator",
) -> Notification:
    """Mark a notification as read via payload flag until a dedicated column exists."""
    notification = await NotificationRepository(session).get(notification_id)
    if notification is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="notification_not_found",
            message=f"Không tìm thấy thông báo '{notification_id}'.",
        )

    # Phase 1 compatibility: keep schema stable and annotate read state in payload.
    payload = dict(notification.payload or {})
    payload["read"] = True
    payload["read_at"] = datetime.now(UTC).isoformat()
    notification.payload = payload

    await write_audit_log(
        session,
        event_type=AuditEventType.NOTIFICATION,
        actor_name=actor_name,
        incident_id=notification.incident_id,
        action_execution_id=notification.execution_id,
        summary="Đã đánh dấu thông báo là đã đọc.",
        payload={"notification_id": str(notification.id)},
    )
    await session.commit()
    await session.refresh(notification)
    return notification



