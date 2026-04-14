"""Internal goals endpoints (Phase 1 bootstrap)."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.schemas.action import ActionPlanRead
from app.schemas.agent import AgentPlanRequest, AgentPlanResponse
from app.schemas.base import ORMBaseSchema
from app.schemas.common import SuccessResponse
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_planning_service import generate_agent_plan

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalRunOnceRequest(ORMBaseSchema):
    """Internal request to run one planning cycle for a goal."""

    station_id: UUID | None = None
    station_code: str | None = None
    region_id: UUID | None = None
    region_code: str | None = None
    incident_id: UUID | None = None
    objective: str | None = None
    provider: Literal["mock", "gemini", "ollama"] | None = None


class GoalRunOnceResponse(ORMBaseSchema):
    """Response payload for internal one-shot goal execution."""

    goal_id: str
    result: AgentPlanResponse


@router.post("/{goal_id}/run-once", response_model=SuccessResponse[GoalRunOnceResponse])
async def run_goal_once(
    goal_id: str,
    payload: GoalRunOnceRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Run one planning cycle for demo/testing before monitoring goals model exists."""
    # Phase 1 bridge: goal_id is accepted as a stable API contract, but not persisted yet.
    bundle = await generate_agent_plan(
        session,
        payload=AgentPlanRequest(
            station_id=payload.station_id,
            station_code=payload.station_code,
            region_id=payload.region_id,
            region_code=payload.region_code,
            incident_id=payload.incident_id,
            objective=payload.objective,
            provider=payload.provider,
        ),
        redis_manager=redis_manager,
    )
    response_payload = GoalRunOnceResponse(
        goal_id=goal_id,
        result=AgentPlanResponse(
            assessment=RiskAssessmentRead.model_validate(bundle.risk_bundle.assessment),
            reading=SensorReadingRead.model_validate(bundle.risk_bundle.reading),
            weather_snapshot=(
                WeatherSnapshotRead.model_validate(bundle.risk_bundle.weather_snapshot)
                if bundle.risk_bundle.weather_snapshot is not None
                else None
            ),
            plan=ActionPlanRead.model_validate(bundle.plan),
        ),
    )
    return success_response(
        request=request,
        message="Goal run-once completed successfully.",
        data=response_payload,
    )
