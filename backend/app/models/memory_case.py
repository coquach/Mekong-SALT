"""Persistent memory case model for context-action-outcome reuse."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MemoryCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reusable execution memory for similar incident retrieval and re-planning."""

    __tablename__ = "memory_cases"

    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    station_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensor_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_assessment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
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
    decision_log_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("decision_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    objective: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    outcome_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    outcome_status_legacy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    context_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    action_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    outcome_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    region = relationship("Region")
    station = relationship("SensorStation")
    risk_assessment = relationship("RiskAssessment")
    incident = relationship("Incident")
    action_plan = relationship("ActionPlan")
    action_execution = relationship("ActionExecution")
    decision_log = relationship("DecisionLog")
