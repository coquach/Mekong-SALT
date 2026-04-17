"""Sensor station and reading models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StationStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class SensorStation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Physical or virtual sensor station."""

    __tablename__ = "sensor_stations"

    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    station_type: Mapped[str] = mapped_column(String(100), nullable=False, default="salinity")
    status: Mapped[StationStatus] = mapped_column(
        enum_type(StationStatus, "station_status"),
        nullable=False,
        default=StationStatus.ACTIVE,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    location_description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    station_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="sensor_stations")
    readings = relationship(
        "SensorReading",
        back_populates="station",
        cascade="all, delete-orphan",
    )
    risk_assessments = relationship("RiskAssessment", back_populates="station")
    incidents = relationship("Incident", back_populates="station")
    monitoring_goals = relationship("MonitoringGoal", back_populates="station")
    agent_runs = relationship("AgentRun", back_populates="station")
    observation_snapshots = relationship("ObservationSnapshot", back_populates="station")


class SensorReading(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Time-series sensor measurement."""

    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint(
            "station_id",
            "recorded_at",
            "source",
            name="uq_sensor_readings_station_recorded_source",
        ),
    )

    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sensor_stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    salinity_dsm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    water_level_m: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    wind_speed_mps: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    wind_direction_deg: Mapped[int | None] = mapped_column(nullable=True)
    flow_rate_m3s: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    battery_level_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="simulator")
    context_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    station = relationship("SensorStation", back_populates="readings")
    risk_assessments = relationship("RiskAssessment", back_populates="reading")
    observation_snapshots = relationship("ObservationSnapshot", back_populates="reading")
