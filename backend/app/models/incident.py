"""Incident persistence model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import IncidentStatus, RiskLevel
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Operational salinity incident created from risk evidence."""

    __tablename__ = "incidents"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[RiskLevel] = mapped_column(
        enum_type(RiskLevel, "incident_severity"),
        nullable=False,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        enum_type(IncidentStatus, "incident_status"),
        nullable=False,
        default=IncidentStatus.OPEN,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="risk_engine")
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    region = relationship("Region", back_populates="incidents")
    station = relationship("SensorStation", back_populates="incidents")
    risk_assessment = relationship("RiskAssessment", back_populates="incidents")
    action_plans = relationship("ActionPlan", back_populates="incident")
    notifications = relationship("Notification", back_populates="incident")
    audit_logs = relationship("AuditLog", back_populates="incident")

