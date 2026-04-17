"""Repositories for risk assessments and alerts."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import AlertStatus, RiskLevel
from app.models.risk import AlertEvent, RiskAssessment
from app.models.region import Region
from app.models.sensor import SensorReading, SensorStation
from app.repositories.base import AsyncRepository


class RiskAssessmentRepository(AsyncRepository[RiskAssessment]):
    """Risk assessment query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RiskAssessment)

    async def get_latest_for_station(self, station_id: UUID) -> RiskAssessment | None:
        """Return the latest persisted assessment for a station."""
        result = await self.session.scalars(
            select(RiskAssessment)
            .where(RiskAssessment.station_id == station_id)
            .order_by(desc(RiskAssessment.assessed_at), desc(RiskAssessment.created_at))
            .limit(1)
        )
        return result.first()

    async def get_latest(
        self,
        *,
        station_id: UUID | None = None,
        station_code: str | None = None,
        region_id: UUID | None = None,
        region_code: str | None = None,
    ) -> RiskAssessment | None:
        """Return the latest persisted assessment for the requested scope."""
        statement = (
            select(RiskAssessment)
            .options(
                selectinload(RiskAssessment.reading).selectinload(SensorReading.station),
                selectinload(RiskAssessment.station),
                selectinload(RiskAssessment.weather_snapshot),
            )
            .order_by(desc(RiskAssessment.assessed_at), desc(RiskAssessment.created_at))
            .limit(1)
        )
        if station_id is not None:
            statement = statement.where(RiskAssessment.station_id == station_id)
        if region_id is not None:
            statement = statement.where(RiskAssessment.region_id == region_id)
        if station_code is not None:
            statement = statement.join(SensorStation, RiskAssessment.station_id == SensorStation.id).where(
                SensorStation.code == station_code
            )
        if region_code is not None:
            statement = statement.join(Region, RiskAssessment.region_id == Region.id).where(
                Region.code == region_code
            )
        result = await self.session.scalars(statement)
        return result.first()


class AlertEventRepository(AsyncRepository[AlertEvent]):
    """Alert event query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlertEvent)

    async def get_open_by_region_and_severity(
        self, region_id: UUID, severity: RiskLevel
    ) -> AlertEvent | None:
        """Return an existing open alert for the same region and severity."""
        result = await self.session.scalars(
            select(AlertEvent)
            .where(
                AlertEvent.region_id == region_id,
                AlertEvent.severity == severity,
                AlertEvent.status == AlertStatus.OPEN,
            )
            .order_by(desc(AlertEvent.triggered_at), desc(AlertEvent.created_at))
            .limit(1)
        )
        return result.first()
