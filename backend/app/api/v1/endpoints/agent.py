"""Agent planning endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.schemas.action import ActionPlanRead
from app.schemas.agent import AgentPlanRequest, AgentPlanResponse
from app.schemas.common import SuccessResponse
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_planning_service import generate_agent_plan

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/plan",
    response_model=SuccessResponse[AgentPlanResponse],
    summary="Generate and validate an agent-assisted action plan",
)
async def generate_plan_endpoint(
    payload: AgentPlanRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Run the initial LangGraph planning workflow and persist the plan draft."""
    bundle = await generate_agent_plan(
        session,
        payload=payload,
        redis_manager=redis_manager,
    )
    response_payload = AgentPlanResponse(
        assessment=RiskAssessmentRead.model_validate(bundle.risk_bundle.assessment),
        reading=SensorReadingRead.model_validate(bundle.risk_bundle.reading),
        weather_snapshot=(
            WeatherSnapshotRead.model_validate(bundle.risk_bundle.weather_snapshot)
            if bundle.risk_bundle.weather_snapshot is not None
            else None
        ),
        plan=ActionPlanRead.model_validate(bundle.plan),
    )
    return success_response(
        request=request,
        message="Agent-assisted plan generated successfully.",
        data=response_payload,
    )
