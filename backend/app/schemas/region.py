"""Schemas for regions."""

from typing import Any

from pydantic import Field

from app.schemas.base import EntityReadSchema, ORMBaseSchema


class RegionBase(ORMBaseSchema):
    """Shared region fields."""

    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    province: str = Field(max_length=255)
    country: str = Field(default="Vietnam", max_length=100)
    description: str | None = None
    crop_profile: dict[str, Any] | None = None
    is_active: bool = True


class RegionCreate(RegionBase):
    """Schema for creating a region."""


class RegionRead(EntityReadSchema, RegionBase):
    """Schema for returning region records."""

