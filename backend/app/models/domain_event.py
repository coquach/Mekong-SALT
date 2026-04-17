"""Durable domain event model for realtime dashboard streaming."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DomainEvent(Base):
    """Append-only domain events used by cursor-based SSE consumers."""

    __tablename__ = "domain_events"

    sequence: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    aggregate_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    aggregate_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    region_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    incident_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    action_plan_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    execution_batch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
