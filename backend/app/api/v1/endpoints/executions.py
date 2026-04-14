"""Execution endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.action import (
    ActionExecutionRead,
    ActionPlanRead,
    ExecutionSimulateRequest,
    SimulatedExecutionRequest,
    SimulatedExecutionResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.decision import DecisionLogRead
from app.services.agent_execution_service import execute_simulated_plan

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/plans/{plan_id}/simulate", response_model=SuccessResponse[SimulatedExecutionResponse])
async def execute_plan_endpoint(
    plan_id: UUID,
    payload: ExecutionSimulateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Execute a human-approved plan using mock devices/channels."""
    normalized_payload = SimulatedExecutionRequest(
        action_plan_id=plan_id,
        idempotency_key=payload.idempotency_key,
    )
    bundle = await execute_simulated_plan(
        session,
        payload=normalized_payload,
        actor_name="operator",
    )
    return success_response(
        request=request,
        message="Simulated execution completed successfully.",
        data=SimulatedExecutionResponse(
            plan=ActionPlanRead.model_validate(bundle.plan),
            executions=[ActionExecutionRead.model_validate(item) for item in bundle.executions],
            feedback=bundle.feedback,
            decision_logs=[DecisionLogRead.model_validate(item) for item in bundle.decision_logs],
            idempotent_replay=bundle.idempotent_replay,
        ),
    )
