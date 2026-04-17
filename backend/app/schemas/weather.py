"""Schemas for weather context."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import EntityReadSchema, ORMBaseSchema


class WeatherSnapshotBase(ORMBaseSchema):
    """Shared weather snapshot fields."""

    region_id: UUID
    observed_at: datetime
    wind_speed_mps: Decimal | None = None
    wind_direction_deg: int | None = Field(default=None, ge=0, le=360)
    tide_level_m: Decimal | None = None
    rainfall_mm: Decimal | None = None
    condition_summary: str | None = Field(default=None, max_length=255)
    source_payload: dict[str, Any] | None = None


class WeatherSnapshotCreate(WeatherSnapshotBase):
    """Schema for creating a weather snapshot."""


class WeatherSnapshotRead(EntityReadSchema, WeatherSnapshotBase):
    """Schema for returning a weather snapshot."""

