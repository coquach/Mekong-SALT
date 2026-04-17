"""Feedback lifecycle persistence models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class FeedbackSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Captured before/after observation used for outcome evaluation."""

    __tablename__ = "feedback_snapshots"

    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("execution_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_assessment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    station_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensor_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reading_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensor_readings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    snapshot_kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reading_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    salinity_dsm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    water_level_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="feedback-evaluator")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    execution_batch = relationship("ExecutionBatch", back_populates="feedback_snapshots")
    action_plan = relationship("ActionPlan")
    action_execution = relationship("ActionExecution", back_populates="feedback_snapshots")


class OutcomeEvaluation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted outcome taxonomy evaluation for one execution batch."""

    __tablename__ = "outcome_evaluations"

    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("execution_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    before_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feedback_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    after_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feedback_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    outcome_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status_legacy: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_salinity_dsm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    latest_salinity_dsm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    delta_dsm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    replan_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    replan_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    evaluator_name: Mapped[str] = mapped_column(String(255), nullable=False, default="feedback-evaluator")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    execution_batch = relationship("ExecutionBatch", back_populates="outcome_evaluations")
    action_plan = relationship("ActionPlan")
    action_execution = relationship("ActionExecution", back_populates="outcome_evaluations")
    before_snapshot = relationship("FeedbackSnapshot", foreign_keys=[before_snapshot_id])
    after_snapshot = relationship("FeedbackSnapshot", foreign_keys=[after_snapshot_id])
