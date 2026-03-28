"""Repositories for sensor station and reading persistence."""

from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor import SensorReading, SensorStation
from app.repositories.base import AsyncRepository


class SensorStationRepository(AsyncRepository[SensorStation]):
    """Sensor station query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SensorStation)

    async def get_by_code(self, code: str) -> SensorStation | None:
        """Load a station by unique code."""
        result = await self.session.scalars(
            select(SensorStation).where(SensorStation.code == code)
        )
        return result.first()

    async def list_by_region(self, region_id) -> Sequence[SensorStation]:
        """List stations belonging to a region."""
        result = await self.session.scalars(
            select(SensorStation).where(SensorStation.region_id == region_id)
        )
        return result.all()


class SensorReadingRepository(AsyncRepository[SensorReading]):
    """Sensor reading query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SensorReading)

    async def get_latest_for_station(self, station_id) -> SensorReading | None:
        """Return the newest reading for a station."""
        result = await self.session.scalars(
            select(SensorReading)
            .where(SensorReading.station_id == station_id)
            .order_by(desc(SensorReading.recorded_at))
            .limit(1)
        )
        return result.first()

    async def list_history_for_station(
        self, station_id, *, limit: int = 100
    ) -> Sequence[SensorReading]:
        """Return recent history for a station."""
        result = await self.session.scalars(
            select(SensorReading)
            .where(SensorReading.station_id == station_id)
            .order_by(desc(SensorReading.recorded_at))
            .limit(limit)
        )
        return result.all()

