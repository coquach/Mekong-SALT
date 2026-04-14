"""Schemas for dashboard APIs."""

from app.schemas.base import ORMBaseSchema


class DashboardSummary(ORMBaseSchema):
    """Operational summary for the dashboard."""

    open_incidents: int
    pending_approvals: int
    active_notifications: int
    latest_risk_level: str | None = None
    latest_salinity_dsm: str | None = None
    latest_station_code: str | None = None
    simulated_executions_today: int
