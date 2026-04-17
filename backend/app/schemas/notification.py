"""Schemas for mock notifications."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import NotificationChannel, NotificationStatus
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class NotificationRead(EntityReadSchema):
    """Notification delivery record."""

    incident_id: UUID | None = None
    execution_id: UUID | None = None
    channel: NotificationChannel
    status: NotificationStatus
    recipient: str
    subject: str | None = None
    message: str
    payload: dict[str, Any] | None = None
    sent_at: datetime | None = None


class NotificationCreate(ORMBaseSchema):
    """Manual notification request."""

    incident_id: UUID | None = None
    channel: NotificationChannel = NotificationChannel.DASHBOARD
    recipient: str = Field(max_length=255)
    subject: str | None = Field(default=None, max_length=255)
    message: str
    payload: dict[str, Any] | None = None


class NotificationCollection(ORMBaseSchema):
    """Notification list response."""

    items: list[NotificationRead]
    count: int

