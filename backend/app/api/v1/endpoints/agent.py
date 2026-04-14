"""Agent planning endpoints."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.repositories.action import ActionPlanRepository
from app.schemas.action import (
    ActionExecutionRead,
    ActionPlanRead,
    SimulatedExecutionRequest,
    SimulatedExecutionResponse,
)
from app.schemas.agent import AgentPlanRequest, AgentPlanResponse
from app.schemas.common import SuccessResponse
from app.schemas.decision import DecisionLogRead
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_execution_service import execute_simulated_plan
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


@router.get(
    "/plans",
    response_model=SuccessResponse[list[ActionPlanRead]],
    summary="List recent AI-generated plans",
)
async def list_plans_endpoint(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List recent plans for approval dashboards."""
    plans = await ActionPlanRepository(session).list_recent(limit=limit)
    return success_response(
        request=request,
        message="Plans retrieved successfully.",
        data=[ActionPlanRead.model_validate(plan) for plan in plans],
    )


@router.post(
    "/execute-simulated",
    response_model=SuccessResponse[SimulatedExecutionResponse],
    summary="Execute a validated plan using safe simulated actions only",
)
async def execute_simulated_plan_endpoint(
    payload: SimulatedExecutionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Execute a validated action plan in simulated mode and log the results."""
    bundle = await execute_simulated_plan(
        session,
        payload=payload,
        actor_name="operator",
    )
    response_payload = SimulatedExecutionResponse(
        plan=ActionPlanRead.model_validate(bundle.plan),
        executions=[
            ActionExecutionRead.model_validate(execution)
            for execution in bundle.executions
        ],
        feedback=bundle.feedback,
        decision_logs=[
            DecisionLogRead.model_validate(decision_log)
            for decision_log in bundle.decision_logs
        ],
        idempotent_replay=bundle.idempotent_replay,
    )
    return success_response(
        request=request,
        message="Simulated execution completed successfully.",
        data=response_payload,
    )
