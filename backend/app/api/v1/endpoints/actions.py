"""Action log endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.action import ActionLogCollection
from app.schemas.common import SuccessResponse
from app.services.execution import list_action_logs

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get(
    "/logs",
    response_model=SuccessResponse[ActionLogCollection],
    summary="List simulated action execution logs",
)
async def get_action_logs(
    request: Request,
    plan_id: UUID | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
):
    """Return simulated execution logs with their latest linked decision entry."""
    payload = await list_action_logs(
        session,
        plan_id=plan_id,
        region_id=region_id,
        region_code=region_code,
        limit=limit,
    )
    return success_response(
        request=request,
        message="Action logs retrieved successfully.",
        data=payload,
    )
