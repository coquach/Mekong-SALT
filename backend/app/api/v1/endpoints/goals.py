"""Monitoring goals endpoints for CRUD and run-once execution."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.models.goal import MonitoringGoal
from app.schemas.action import ActionPlanRead
from app.schemas.agent import AgentPlanResponse
from app.schemas.common import SuccessResponse
from app.schemas.goal import (
    GoalRunOnceRequest,
    GoalRunOnceResponse,
    GoalThresholds,
    MonitoringGoalCollection,
    MonitoringGoalCreate,
    MonitoringGoalRead,
    MonitoringGoalUpdate,
)
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.goals_service import (
    create_monitoring_goal,
    delete_monitoring_goal,
    get_monitoring_goal,
    list_monitoring_goals,
    run_monitoring_goal_once,
    update_monitoring_goal,
)

router = APIRouter(prefix="/goals", tags=["goals"])


def _goal_to_read(goal: MonitoringGoal) -> MonitoringGoalRead:
    """Map ORM goal to API read payload."""
    return MonitoringGoalRead(
        id=goal.id,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        name=goal.name,
        description=goal.description,
        region_id=goal.region_id,
        station_id=goal.station_id,
        objective=goal.objective,
        provider=goal.provider,
        thresholds=GoalThresholds(
            warning_threshold_dsm=goal.warning_threshold_dsm,
            critical_threshold_dsm=goal.critical_threshold_dsm,
        ),
        evaluation_interval_minutes=goal.evaluation_interval_minutes,
        is_active=goal.is_active,
        last_run_at=goal.last_run_at,
        last_run_status=goal.last_run_status,
        last_run_plan_id=goal.last_run_plan_id,
    )


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
        data=_goal_to_read(goal),
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
            items=[_goal_to_read(goal) for goal in goals],
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
        data=_goal_to_read(goal),
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
        data=_goal_to_read(goal),
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
    response_payload = GoalRunOnceResponse(
        goal=_goal_to_read(bundle.goal),
        result=AgentPlanResponse(
            assessment=RiskAssessmentRead.model_validate(bundle.plan_bundle.risk_bundle.assessment),
            reading=SensorReadingRead.model_validate(bundle.plan_bundle.risk_bundle.reading),
            weather_snapshot=(
                WeatherSnapshotRead.model_validate(bundle.plan_bundle.risk_bundle.weather_snapshot)
                if bundle.plan_bundle.risk_bundle.weather_snapshot is not None
                else None
            ),
            plan=ActionPlanRead.model_validate(bundle.plan_bundle.plan),
        ),
    )
    return success_response(
        request=request,
        message="Goal run-once completed successfully.",
        data=response_payload,
    )
