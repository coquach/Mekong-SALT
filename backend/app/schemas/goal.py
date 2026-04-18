"""Schemas for monitoring goal configuration."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.core.salinity_units import are_units_consistent, dsm_to_gl, gl_to_dsm
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class GoalThresholds(ORMBaseSchema):
    """Threshold configuration for a monitoring goal."""

    warning_threshold_dsm: Decimal | None = Field(default=None, gt=0)
    critical_threshold_dsm: Decimal | None = Field(default=None, gt=0)
    warning_threshold_gl: Decimal | None = Field(default=None, gt=0)
    critical_threshold_gl: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        warning_dsm = self.warning_threshold_dsm
        critical_dsm = self.critical_threshold_dsm
        warning_gl = self.warning_threshold_gl
        critical_gl = self.critical_threshold_gl

        if warning_dsm is None and warning_gl is None:
            raise ValueError("Either warning_threshold_dsm or warning_threshold_gl is required.")
        if critical_dsm is None and critical_gl is None:
            raise ValueError("Either critical_threshold_dsm or critical_threshold_gl is required.")

        if warning_dsm is None:
            warning_dsm = gl_to_dsm(warning_gl)
        if critical_dsm is None:
            critical_dsm = gl_to_dsm(critical_gl)
        if warning_dsm is None or critical_dsm is None:
            raise ValueError("Unable to normalize warning/critical thresholds.")

        normalized_warning_gl = dsm_to_gl(warning_dsm)
        normalized_critical_gl = dsm_to_gl(critical_dsm)
        if normalized_warning_gl is None or normalized_critical_gl is None:
            raise ValueError("Unable to normalize warning/critical thresholds.")

        if warning_gl is not None and not are_units_consistent(
            salinity_dsm=warning_dsm, salinity_gl=warning_gl
        ):
            raise ValueError(
                "warning_threshold_dsm and warning_threshold_gl are inconsistent."
            )
        if critical_gl is not None and not are_units_consistent(
            salinity_dsm=critical_dsm, salinity_gl=critical_gl
        ):
            raise ValueError(
                "critical_threshold_dsm and critical_threshold_gl are inconsistent."
            )

        if critical_dsm <= warning_dsm:
            raise ValueError("critical threshold must be greater than warning threshold.")

        self.warning_threshold_dsm = warning_dsm
        self.critical_threshold_dsm = critical_dsm
        self.warning_threshold_gl = normalized_warning_gl
        self.critical_threshold_gl = normalized_critical_gl
        return self


class MonitoringGoalBase(ORMBaseSchema):
    """Shared fields for monitoring goal payloads."""

    name: str = Field(min_length=3, max_length=150)
    description: str | None = None
    region_id: UUID
    station_id: UUID | None = None
    objective: str = Field(min_length=3, max_length=255)
    provider: Literal["mock", "gemini"] | None = None
    thresholds: GoalThresholds
    evaluation_interval_minutes: int = Field(ge=1, le=10080)
    is_active: bool = True


class MonitoringGoalCreate(MonitoringGoalBase):
    """Payload for creating a monitoring goal."""


class MonitoringGoalUpdate(ORMBaseSchema):
    """Payload for updating a monitoring goal."""

    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = None
    region_id: UUID | None = None
    station_id: UUID | None = None
    objective: str | None = Field(default=None, min_length=3, max_length=255)
    provider: Literal["mock", "gemini"] | None = None
    thresholds: GoalThresholds | None = None
    evaluation_interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    is_active: bool | None = None


class MonitoringGoalRead(EntityReadSchema):
    """Monitoring goal read model."""

    name: str
    description: str | None = None
    region_id: UUID
    station_id: UUID | None = None
    objective: str
    provider: Literal["mock", "gemini"] | None = None
    thresholds: GoalThresholds
    evaluation_interval_minutes: int
    is_active: bool
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    last_run_plan_id: UUID | None = None
    last_processed_reading_id: UUID | None = None


class MonitoringGoalCollection(ORMBaseSchema):
    """Collection response payload for goal listing."""

    items: list[MonitoringGoalRead]
    count: int
