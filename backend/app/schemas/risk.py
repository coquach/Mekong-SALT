"""Schemas for risk and alert entities."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.core.salinity_units import dsm_to_gl
from app.models.enums import AlertStatus, RiskLevel, TrendDirection
from app.schemas.base import EntityReadSchema, ORMBaseSchema
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead


class RiskAssessmentBase(ORMBaseSchema):
    """Shared risk assessment fields."""

    region_id: UUID
    station_id: UUID | None = None
    based_on_reading_id: UUID | None = None
    based_on_weather_id: UUID | None = None
    assessed_at: datetime
    risk_level: RiskLevel
    salinity_dsm: Decimal | None = None
    salinity_gl: Decimal | None = None
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    trend_delta_dsm: Decimal | None = None
    trend_delta_gl: Decimal | None = None
    rule_version: str = Field(default="v1", max_length=50)
    summary: str
    rationale: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalize_salinity_units(self) -> "RiskAssessmentBase":
        if self.salinity_gl is None and self.salinity_dsm is not None:
            self.salinity_gl = dsm_to_gl(self.salinity_dsm)
        if self.trend_delta_gl is None and self.trend_delta_dsm is not None:
            self.trend_delta_gl = dsm_to_gl(self.trend_delta_dsm)
        return self


class RiskAssessmentCreate(RiskAssessmentBase):
    """Schema for creating a risk assessment."""


class RiskAssessmentRead(EntityReadSchema, RiskAssessmentBase):
    """Schema for returning a risk assessment."""


class AlertEventBase(ORMBaseSchema):
    """Shared alert event fields."""

    region_id: UUID
    risk_assessment_id: UUID
    triggered_at: datetime
    severity: RiskLevel
    title: str = Field(max_length=255)
    message: str
    status: AlertStatus = AlertStatus.OPEN
    acknowledged_by: str | None = Field(default=None, max_length=255)
    acknowledged_at: datetime | None = None


class AlertEventCreate(AlertEventBase):
    """Schema for creating an alert event."""


class AlertEventRead(EntityReadSchema, AlertEventBase):
    """Schema for returning an alert event."""


class RiskEvaluationFilters(ORMBaseSchema):
    """Input filters for current risk and alert evaluation."""

    station_id: UUID | None = None
    station_code: str | None = None
    region_id: UUID | None = None
    region_code: str | None = None


class RiskCurrentResponse(ORMBaseSchema):
    """Response payload for a current risk evaluation."""

    assessment: RiskAssessmentRead
    reading: SensorReadingRead
    weather_snapshot: WeatherSnapshotRead | None = None
    agent_run_id: UUID | None = None


class RiskLatestResponse(ORMBaseSchema):
    """Response payload for the latest persisted risk assessment."""

    assessment: RiskAssessmentRead
    reading: SensorReadingRead | None = None
    weather_snapshot: WeatherSnapshotRead | None = None


class AlertEvaluationResponse(ORMBaseSchema):
    """Response payload for alert evaluation."""

    assessment: RiskAssessmentRead
    reading: SensorReadingRead
    weather_snapshot: WeatherSnapshotRead | None = None
    alert: AlertEventRead | None = None
    alert_created: bool
    agent_run_id: UUID | None = None
