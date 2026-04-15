"""Monitoring goals endpoints for CRUD and run-once execution."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.presenters.goals import goal_run_once_to_response, goal_to_read
from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.goal import (
    GoalRunOnceRequest,
    GoalRunOnceResponse,
    MonitoringGoalCollection,
    MonitoringGoalCreate,
    MonitoringGoalRead,
    MonitoringGoalUpdate,
)
from app.services.goals_service import (
    create_monitoring_goal,
    delete_monitoring_goal,
    get_monitoring_goal,
    list_monitoring_goals,
    run_monitoring_goal_once,
    update_monitoring_goal,
)

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=SuccessResponse[MonitoringGoalRead], status_code=201)
async def create_goal(
    payload: MonitoringGoalCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a monitoring goal."""
    goal = await create_monitoring_goal(session, payload)
    return success_response(
        request=request,
        message="Monitoring goal created successfully.",
        data=goal_to_read(goal),
        status_code=201,
    )


@router.get("", response_model=SuccessResponse[MonitoringGoalCollection])
async def list_goals(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    is_active: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """List monitoring goals."""
    goals = await list_monitoring_goals(session, limit=limit, is_active=is_active)
    return success_response(
        request=request,
        message="Monitoring goals retrieved successfully.",
        data=MonitoringGoalCollection(
            items=[goal_to_read(goal) for goal in goals],
            count=len(goals),
        ),
    )


@router.get("/{goal_id}", response_model=SuccessResponse[MonitoringGoalRead])
async def get_goal(
    goal_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get one monitoring goal."""
    goal = await get_monitoring_goal(session, goal_id)
    return success_response(
        request=request,
        message="Monitoring goal retrieved successfully.",
        data=goal_to_read(goal),
    )


@router.patch("/{goal_id}", response_model=SuccessResponse[MonitoringGoalRead])
async def update_goal(
    goal_id: UUID,
    payload: MonitoringGoalUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update a monitoring goal."""
    goal = await update_monitoring_goal(session, goal_id, payload)
    return success_response(
        request=request,
        message="Monitoring goal updated successfully.",
        data=goal_to_read(goal),
    )


@router.delete("/{goal_id}", response_model=SuccessResponse[dict[str, str]])
async def delete_goal(
    goal_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a monitoring goal."""
    await delete_monitoring_goal(session, goal_id)
    return success_response(
        request=request,
        message="Monitoring goal deleted successfully.",
        data={"goal_id": str(goal_id)},
    )


@router.post("/{goal_id}/run-once", response_model=SuccessResponse[GoalRunOnceResponse])
async def run_goal_once(
    goal_id: UUID,
    payload: GoalRunOnceRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Run one planning cycle immediately using persisted goal configuration."""
    bundle = await run_monitoring_goal_once(
        session,
        goal_id=goal_id,
        payload=payload,
        redis_manager=redis_manager,
    )
    return success_response(
        request=request,
        message="Goal run-once completed successfully.",
        data=goal_run_once_to_response(bundle),
    )
