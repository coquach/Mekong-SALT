"""FE-facing plan endpoints plus internal regenerate bridge (Phase 1)."""

from http import HTTPStatus
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.models.enums import ApprovalDecision
from app.repositories.action import ActionPlanRepository
from app.schemas.action import (
    ActionExecutionRead,
    ActionPlanRead,
    ExecutionSimulateRequest,
    SimulatedExecutionRequest,
    SimulatedExecutionResponse,
)
from app.schemas.agent import AgentPlanRequest, AgentPlanResponse
from app.schemas.approval import ApprovalDecisionResponse, ApprovalRead, ApprovalRequest
from app.schemas.base import ORMBaseSchema
from app.schemas.common import SuccessResponse
from app.schemas.decision import DecisionLogRead
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_execution_service import execute_simulated_plan
from app.services.agent_planning_service import generate_agent_plan
from app.services.approval_service import decide_plan

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanDecisionNoteRequest(ORMBaseSchema):
    """Optional comment payload for approve/reject endpoints."""

    comment: str | None = None


class PlanRegenerateRequest(ORMBaseSchema):
    """Internal regenerate request options."""

    provider: Literal["mock", "gemini", "ollama"] | None = None


@router.get("", response_model=SuccessResponse[list[ActionPlanRead]])
async def list_plans(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List recent plans under FE-friendly `/plans` namespace."""
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


@router.post("/{plan_id}/approve", response_model=SuccessResponse[ApprovalDecisionResponse])
async def approve_plan(
    plan_id: UUID,
    payload: PlanDecisionNoteRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Approve a pending plan under FE-facing path semantics."""
    # Phase 1 bridge: map FE approve endpoint to the existing approval service.
    approval, plan = await decide_plan(
        session,
        plan_id=plan_id,
        payload=ApprovalRequest(decision=ApprovalDecision.APPROVED, comment=payload.comment),
        actor_name="supervisor",
    )
    return success_response(
        request=request,
        message="Plan approved successfully.",
        data=ApprovalDecisionResponse(
            approval=ApprovalRead.model_validate(approval),
            plan=ActionPlanRead.model_validate(plan),
        ),
    )


@router.post("/{plan_id}/reject", response_model=SuccessResponse[ApprovalDecisionResponse])
async def reject_plan(
    plan_id: UUID,
    payload: PlanDecisionNoteRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Reject a pending plan under FE-facing path semantics."""
    approval, plan = await decide_plan(
        session,
        plan_id=plan_id,
        payload=ApprovalRequest(decision=ApprovalDecision.REJECTED, comment=payload.comment),
        actor_name="supervisor",
    )
    return success_response(
        request=request,
        message="Plan rejected successfully.",
        data=ApprovalDecisionResponse(
            approval=ApprovalRead.model_validate(approval),
            plan=ActionPlanRead.model_validate(plan),
        ),
    )


@router.post("/{plan_id}/execute-simulated", response_model=SuccessResponse[SimulatedExecutionResponse])
async def execute_plan_simulated(
    plan_id: UUID,
    payload: ExecutionSimulateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Execute an approved plan in simulated mode under FE-facing path semantics."""
    bundle = await execute_simulated_plan(
        session,
        payload=SimulatedExecutionRequest(
            action_plan_id=plan_id,
            idempotency_key=payload.idempotency_key,
        ),
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


@router.post("/{plan_id}/regenerate", response_model=SuccessResponse[AgentPlanResponse])
async def regenerate_plan(
    plan_id: UUID,
    payload: PlanRegenerateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Internal endpoint to regenerate a plan from an existing plan context."""
    existing_plan = await ActionPlanRepository(session).get_with_assessment(plan_id)
    if existing_plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{plan_id}' was not found.",
        )

    # We keep regenerate minimal in Phase 1 by reusing known context from the existing plan.
    regen_payload = AgentPlanRequest(
        station_id=existing_plan.risk_assessment.station_id if existing_plan.risk_assessment is not None else None,
        region_id=existing_plan.region_id,
        incident_id=existing_plan.incident_id,
        objective=existing_plan.objective,
        provider=payload.provider,
    )
    bundle = await generate_agent_plan(
        session,
        payload=regen_payload,
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
        message="Plan regenerated successfully.",
        data=response_payload,
    )
