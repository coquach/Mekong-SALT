"""Notification persistence models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Mock notification delivery record."""

    __tablename__ = "notifications"

    incident_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        enum_type(NotificationChannel, "notification_channel"),
        nullable=False,
        index=True,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        enum_type(NotificationStatus, "notification_status"),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="notifications")
    execution = relationship("ActionExecution", back_populates="notifications")

