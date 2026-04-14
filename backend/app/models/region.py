"""Region persistence model."""

from typing import Any

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Region(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Administrative or operational region in the Mekong Delta."""

    __tablename__ = "regions"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    province: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Vietnam")
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    crop_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sensor_stations = relationship("SensorStation", back_populates="region")
    weather_snapshots = relationship("WeatherSnapshot", back_populates="region")
    risk_assessments = relationship("RiskAssessment", back_populates="region")
    alert_events = relationship("AlertEvent", back_populates="region")
    action_plans = relationship("ActionPlan", back_populates="region")
    action_executions = relationship("ActionExecution", back_populates="region")
    decision_logs = relationship("DecisionLog", back_populates="region")
    incidents = relationship("Incident", back_populates="region")
    audit_logs = relationship("AuditLog", back_populates="region")
