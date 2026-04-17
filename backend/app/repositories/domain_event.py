"""Repository helpers for durable domain event streams."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.repositories.base import AsyncRepository


class DomainEventRepository(AsyncRepository[DomainEvent]):
    """Append/read domain events for cursor-based consumers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DomainEvent)

    async def list_after_cursor(
        self,
        *,
        cursor: int,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Return events with id > cursor in ascending id order."""
        result = await self.session.scalars(
            select(DomainEvent)
            .where(DomainEvent.sequence > int(cursor))
            .order_by(DomainEvent.sequence.asc())
            .limit(limit)
        )
        return list(result.all())
