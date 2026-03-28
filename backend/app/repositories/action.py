"""Repositories for action plan persistence."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionPlan
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
