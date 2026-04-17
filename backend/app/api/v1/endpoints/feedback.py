"""Feedback lifecycle endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.feedback import FeedbackLifecycleRead, FeedbackSnapshotRead, OutcomeEvaluationRead
from app.services.feedback import evaluate_execution_batch_feedback, get_latest_batch_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _to_feedback_lifecycle_read(bundle) -> FeedbackLifecycleRead:
    return FeedbackLifecycleRead(
        evaluation=OutcomeEvaluationRead.model_validate(bundle.evaluation),
        before_snapshot=(
            FeedbackSnapshotRead.model_validate(bundle.before_snapshot)
            if bundle.before_snapshot is not None
            else None
        ),
        after_snapshot=(
            FeedbackSnapshotRead.model_validate(bundle.after_snapshot)
            if bundle.after_snapshot is not None
            else None
        ),
        feedback=bundle.feedback,
    )


@router.post(
    "/execution-batches/{batch_id}/evaluate",
    response_model=SuccessResponse[FeedbackLifecycleRead],
    summary="Persist feedback lifecycle evaluation",
)
async def feedback_evaluate(
    batch_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Persist before/after snapshots and one outcome evaluation for a batch."""
    bundle = await evaluate_execution_batch_feedback(
        session,
        batch_id=batch_id,
        evaluator_name="feedback-api",
    )
    await session.commit()

    return success_response(
        request=request,
        message="Feedback lifecycle evaluation persisted successfully.",
        data=_to_feedback_lifecycle_read(bundle),
    )


@router.get(
    "/execution-batches/{batch_id}/latest",
    response_model=SuccessResponse[FeedbackLifecycleRead],
    summary="Get latest persisted feedback lifecycle evaluation",
)
async def feedback_latest(
    batch_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return latest persisted feedback snapshots and evaluation for a batch."""
    bundle = await get_latest_batch_feedback(session, batch_id=batch_id)
    return success_response(
        request=request,
        message="Latest feedback lifecycle evaluation retrieved successfully.",
        data=_to_feedback_lifecycle_read(bundle),
    )
