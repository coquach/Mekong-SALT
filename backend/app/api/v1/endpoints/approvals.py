"""Approval workflow endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.approval import ApprovalDecisionResponse, ApprovalRead, ApprovalRequest
from app.schemas.action import ActionPlanRead
from app.schemas.common import SuccessResponse
from app.services.approval_service import decide_plan

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/plans/{plan_id}", response_model=SuccessResponse[ApprovalDecisionResponse])
async def decide_plan_endpoint(
    plan_id: UUID,
    payload: ApprovalRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Approve or reject a pending AI plan."""
    approval, plan = await decide_plan(
        session,
        plan_id=plan_id,
        payload=payload,
        actor_name="supervisor",
    )
    return success_response(
        request=request,
        message=f"Plan {payload.decision.value} successfully.",
        data=ApprovalDecisionResponse(
            approval=ApprovalRead.model_validate(approval),
            plan=ActionPlanRead.model_validate(plan),
        ),
    )
