"""Send a demo notification through the Zalo delivery path."""

from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.db.session import AsyncSessionFactory, close_database_engine
from app.models.enums import NotificationChannel
from app.schemas.notification import NotificationCreate
from app.services.notify import create_notification


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send a demo Zalo notification.")
    parser.add_argument(
        "--subject",
        default="Mekong-SALT demo: cảnh báo Zalo",
        help="Notification subject.",
    )
    parser.add_argument(
        "--message",
        default="Đây là tin nhắn demo từ backend qua luồng Zalo.",
        help="Notification message.",
    )
    parser.add_argument(
        "--recipient",
        default="zalo-operator-group",
        help="Logical recipient label stored in DB.",
    )
    parser.add_argument(
        "--incident-id",
        default=None,
        help="Optional incident UUID to link to the notification.",
    )
    return parser


async def _run(subject: str, message: str, recipient: str, incident_id: str | None) -> None:
    async with AsyncSessionFactory() as session:
        notification = await create_notification(
            session,
            NotificationCreate(
                incident_id=UUID(incident_id) if incident_id else None,
                channel=NotificationChannel.ZALO_MOCK,
                recipient=recipient,
                subject=subject,
                message=message,
                payload={
                    "event": "demo_zalo_notification",
                    "channel": "zalo_mock",
                },
            ),
        )
        await session.commit()
        await session.refresh(notification)

        delivery = notification.payload.get("delivery") if notification.payload else None
        print(
            "notification_sent "
            f"id={notification.id} "
            f"status={notification.status.value} "
            f"channel={notification.channel.value} "
            f"delivery_mode={delivery.get('mode') if isinstance(delivery, dict) else 'unknown'} "
            f"message_id={delivery.get('message_id') if isinstance(delivery, dict) else 'unknown'}"
        )


async def _main_async() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        await _run(
            subject=args.subject,
            message=args.message,
            recipient=args.recipient,
            incident_id=args.incident_id,
        )
    finally:
        await close_database_engine()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
