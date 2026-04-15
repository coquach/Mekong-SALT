"""Repository helpers for monitoring goals."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.goal import MonitoringGoal
from app.repositories.base import AsyncRepository


class MonitoringGoalRepository(AsyncRepository[MonitoringGoal]):
    """Monitoring goal persistence and query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MonitoringGoal)

    async def get_with_relations(self, goal_id: UUID) -> MonitoringGoal | None:
        """Load a goal with station and region relationships preloaded."""
        result = await self.session.scalars(
            select(MonitoringGoal)
            .options(
                selectinload(MonitoringGoal.region),
                selectinload(MonitoringGoal.station),
            )
            .where(MonitoringGoal.id == goal_id)
        )
        return result.first()

    async def get_by_name(self, name: str) -> MonitoringGoal | None:
        """Load a goal by unique name."""
        result = await self.session.scalars(
            select(MonitoringGoal).where(MonitoringGoal.name == name)
        )
        return result.first()

    async def list_recent(
        self,
        *,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> Sequence[MonitoringGoal]:
        """List recent goals with optional active-state filtering."""
        statement = (
            select(MonitoringGoal)
            .options(
                selectinload(MonitoringGoal.region),
                selectinload(MonitoringGoal.station),
            )
            .order_by(MonitoringGoal.created_at.desc())
            .limit(limit)
        )
        if is_active is not None:
            statement = statement.where(MonitoringGoal.is_active == is_active)
        result = await self.session.scalars(statement)
        return result.all()

    async def list_active(self, *, limit: int = 100) -> Sequence[MonitoringGoal]:
        """List active goals for the monitoring worker."""
        result = await self.session.scalars(
            select(MonitoringGoal)
            .options(
                selectinload(MonitoringGoal.region),
                selectinload(MonitoringGoal.station),
            )
            .where(MonitoringGoal.is_active.is_(True))
            .order_by(MonitoringGoal.created_at.asc())
            .limit(limit)
        )
        return result.all()
