"""Repositories for region persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.region import Region
from app.repositories.base import AsyncRepository


class RegionRepository(AsyncRepository[Region]):
    """Region-specific query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Region)

    async def get_by_code(self, code: str) -> Region | None:
        """Load a region by unique code."""
        result = await self.session.scalars(select(Region).where(Region.code == code))
        return result.first()

