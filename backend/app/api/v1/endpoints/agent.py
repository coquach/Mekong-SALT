"""Agent planning endpoints.

Legacy note:
These `/agent/*` routes are kept for backward compatibility while FE migrates
to the Phase 1 public facade under `/plans` and `/readings`.
The legacy `POST /agent/plan` route is retained for compatibility.
"""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.repositories.action import ActionPlanRepository
from app.repositories.agent_run import AgentRunRepository
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
from app.schemas.trace import AgentRunCollection, AgentRunRead, ObservationSnapshotRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_execution_service import execute_simulated_plan
from app.services.agent_planning_service import generate_agent_plan

router = APIRouter(prefix="/agent", tags=["agent"])


def _run_to_read_model(run) -> AgentRunRead:
    """Map ORM run record to API read schema."""
    return AgentRunRead(
        id=run.id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        run_type=run.run_type,
        trigger_source=run.trigger_source,
        status=run.status,
        payload=run.payload,
        trace=run.trace,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
        region_id=run.region_id,
        station_id=run.station_id,
        risk_assessment_id=run.risk_assessment_id,
        incident_id=run.incident_id,
        action_plan_id=run.action_plan_id,
        observation_snapshot=(
            ObservationSnapshotRead(
                id=run.observation_snapshot.id,
                created_at=run.observation_snapshot.created_at,
                updated_at=run.observation_snapshot.updated_at,
                agent_run_id=run.observation_snapshot.agent_run_id,
                captured_at=run.observation_snapshot.captured_at,
                source=run.observation_snapshot.source,
                region_id=run.observation_snapshot.region_id,
                station_id=run.observation_snapshot.station_id,
                reading_id=run.observation_snapshot.reading_id,
                weather_snapshot_id=run.observation_snapshot.weather_snapshot_id,
                payload=run.observation_snapshot.payload,
            )
            if run.observation_snapshot is not None
            else None
        ),
    )


@router.post(
    "/plan",
    response_model=SuccessResponse[AgentPlanResponse],
    summary="Generate a plan from current observations (legacy-compatible)",
)
async def generate_plan_endpoint(
    payload: AgentPlanRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Generate and persist an AI plan from the requested scope."""
    bundle = await generate_agent_plan(
        session,
        payload=payload,
        redis_manager=redis_manager,
        trigger_source="agent.plan.endpoint",
        trigger_payload={"endpoint": "/api/v1/agent/plan"},
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
        agent_run_id=bundle.run_id,
    )
    return success_response(
        request=request,
        message="Plan generated successfully.",
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


@router.get(
    "/runs",
    response_model=SuccessResponse[AgentRunCollection],
    summary="List recent run traces",
)
async def list_agent_runs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List recent agent runs with snapshot linkage."""
    runs = await AgentRunRepository(session).list_recent(limit=limit)
    items = [_run_to_read_model(run) for run in runs]
    return success_response(
        request=request,
        message="Agent runs retrieved successfully.",
        data=AgentRunCollection(items=items, count=len(items)),
    )


@router.get(
    "/runs/{run_id}",
    response_model=SuccessResponse[AgentRunRead],
    summary="Get one run trace",
)
async def get_agent_run(
    run_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get one run including observation snapshot and decision trace."""
    run = await AgentRunRepository(session).get_with_snapshot(run_id)
    if run is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="agent_run_not_found",
            message=f"Agent run '{run_id}' was not found.",
        )
    return success_response(
        request=request,
        message="Agent run retrieved successfully.",
        data=_run_to_read_model(run),
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
