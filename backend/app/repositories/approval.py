"""Repositories for plan approval workflow."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.repositories.base import AsyncRepository


class ApprovalRepository(AsyncRepository[Approval]):
    """Approval query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Approval)

    async def list_for_plan(self, plan_id: UUID) -> list[Approval]:
        """Return approval decisions for a plan."""
        result = await self.session.scalars(
            select(Approval)
            .where(Approval.plan_id == plan_id)
            .order_by(desc(Approval.decided_at), desc(Approval.created_at))
        )
        return list(result.all())

