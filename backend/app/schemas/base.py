"""Shared schema primitives for domain entities."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBaseSchema(BaseModel):
    """Base schema configured for ORM model parsing."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class EntityReadSchema(ORMBaseSchema):
    """Common read fields for persisted entities."""

    id: UUID
    created_at: datetime
    updated_at: datetime

