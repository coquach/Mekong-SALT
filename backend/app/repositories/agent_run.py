"""Repository helpers for agent runs and observation snapshots."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_run import AgentRun, ObservationSnapshot
from app.repositories.base import AsyncRepository


class AgentRunRepository(AsyncRepository[AgentRun]):
    """Persistence helpers for run trace records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AgentRun)

    async def get_with_snapshot(self, run_id: UUID) -> AgentRun | None:
        """Load one run with linked snapshot and decision entities."""
        result = await self.session.scalars(
            select(AgentRun)
            .options(
                selectinload(AgentRun.observation_snapshot),
                selectinload(AgentRun.risk_assessment),
                selectinload(AgentRun.incident),
                selectinload(AgentRun.action_plan),
            )
            .where(AgentRun.id == run_id)
        )
        return result.first()

    async def list_recent(self, *, limit: int = 100) -> Sequence[AgentRun]:
        """List latest runs first."""
        result = await self.session.scalars(
            select(AgentRun)
            .options(selectinload(AgentRun.observation_snapshot))
            .order_by(AgentRun.started_at.desc())
            .limit(limit)
        )
        return result.all()


class ObservationSnapshotRepository(AsyncRepository[ObservationSnapshot]):
    """Persistence helpers for observation snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ObservationSnapshot)

    async def get_by_run_id(self, run_id: UUID) -> ObservationSnapshot | None:
        """Load snapshot linked to a specific run."""
        result = await self.session.scalars(
            select(ObservationSnapshot).where(ObservationSnapshot.agent_run_id == run_id)
        )
        return result.first()
