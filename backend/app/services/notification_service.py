"""Mock notification services."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditEventType, NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.repositories.ops import NotificationRepository
from app.schemas.notification import NotificationCreate
from app.services.audit_service import write_audit_log


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
    notifications: list[Notification] = []
    for channel, recipient in [
        (NotificationChannel.DASHBOARD, "dashboard"),
        (NotificationChannel.SMS_MOCK, "+84000000000"),
        (NotificationChannel.ZALO_MOCK, "zalo-operator-group"),
        (NotificationChannel.EMAIL_MOCK, "ops@example.local"),
    ]:
        notification = await create_notification(
            session,
            NotificationCreate(
                incident_id=incident_id,
                channel=channel,
                recipient=recipient,
                subject="Mekong-SALT salinity response",
                message=message,
                payload={"mock": True},
            ),
            execution_id=execution_id,
        )
        notifications.append(notification)
    return notifications


async def list_notifications(session: AsyncSession, *, limit: int = 100) -> list[Notification]:
    """List recent notifications."""
    return await NotificationRepository(session).list_recent(limit=limit)

