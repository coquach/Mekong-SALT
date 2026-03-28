"""Repositories for action plan persistence."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.action import ActionExecution, ActionPlan
from app.repositories.base import AsyncRepository


class ActionPlanRepository(AsyncRepository[ActionPlan]):
    """Action plan query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ActionPlan)

    async def get_latest_for_assessment(self, risk_assessment_id: UUID) -> ActionPlan | None:
        """Return the latest action plan persisted for a risk assessment."""
        result = await self.session.scalars(
            select(ActionPlan)
            .where(ActionPlan.risk_assessment_id == risk_assessment_id)
            .order_by(desc(ActionPlan.created_at))
            .limit(1)
        )
        return result.first()

    async def get_with_assessment(self, plan_id: UUID) -> ActionPlan | None:
        """Return a plan with its assessment eagerly loaded."""
        result = await self.session.scalars(
            select(ActionPlan)
            .options(selectinload(ActionPlan.risk_assessment))
            .where(ActionPlan.id == plan_id)
        )
        return result.first()


class ActionExecutionRepository(AsyncRepository[ActionExecution]):
    """Action execution query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ActionExecution)

    async def list_for_logs(
        self,
        *,
        region_id: UUID | None = None,
        plan_id: UUID | None = None,
        limit: int = 50,
    ) -> list[ActionExecution]:
        """Return action executions for log views."""
        statement = select(ActionExecution).order_by(
            desc(ActionExecution.started_at),
            desc(ActionExecution.created_at),
        )
        if region_id is not None:
            statement = statement.where(ActionExecution.region_id == region_id)
        if plan_id is not None:
            statement = statement.where(ActionExecution.plan_id == plan_id)
        result = await self.session.scalars(statement.limit(limit))
        return list(result.all())
