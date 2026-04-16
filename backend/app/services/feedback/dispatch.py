"""Feedback notification dispatch adapters."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.action import FeedbackEvaluation
from app.services.notify import create_execution_summary_notifications


async def dispatch_feedback_notifications(
    session: AsyncSession,
    *,
    incident_id: UUID | None,
    action_plan_id: UUID,
    execution_id: UUID | None,
    execution_count: int,
    feedback: FeedbackEvaluation,
) -> None:
    """Dispatch feedback lifecycle notifications via pluggable notifier boundary."""
    await create_execution_summary_notifications(
        session,
        incident_id=incident_id,
        execution_id=execution_id,
        action_plan_id=action_plan_id,
        outcome_class=feedback.outcome_class,
        summary=feedback.summary,
        execution_count=execution_count,
        replan_recommended=feedback.replan_recommended,
    )
