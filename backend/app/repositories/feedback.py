"""Repositories for feedback lifecycle persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feedback import FeedbackSnapshot, OutcomeEvaluation
from app.repositories.base import AsyncRepository


class FeedbackSnapshotRepository(AsyncRepository[FeedbackSnapshot]):
    """Feedback snapshot query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FeedbackSnapshot)

    async def list_for_batch(self, batch_id: UUID) -> list[FeedbackSnapshot]:
        """List snapshots captured for one execution batch."""
        result = await self.session.scalars(
            select(FeedbackSnapshot)
            .where(FeedbackSnapshot.batch_id == batch_id)
            .order_by(desc(FeedbackSnapshot.captured_at), desc(FeedbackSnapshot.created_at))
        )
        return list(result.all())


class OutcomeEvaluationRepository(AsyncRepository[OutcomeEvaluation]):
    """Outcome evaluation query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OutcomeEvaluation)

    async def get_latest_for_batch(self, batch_id: UUID) -> OutcomeEvaluation | None:
        """Return the latest evaluation record for one execution batch."""
        result = await self.session.scalars(
            select(OutcomeEvaluation)
            .options(
                selectinload(OutcomeEvaluation.before_snapshot),
                selectinload(OutcomeEvaluation.after_snapshot),
            )
            .where(OutcomeEvaluation.batch_id == batch_id)
            .order_by(desc(OutcomeEvaluation.evaluated_at), desc(OutcomeEvaluation.created_at))
            .limit(1)
        )
        return result.first()
