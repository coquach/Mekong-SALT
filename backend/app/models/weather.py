"""Weather snapshot model."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WeatherSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Weather and tidal context captured for a region."""

    __tablename__ = "weather_snapshots"

    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    wind_speed_mps: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    wind_direction_deg: Mapped[int | None] = mapped_column(nullable=True)
    tide_level_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    condition_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="weather_snapshots")
    risk_assessments = relationship("RiskAssessment", back_populates="weather_snapshot")
    observation_snapshots = relationship("ObservationSnapshot", back_populates="weather_snapshot")

