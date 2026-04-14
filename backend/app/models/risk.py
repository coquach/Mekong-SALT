"""Risk assessment and alert models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AlertStatus, RiskLevel, TrendDirection
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class RiskAssessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted risk assessment derived from observations."""

    __tablename__ = "risk_assessments"

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
    based_on_reading_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensor_readings.id", ondelete="SET NULL"),
        nullable=True,
    )
    based_on_weather_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("weather_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        enum_type(RiskLevel, "risk_level"),
        nullable=False,
        index=True,
    )
    salinity_dsm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    trend_direction: Mapped[TrendDirection] = mapped_column(
        enum_type(TrendDirection, "trend_direction"),
        nullable=False,
        default=TrendDirection.UNKNOWN,
    )
    trend_delta_dsm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    rule_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    rationale: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="risk_assessments")
    station = relationship("SensorStation", back_populates="risk_assessments")
    reading = relationship("SensorReading", back_populates="risk_assessments")
    weather_snapshot = relationship("WeatherSnapshot", back_populates="risk_assessments")
    alert_events = relationship("AlertEvent", back_populates="risk_assessment")
    action_plans = relationship("ActionPlan", back_populates="risk_assessment")
    decision_logs = relationship("DecisionLog", back_populates="risk_assessment")
    incidents = relationship("Incident", back_populates="risk_assessment")


class AlertEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Alert raised from a persisted risk assessment."""

    __tablename__ = "alert_events"

    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    severity: Mapped[RiskLevel] = mapped_column(
        enum_type(RiskLevel, "alert_severity"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        enum_type(AlertStatus, "alert_status"),
        nullable=False,
        default=AlertStatus.OPEN,
    )
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    region = relationship("Region", back_populates="alert_events")
    risk_assessment = relationship("RiskAssessment", back_populates="alert_events")
