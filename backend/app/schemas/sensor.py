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

