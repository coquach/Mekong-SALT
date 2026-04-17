"""Repositories for action plan persistence."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ActionPlanStatus
from app.models.action import ActionExecution, ActionPlan, ExecutionBatch
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
            .options(
                selectinload(ActionPlan.risk_assessment),
                selectinload(ActionPlan.incident),
            )
            .where(ActionPlan.id == plan_id)
        )
        return result.first()

    async def list_recent(self, *, limit: int = 100) -> list[ActionPlan]:
        """Return recent action plans."""
        result = await self.session.scalars(
            select(ActionPlan).order_by(desc(ActionPlan.created_at)).limit(limit)
        )
        return list(result.all())

    async def get_open_for_incident(self, incident_id: UUID) -> ActionPlan | None:
        """Return an existing plan that should suppress duplicate incident work."""
        active_statuses = {
            ActionPlanStatus.DRAFT,
            ActionPlanStatus.VALIDATED,
            ActionPlanStatus.PENDING_APPROVAL,
            ActionPlanStatus.APPROVED,
        }
        result = await self.session.scalars(
            select(ActionPlan)
            .where(
                ActionPlan.incident_id == incident_id,
                ActionPlan.status.in_(active_statuses),
            )
            .order_by(desc(ActionPlan.created_at))
            .limit(1)
        )
        return result.first()

    async def get_latest_for_incident(self, incident_id: UUID) -> ActionPlan | None:
        """Return the latest plan for one incident regardless of lifecycle state."""
        result = await self.session.scalars(
            select(ActionPlan)
            .where(ActionPlan.incident_id == incident_id)
            .order_by(desc(ActionPlan.created_at))
            .limit(1)
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
        batch_id: UUID | None = None,
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
        if batch_id is not None:
            statement = statement.where(ActionExecution.batch_id == batch_id)
        result = await self.session.scalars(statement.limit(limit))
        return list(result.all())

    async def list_for_batch(self, batch_id: UUID) -> list[ActionExecution]:
        """Return all executions belonging to one execution batch."""
        result = await self.session.scalars(
            select(ActionExecution)
            .where(ActionExecution.batch_id == batch_id)
            .order_by(ActionExecution.step_index, desc(ActionExecution.created_at))
        )
        return list(result.all())

    async def get_by_idempotency_key(self, key: str) -> ActionExecution | None:
        """Load an execution by idempotency key."""
        result = await self.session.scalars(
            select(ActionExecution).where(ActionExecution.idempotency_key == key)
        )
        return result.first()


class ExecutionBatchRepository(AsyncRepository[ExecutionBatch]):
    """Execution batch query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ExecutionBatch)

    async def get_with_executions(self, batch_id: UUID) -> ExecutionBatch | None:
        """Load one batch with executions eagerly loaded."""
        result = await self.session.scalars(
            select(ExecutionBatch)
            .options(selectinload(ExecutionBatch.executions))
            .where(ExecutionBatch.id == batch_id)
        )
        return result.first()

    async def list_recent(self, *, limit: int = 100) -> list[ExecutionBatch]:
        """Return recent execution batches with their executions loaded."""
        result = await self.session.scalars(
            select(ExecutionBatch)
            .options(selectinload(ExecutionBatch.executions))
            .order_by(desc(ExecutionBatch.started_at), desc(ExecutionBatch.created_at))
            .limit(limit)
        )
        return list(result.all())

    async def get_by_idempotency_key(self, key: str) -> ExecutionBatch | None:
        """Load an execution batch by idempotency key."""
        result = await self.session.scalars(
            select(ExecutionBatch).where(ExecutionBatch.idempotency_key == key)
        )
        return result.first()
