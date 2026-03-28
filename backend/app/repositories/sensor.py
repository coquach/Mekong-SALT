"""Repositories for sensor station and reading persistence."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

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

    @staticmethod
    def _apply_filters(
        statement: Select,
        *,
        station_id: UUID | None = None,
        region_id: UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> Select:
        if region_id is not None:
            statement = statement.join(SensorStation)
            statement = statement.where(SensorStation.region_id == region_id)
        if station_id is not None:
            statement = statement.where(SensorReading.station_id == station_id)
        if start_at is not None:
            statement = statement.where(SensorReading.recorded_at >= start_at)
        if end_at is not None:
            statement = statement.where(SensorReading.recorded_at <= end_at)
        return statement

    async def get_with_station(self, reading_id: UUID) -> SensorReading | None:
        """Load a reading with station relationship populated."""
        result = await self.session.scalars(
            select(SensorReading)
            .options(selectinload(SensorReading.station))
            .where(SensorReading.id == reading_id)
        )
        return result.first()

    async def get_latest_for_station(self, station_id) -> SensorReading | None:
        """Return the newest reading for a station."""
        result = await self.session.scalars(
            select(SensorReading)
            .where(SensorReading.station_id == station_id)
            .order_by(desc(SensorReading.recorded_at))
            .options(selectinload(SensorReading.station))
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
            .options(selectinload(SensorReading.station))
            .limit(limit)
        )
        return result.all()

    async def list_history(
        self,
        *,
        station_id: UUID | None = None,
        region_id: UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[SensorReading]:
        """Return historical readings filtered by station, region, and time range."""
        statement = select(SensorReading).options(selectinload(SensorReading.station))
        statement = self._apply_filters(
            statement,
            station_id=station_id,
            region_id=region_id,
            start_at=start_at,
            end_at=end_at,
        )
        statement = statement.order_by(
            desc(SensorReading.recorded_at),
            desc(SensorReading.created_at),
        ).limit(limit)
        result = await self.session.scalars(statement)
        return result.all()

    async def list_latest(
        self,
        *,
        station_id: UUID | None = None,
        region_id: UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[SensorReading]:
        """Return the latest reading per station under the provided filters."""
        ranked_readings = self._apply_filters(
            select(
                SensorReading.id.label("reading_id"),
                func.row_number()
                .over(
                    partition_by=SensorReading.station_id,
                    order_by=(
                        desc(SensorReading.recorded_at),
                        desc(SensorReading.created_at),
                    ),
                )
                .label("row_num"),
            ),
            station_id=station_id,
            region_id=region_id,
            start_at=start_at,
            end_at=end_at,
        ).subquery()

        ranked_alias = aliased(SensorReading, name="ranked_sensor_reading")
        statement = (
            select(ranked_alias)
            .join(ranked_readings, ranked_alias.id == ranked_readings.c.reading_id)
            .where(ranked_readings.c.row_num == 1)
            .options(selectinload(ranked_alias.station))
            .order_by(desc(ranked_alias.recorded_at), ranked_alias.station_id)
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return result.all()
