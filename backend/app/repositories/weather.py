"""Repository helpers for weather snapshots."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import WeatherSnapshot
from app.repositories.base import AsyncRepository


class WeatherSnapshotRepository(AsyncRepository[WeatherSnapshot]):
    """Weather snapshot query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WeatherSnapshot)

    async def get_latest_for_region(self, region_id: UUID) -> WeatherSnapshot | None:
        """Return the latest weather snapshot for a region."""
        result = await self.session.scalars(
            select(WeatherSnapshot)
            .where(WeatherSnapshot.region_id == region_id)
            .order_by(desc(WeatherSnapshot.observed_at), desc(WeatherSnapshot.created_at))
            .limit(1)
        )
        return result.first()

    async def get_recent_for_region(
        self, region_id: UUID, *, freshness_minutes: int
    ) -> WeatherSnapshot | None:
        """Return a recent weather snapshot for a region if one exists."""
        cutoff = datetime.now(UTC) - timedelta(minutes=freshness_minutes)
        result = await self.session.scalars(
            select(WeatherSnapshot)
            .where(
                WeatherSnapshot.region_id == region_id,
                WeatherSnapshot.observed_at >= cutoff,
            )
            .order_by(desc(WeatherSnapshot.observed_at), desc(WeatherSnapshot.created_at))
            .limit(1)
        )
        return result.first()

    async def get_by_region_and_observed_at(
        self, region_id: UUID, observed_at: datetime
    ) -> WeatherSnapshot | None:
        """Find a normalized snapshot for the same region and observation time."""
        result = await self.session.scalars(
            select(WeatherSnapshot).where(
                WeatherSnapshot.region_id == region_id,
                WeatherSnapshot.observed_at == observed_at,
            )
        )
        return result.first()

