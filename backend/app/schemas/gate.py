"""Schemas for operational gates."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import GateStatus
from app.schemas.base import EntityReadSchema, ORMBaseSchema
from app.schemas.sensor import SensorStationSummary


class GateBase(ORMBaseSchema):
    """Shared gate fields."""

    region_id: UUID
    station_id: UUID | None = None
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    gate_type: str = Field(default="sluice", max_length=100)
    status: GateStatus = GateStatus.CLOSED
    latitude: Decimal
    longitude: Decimal
    location_description: str | None = None
    last_operated_at: datetime | None = None
    gate_metadata: dict[str, Any] | None = None


class GateCreate(GateBase):
    """Schema for creating a gate."""


class GateUpdate(ORMBaseSchema):
    """Partial gate update request."""

    station_id: UUID | None = None
    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    gate_type: str | None = Field(default=None, max_length=100)
    status: GateStatus | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_description: str | None = None
    last_operated_at: datetime | None = None
    gate_metadata: dict[str, Any] | None = None


class GateRead(EntityReadSchema, GateBase):
    """Schema for returning a gate."""

    station: SensorStationSummary | None = None


class GateCollection(ORMBaseSchema):
    """Collection wrapper for gate query responses."""

    items: list[GateRead]
    count: int
