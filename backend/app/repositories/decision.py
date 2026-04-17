"""Repositories for decision log persistence."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision import DecisionLog
from app.repositories.base import AsyncRepository


class DecisionLogRepository(AsyncRepository[DecisionLog]):
    """Decision log query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DecisionLog)

    async def list_for_execution_ids(
        self,
        execution_ids: list[UUID],
    ) -> list[DecisionLog]:
        """Return decision logs linked to the given executions."""
        if not execution_ids:
            return []
        result = await self.session.scalars(
            select(DecisionLog)
            .where(DecisionLog.action_execution_id.in_(execution_ids))
            .order_by(desc(DecisionLog.logged_at), desc(DecisionLog.created_at))
        )
        return list(result.all())
