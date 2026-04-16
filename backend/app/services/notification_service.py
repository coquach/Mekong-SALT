"""Mock notification services."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import AuditEventType, NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.repositories.ops import NotificationRepository
from app.schemas.notification import NotificationCreate
from app.services.audit_service import write_audit_log


_DEFAULT_CHANNEL_RECIPIENTS: tuple[tuple[NotificationChannel, str], ...] = (
    (NotificationChannel.DASHBOARD, "dashboard"),
    (NotificationChannel.SMS_MOCK, "+84000000000"),
    (NotificationChannel.ZALO_MOCK, "zalo-operator-group"),
    (NotificationChannel.EMAIL_MOCK, "ops@example.local"),
)


async def create_notification(
    session: AsyncSession,
    payload: NotificationCreate,
    *,
    execution_id: UUID | None = None,
    actor_name: str = "notification-service",
) -> Notification:
    """Create a mock notification and mark it as sent."""
    notification = Notification(
        incident_id=payload.incident_id,
        execution_id=execution_id,
        channel=payload.channel,
        status=NotificationStatus.SENT,
        recipient=payload.recipient,
        subject=payload.subject,
        message=payload.message,
        payload=payload.payload,
        sent_at=datetime.now(UTC),
    )
    await NotificationRepository(session).add(notification)
    await write_audit_log(
        session,
        event_type=AuditEventType.NOTIFICATION,
        actor_name=actor_name,
        incident_id=payload.incident_id,
        action_execution_id=execution_id,
        summary=f"Mock notification sent via {payload.channel.value}.",
        payload={"recipient": payload.recipient, "subject": payload.subject},
    )
    return notification


async def create_execution_alert_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID | None,
    execution_id: UUID | None,
    message: str,
) -> list[Notification]:
    """Create dashboard/SMS/Zalo/email mock notifications for send_alert."""
    return await create_operational_notifications(
        session,
        incident_id=incident_id,
        execution_id=execution_id,
        subject="Mekong-SALT salinity response",
        message=message,
        payload={"mock": True, "event": "execution_alert"},
    )


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
    """Create notifications across configured operational channels (mock-friendly)."""
    notifications: list[Notification] = []
    for channel, recipient in (channel_recipients or _DEFAULT_CHANNEL_RECIPIENTS):
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


async def create_incident_created_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID,
    title: str,
    severity: str,
    source: str,
) -> list[Notification]:
    """Notify stakeholders when an incident is opened."""
    return await create_operational_notifications(
        session,
        incident_id=incident_id,
        subject=f"Incident opened: {severity.upper()} salinity",
        message=f"Incident '{title}' was opened from source '{source}'.",
        payload={
            "event": "incident_created",
            "severity": severity,
            "title": title,
            "source": source,
        },
    )


async def create_plan_created_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID | None,
    action_plan_id: UUID,
    objective: str,
    status: str,
) -> list[Notification]:
    """Notify stakeholders when a plan is generated."""
    return await create_operational_notifications(
        session,
        incident_id=incident_id,
        subject=f"Action plan generated ({status})",
        message=f"Plan '{action_plan_id}' generated for objective: {objective}",
        payload={
            "event": "plan_created",
            "action_plan_id": str(action_plan_id),
            "status": status,
            "objective": objective,
        },
    )


async def create_execution_summary_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID | None,
    execution_id: UUID | None,
    action_plan_id: UUID,
    outcome_class: str,
    summary: str,
    execution_count: int,
    replan_recommended: bool,
) -> list[Notification]:
    """Notify stakeholders after execution finishes and feedback is available."""
    return await create_operational_notifications(
        session,
        incident_id=incident_id,
        execution_id=execution_id,
        subject=f"Execution summary: {outcome_class}",
        message=summary,
        payload={
            "event": "execution_summary",
            "action_plan_id": str(action_plan_id),
            "execution_count": execution_count,
            "outcome_class": outcome_class,
            "replan_recommended": replan_recommended,
        },
    )


async def list_notifications(session: AsyncSession, *, limit: int = 100) -> list[Notification]:
    """List recent notifications."""
    return await NotificationRepository(session).list_recent(limit=limit)


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
            message=f"Notification '{notification_id}' was not found.",
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
        summary="Notification marked as read.",
        payload={"notification_id": str(notification.id)},
    )
    await session.commit()
    await session.refresh(notification)
    return notification

