"""Schemas for risk and alert entities."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import AlertStatus, RiskLevel, TrendDirection
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class RiskAssessmentBase(ORMBaseSchema):
    """Shared risk assessment fields."""

    region_id: UUID
    station_id: UUID | None = None
    based_on_reading_id: UUID | None = None
    based_on_weather_id: UUID | None = None
    assessed_at: datetime
    risk_level: RiskLevel
    salinity_dsm: Decimal | None = None
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    trend_delta_dsm: Decimal | None = None
    rule_version: str = Field(default="v1", max_length=50)
    summary: str
    rationale: dict[str, Any] | None = None


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

