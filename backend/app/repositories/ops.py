"""Repositories for audit, notification, and outcomes."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ActionOutcome, AuditLog
from app.models.notification import Notification
from app.repositories.base import AsyncRepository


class AuditLogRepository(AsyncRepository[AuditLog]):
    """Audit log query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    async def list_recent(
        self,
        *,
        incident_id: UUID | None = None,
        plan_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Return recent audit events."""
        statement = select(AuditLog).order_by(desc(AuditLog.occurred_at), desc(AuditLog.created_at))
        if incident_id is not None:
            statement = statement.where(AuditLog.incident_id == incident_id)
        if plan_id is not None:
            statement = statement.where(AuditLog.action_plan_id == plan_id)
        result = await self.session.scalars(statement.limit(limit))
        return list(result.all())


class NotificationRepository(AsyncRepository[Notification]):
    """Notification query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def list_recent(self, *, limit: int = 100) -> list[Notification]:
        """Return recent notifications."""
        result = await self.session.scalars(
            select(Notification).order_by(desc(Notification.created_at)).limit(limit)
        )
        return list(result.all())


class ActionOutcomeRepository(AsyncRepository[ActionOutcome]):
    """Action outcome query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ActionOutcome)
