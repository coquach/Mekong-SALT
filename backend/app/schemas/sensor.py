"""Schemas for sensor stations and readings."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

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
    temperature_c: Decimal | None = None
    battery_level_pct: Decimal | None = None
    context_payload: dict[str, Any] | None = None


class SensorReadingCreate(SensorReadingBase):
    """Schema for creating a sensor reading."""


class SensorReadingRead(EntityReadSchema, SensorReadingBase):
    """Schema for returning a sensor reading."""

    station: SensorStationSummary


class SensorReadingIngestRequest(ORMBaseSchema):
    """Payload for sensor reading ingestion."""

    station_code: str = Field(max_length=50)
    recorded_at: datetime
    salinity_dsm: Decimal
    water_level_m: Decimal
    temperature_c: Decimal | None = None
    battery_level_pct: Decimal | None = None
    context_payload: dict[str, Any] | None = None


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
