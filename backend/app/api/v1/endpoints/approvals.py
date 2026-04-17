"""Approval endpoints for human-in-the-loop plan decisions."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.core.responses import success_response
from app.db.session import get_db_session
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
    session: AsyncSession = Depends(get_db_session),
):
    """Apply a human decision to a pending plan."""
    approval, plan = await decide_plan(
        session,
        plan_id=plan_id,
        payload=payload,
        actor_name=actor_name,
    )
    return success_response(
        request=request,
        message="Plan decision recorded successfully.",
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
