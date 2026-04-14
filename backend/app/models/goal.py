"""Monitoring goal model for periodic planning automation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MonitoringGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted automation goal configuration for scheduled planning runs."""

    __tablename__ = "monitoring_goals"
    __table_args__ = (
        CheckConstraint(
            "warning_threshold_dsm > 0",
            name="monitoring_goal_warning_threshold_positive",
        ),
        CheckConstraint(
            "critical_threshold_dsm > warning_threshold_dsm",
            name="monitoring_goal_critical_gt_warning",
        ),
        CheckConstraint(
            "evaluation_interval_minutes >= 1",
            name="monitoring_goal_interval_positive",
        ),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
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
    objective: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    warning_threshold_dsm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    critical_threshold_dsm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    evaluation_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_run_plan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    region = relationship("Region", back_populates="monitoring_goals")
    station = relationship("SensorStation", back_populates="monitoring_goals")
    last_run_plan = relationship("ActionPlan")
