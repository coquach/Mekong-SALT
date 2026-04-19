"""Plan read endpoints."""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.session import get_db_session
from app.repositories.action import ActionPlanRepository
from app.schemas.action import ActionPlanRead
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=SuccessResponse[list[ActionPlanRead]])
async def list_plans(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List recent plans under canonical `/plans` namespace."""
    plans = await ActionPlanRepository(session).list_recent(limit=limit)
    return success_response(
        request=request,
        message="Plans retrieved successfully.",
        data=[ActionPlanRead.model_validate(plan) for plan in plans],
    )


@router.get("/{plan_id}", response_model=SuccessResponse[ActionPlanRead])
async def get_plan(
    plan_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return one plan detail by ID."""
    plan = await ActionPlanRepository(session).get_with_assessment(plan_id)
    if plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{plan_id}' was not found.",
        )
    return success_response(
        request=request,
        message="Plan retrieved successfully.",
        data=ActionPlanRead.model_validate(plan),
    )
