"""Gate persistence model."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import GateStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class Gate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Operational gate or sluice asset managed by the region."""

    __tablename__ = "control_gates"

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
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gate_type: Mapped[str] = mapped_column(String(100), nullable=False, default="sluice")
    status: Mapped[GateStatus] = mapped_column(
        enum_type(GateStatus, "gate_status"),
        nullable=False,
        default=GateStatus.CLOSED,
        index=True,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    location_description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_operated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gate_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="gates")
    station = relationship("SensorStation", back_populates="gates")
