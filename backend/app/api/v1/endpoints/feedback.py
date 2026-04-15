"""Feedback API contract placeholders.

These endpoints intentionally return 501 while preserving an explicit OpenAPI
contract for post-execution evaluation workflows.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.core.responses import success_response
from app.schemas.base import ORMBaseSchema
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackContractPlaceholder(ORMBaseSchema):
    """Contract metadata returned by placeholder feedback endpoints."""

    area: str = "feedback"
    owner: str = "app.services.feedback (planned)"
    status: str = "placeholder"
    endpoint: str
    expected_behavior: str
    next_step: str = "Implement dedicated feedback service + outcome taxonomy mapping."


@router.post(
    "/execution-batches/{batch_id}/evaluate",
    response_model=SuccessResponse[FeedbackContractPlaceholder],
    summary="Feedback evaluation contract placeholder",
)
async def feedback_evaluate_contract(
    batch_id: UUID,
    request: Request,
):
    """Expose the future feedback evaluation API contract without side effects."""
    return success_response(
        request=request,
        status_code=501,
        message="Feedback evaluation API contract placeholder.",
        data=FeedbackContractPlaceholder(
            endpoint=f"/api/v1/feedback/execution-batches/{batch_id}/evaluate",
            expected_behavior=(
                "Compare pre/post snapshots and classify execution outcome for "
                "re-planning decisions."
            ),
        ),
    )


@router.get(
    "/execution-batches/{batch_id}/latest",
    response_model=SuccessResponse[FeedbackContractPlaceholder],
    summary="Feedback read contract placeholder",
)
async def feedback_latest_contract(
    batch_id: UUID,
    request: Request,
):
    """Expose the future feedback read API contract without side effects."""
    return success_response(
        request=request,
        status_code=501,
        message="Feedback read API contract placeholder.",
        data=FeedbackContractPlaceholder(
            endpoint=f"/api/v1/feedback/execution-batches/{batch_id}/latest",
            expected_behavior="Return latest feedback evaluation result for one execution batch.",
        ),
    )
