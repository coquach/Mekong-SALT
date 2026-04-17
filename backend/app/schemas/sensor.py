"""Schemas for sensor stations and readings."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.core.salinity_units import are_units_consistent, dsm_to_gl, gl_to_dsm
from app.models.enums import StationStatus
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class SensorStationBase(ORMBaseSchema):
    """Shared sensor station fields."""

    region_id: UUID
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    station_type: str = Field(default="salinity", max_length=100)
    status: StationStatus = StationStatus.ACTIVE
    latitude: Decimal
    longitude: Decimal
    location_description: str | None = None
    installed_at: datetime | None = None
    station_metadata: dict[str, Any] | None = None


class SensorStationCreate(SensorStationBase):
    """Schema for creating a sensor station."""


class SensorStationRead(EntityReadSchema, SensorStationBase):
    """Schema for returning a sensor station."""


class SensorStationSummary(ORMBaseSchema):
    """Compact station shape embedded in reading responses."""

    id: UUID
    region_id: UUID
    code: str
    name: str
    station_type: str
    status: StationStatus


class SensorReadingBase(ORMBaseSchema):
    """Shared sensor reading fields."""

    station_id: UUID
    recorded_at: datetime
    salinity_dsm: Decimal
    water_level_m: Decimal
    wind_speed_mps: Decimal | None = None
    wind_direction_deg: int | None = None
    flow_rate_m3s: Decimal | None = None
    temperature_c: Decimal | None = None
    battery_level_pct: Decimal | None = None
    source: str = Field(default="simulator", max_length=100)
    context_payload: dict[str, Any] | None = None


class SensorReadingCreate(SensorReadingBase):
    """Schema for creating a sensor reading."""


class SensorReadingRead(EntityReadSchema, SensorReadingBase):
    """Schema for returning a sensor reading."""

    salinity_gl: Decimal | None = None
    station: SensorStationSummary

    @model_validator(mode="after")
    def normalize_salinity_read_units(self) -> "SensorReadingRead":
        if self.salinity_gl is None:
            self.salinity_gl = dsm_to_gl(self.salinity_dsm)
        return self


class SensorReadingIngestRequest(ORMBaseSchema):
    """Payload for sensor reading ingestion."""

    station_code: str = Field(max_length=50)
    recorded_at: datetime
    salinity_dsm: Decimal | None = Field(default=None, gt=0)
    salinity_gl: Decimal | None = Field(default=None, gt=0)
    water_level_m: Decimal
    wind_speed_mps: Decimal | None = None
    wind_direction_deg: int | None = None
    flow_rate_m3s: Decimal | None = None
    temperature_c: Decimal | None = None
    battery_level_pct: Decimal | None = None
    source: str = Field(default="simulator", max_length=100)
    context_payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalize_salinity_input_units(self) -> "SensorReadingIngestRequest":
        if self.salinity_dsm is None and self.salinity_gl is None:
            raise ValueError("Either salinity_dsm or salinity_gl is required.")

        if self.salinity_dsm is None:
            self.salinity_dsm = gl_to_dsm(self.salinity_gl)

        if self.salinity_dsm is None:
            raise ValueError("Unable to normalize salinity_dsm from provided values.")

        if self.salinity_gl is None:
            self.salinity_gl = dsm_to_gl(self.salinity_dsm)
        elif not are_units_consistent(
            salinity_dsm=self.salinity_dsm,
            salinity_gl=self.salinity_gl,
        ):
            raise ValueError("salinity_dsm and salinity_gl are inconsistent.")

        return self


class SensorStationUpdate(ORMBaseSchema):
    """Partial station update request."""

    name: str | None = Field(default=None, max_length=255)
    station_type: str | None = Field(default=None, max_length=100)
    status: StationStatus | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_description: str | None = None
    station_metadata: dict[str, Any] | None = None


class SensorStationCollection(ORMBaseSchema):
    """Collection wrapper for station query responses."""

    items: list[SensorStationRead]
    count: int


class SensorReadingHistoryFilters(ORMBaseSchema):
    """Validated filter set for latest/history queries."""

    station_id: UUID | None = None
    station_code: str | None = None
    region_id: UUID | None = None
    region_code: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class SensorReadingCollection(ORMBaseSchema):
    """Collection wrapper for reading query responses."""

    items: list[SensorReadingRead]
    count: int
