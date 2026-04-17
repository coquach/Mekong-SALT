"""Schemas for dashboard APIs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.base import ORMBaseSchema


class DashboardSummary(ORMBaseSchema):
    """Operational summary for the dashboard."""

    open_incidents: int
    pending_approvals: int
    active_notifications: int
    latest_risk_level: str | None = None
    latest_salinity_dsm: str | None = None
    latest_salinity_gl: str | None = None
    latest_station_code: str | None = None
    simulated_executions_today: int


class DashboardTimelineItem(ORMBaseSchema):
    """Compact timeline point used by FE charts."""

    assessed_at: datetime
    station_code: str | None = None
    risk_level: str
    salinity_dsm: str | None = None
    salinity_gl: str | None = None


class DashboardTimeline(ORMBaseSchema):
    """Timeline payload for dashboard trend visualizations."""

    items: list[DashboardTimelineItem]
    count: int


class DashboardEarthEngineLatest(ORMBaseSchema):
    """Latest persisted Earth Engine context captured during planning."""

    run_id: UUID | None = None
    captured_at: datetime | None = None
    region_id: UUID | None = None
    region_code: str | None = None
    station_id: UUID | None = None
    station_code: str | None = None
    source: str | None = None
    earth_engine_context: dict[str, Any] | None = None
