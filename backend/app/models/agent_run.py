"""Agent run and observation snapshot models for decision traceability."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Execution trace for risk/plan automation runs."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('started', 'succeeded', 'failed', 'skipped')",
            name="agent_run_status_valid",
        ),
    )

    run_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    trigger_source: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="started")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    trace: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
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

    region = relationship("Region", back_populates="agent_runs")
    station = relationship("SensorStation", back_populates="agent_runs")
    risk_assessment = relationship("RiskAssessment", back_populates="agent_runs")
    incident = relationship("Incident", back_populates="agent_runs")
    action_plan = relationship("ActionPlan", back_populates="agent_runs")
    observation_snapshot = relationship(
        "ObservationSnapshot",
        back_populates="agent_run",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ObservationSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted pre-decision observation context for each run."""

    __tablename__ = "observation_snapshots"

    agent_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="runtime", index=True)

    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
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
    weather_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("weather_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    agent_run = relationship("AgentRun", back_populates="observation_snapshot")
    region = relationship("Region", back_populates="observation_snapshots")
    station = relationship("SensorStation", back_populates="observation_snapshots")
    reading = relationship("SensorReading", back_populates="observation_snapshots")
    weather_snapshot = relationship("WeatherSnapshot", back_populates="observation_snapshots")
