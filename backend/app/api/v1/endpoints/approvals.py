"""Approval endpoints for human-in-the-loop plan decisions."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.core.config import get_settings
from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.models.enums import ApprovalDecision
from app.orchestration.lifecycle_graph import advance_plan_with_lifecycle_graph
from app.schemas.approval import ApprovalCollection, ApprovalDecisionResponse, ApprovalRequest
from app.schemas.common import SuccessResponse
from app.services.approval import decide_plan, list_plan_approvals
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post(
    "/plans/{plan_id}/decision",
    response_model=SuccessResponse[ApprovalDecisionResponse],
    summary="Approve or reject a pending plan",
)
async def approval_decision_endpoint(
    plan_id: UUID,
    payload: ApprovalRequest,
    request: Request,
    actor_name: str = Query(default="operator", min_length=1, max_length=255),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
    session: AsyncSession = Depends(get_db_session),
):
    """Apply a human decision to a pending plan."""
    approval, plan = await decide_plan(
        session,
        plan_id=plan_id,
        payload=payload,
        actor_name=actor_name,
    )

    message = "Plan decision recorded successfully."
    if payload.decision is ApprovalDecision.APPROVED:
        lifecycle_result = await advance_plan_with_lifecycle_graph(
            session,
            plan=plan,
            settings=get_settings(),
            redis_manager=redis_manager,
        )
        plan = lifecycle_result.plan
        if lifecycle_result.status == "executed":
            message = "Plan approved and executed successfully."
        elif lifecycle_result.status == "approved_not_executed":
            message = "Plan approved, but execution was skipped by policy."
        elif lifecycle_result.status == "awaiting_human_approval":
            message = "Plan approved, but it still requires human approval."
        else:
            message = "Plan approved and advanced through the lifecycle graph."

    return success_response(
        request=request,
        message=message,
        data=ApprovalDecisionResponse(
            approval=approval,
            plan=plan,
        ),
    )


@router.get(
    "/plans/{plan_id}/history",
    response_model=SuccessResponse[ApprovalCollection],
    summary="List approval decision history for a plan",
)
async def approval_history_endpoint(
    plan_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return approval records for a plan in descending decision time order."""
    approvals = await list_plan_approvals(session, plan_id)
    return success_response(
        request=request,
        message="Approval history retrieved successfully.",
        data=ApprovalCollection(
            items=approvals,
            count=len(approvals),
        ),
    )
