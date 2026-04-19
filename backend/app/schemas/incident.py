"""Schemas for incident management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import IncidentStatus, RiskLevel
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class IncidentBase(ORMBaseSchema):
    """Shared incident fields."""

    region_id: UUID
    station_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    title: str = Field(max_length=255)
    description: str
    severity: RiskLevel
    status: IncidentStatus = IncidentStatus.OPEN
    source: str = Field(default="risk_engine", max_length=100)
    evidence: dict[str, Any] | None = None
    opened_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    created_by: str | None = Field(default=None, max_length=255)


class IncidentCreate(ORMBaseSchema):
    """Manual incident creation request."""

    region_id: UUID
    station_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    title: str = Field(max_length=255)
    description: str
    severity: RiskLevel
    source: str = Field(default="manual", max_length=100)
    evidence: dict[str, Any] | None = None


class IncidentUpdate(ORMBaseSchema):
    """Incident lifecycle update request."""

    status: IncidentStatus
    note: str | None = None


class IncidentRead(EntityReadSchema, IncidentBase):
    """Incident response payload."""


class IncidentCollection(ORMBaseSchema):
    """Paginated incident list."""

    items: list[IncidentRead]
    count: int

