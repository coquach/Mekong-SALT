"""Repositories for gate persistence."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gate import Gate
from app.repositories.base import AsyncRepository


class GateRepository(AsyncRepository[Gate]):
    """Gate query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Gate)

    async def get_by_code(self, code: str) -> Gate | None:
        """Load a gate by unique code."""
        result = await self.session.scalars(
            select(Gate)
            .options(selectinload(Gate.station))
            .where(Gate.code == code)
        )
        return result.first()

    async def get_with_station(self, gate_id: UUID) -> Gate | None:
        """Load a gate and its linked station."""
        result = await self.session.scalars(
            select(Gate)
            .options(selectinload(Gate.station))
            .where(Gate.id == gate_id)
        )
        return result.first()

    async def list_all(self, *, limit: int = 100) -> Sequence[Gate]:
        """List gates in deterministic code order."""
        result = await self.session.scalars(
            select(Gate)
            .options(selectinload(Gate.station))
            .order_by(Gate.code)
            .limit(limit)
        )
        return result.all()

    async def list_by_region(self, region_id: UUID, *, limit: int = 100) -> Sequence[Gate]:
        """List gates belonging to a region."""
        result = await self.session.scalars(
            select(Gate)
            .options(selectinload(Gate.station))
            .where(Gate.region_id == region_id)
            .order_by(Gate.code)
            .limit(limit)
        )
        return result.all()

    async def get_preferred_for_station(self, station_id: UUID) -> Gate | None:
        """Load the first gate linked to a station."""
        result = await self.session.scalars(
            select(Gate)
            .options(selectinload(Gate.station))
            .where(Gate.station_id == station_id)
            .order_by(Gate.code)
        )
        return result.first()
