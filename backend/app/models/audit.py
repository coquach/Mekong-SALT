"""Audit and outcome persistence models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AuditEventType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Structured audit event for transparency and traceability."""

    __tablename__ = "audit_logs"

    event_type: Mapped[AuditEventType] = mapped_column(
        enum_type(AuditEventType, "audit_event_type"),
        nullable=False,
        index=True,
    )
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_plan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="audit_logs")
    incident = relationship("Incident", back_populates="audit_logs")
    action_plan = relationship("ActionPlan", back_populates="audit_logs")
    action_execution = relationship("ActionExecution", back_populates="audit_logs")


class ActionOutcome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Post-action outcome record linking metrics to an execution."""

    __tablename__ = "action_outcomes"

    execution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pre_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    post_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)

    execution = relationship("ActionExecution", back_populates="outcomes")
