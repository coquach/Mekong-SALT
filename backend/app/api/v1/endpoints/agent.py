"""Agent planning endpoints.

Legacy note:
These `/agent/*` routes are kept for backward compatibility while FE migrates
to the Phase 1 public facade under `/plans` and `/readings`.
The old `POST /agent/plan` creation route has been removed.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.repositories.action import ActionPlanRepository
from app.schemas.action import (
    ActionExecutionRead,
    ActionPlanRead,
    SimulatedExecutionRequest,
    SimulatedExecutionResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.decision import DecisionLogRead
from app.services.agent_execution_service import execute_simulated_plan

router = APIRouter(prefix="/agent", tags=["agent"])


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
