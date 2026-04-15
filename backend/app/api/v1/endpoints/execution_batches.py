"""Execution batch endpoints."""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.session import get_db_session
from app.models.action import ActionExecution, ExecutionBatch
from app.repositories.action import ExecutionBatchRepository
from app.repositories.ops import ActionOutcomeRepository
from app.schemas.action import (
    ActionExecutionRead,
    ExecutionBatchCollection,
    ExecutionBatchDetail,
    ExecutionBatchRead,
    ExecutionSimulateRequest,
    SimulatedExecutionBatchResponse,
    SimulatedExecutionRequest,
)
from app.schemas.audit import ActionOutcomeRead
from app.schemas.base import ORMBaseSchema
from app.schemas.common import SuccessResponse
from app.schemas.decision import DecisionLogRead
from app.services.agent_execution_service import execute_simulated_plan

router = APIRouter(tags=["execution-batches"])


class ActionOutcomeCollection(ORMBaseSchema):
    """Collection payload for action outcomes."""

    items: list[ActionOutcomeRead]
    count: int


def _to_batch_read(batch: ExecutionBatch, executions: list[ActionExecution]) -> ExecutionBatchRead:
    started_values = [item.started_at for item in executions if item.started_at is not None]
    completed_values = [item.completed_at for item in executions if item.completed_at is not None]
    return ExecutionBatchRead(
        id=str(batch.id),
        plan_id=batch.plan_id,
        region_id=batch.region_id,
        status=batch.status.value,
        simulated=batch.simulated,
        requested_by=batch.requested_by,
        idempotency_key=batch.idempotency_key,
        started_at=batch.started_at or (min(started_values) if started_values else None),
        completed_at=batch.completed_at or (max(completed_values) if completed_values else None),
        step_count=len(executions),
    )


@router.get("/execution-batches", response_model=SuccessResponse[ExecutionBatchCollection])
async def list_execution_batches(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List persisted execution batches as full transaction records."""
    batches = await ExecutionBatchRepository(session).list_recent(limit=limit)
    items = [_to_batch_read(batch, list(batch.executions)) for batch in batches]

    return success_response(
        request=request,
        message="Execution batches retrieved successfully.",
        data=ExecutionBatchCollection(items=items, count=len(items)),
    )


@router.get("/execution-batches/{batch_id}", response_model=SuccessResponse[ExecutionBatchDetail])
async def get_execution_batch(
    batch_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return one batch with all step executions."""
    batch = await ExecutionBatchRepository(session).get_with_executions(batch_id)
    if batch is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="execution_batch_not_found",
            message=f"Execution batch '{batch_id}' was not found.",
        )

    executions = sorted(
        list(batch.executions),
        key=lambda item: (item.step_index, item.created_at),
    )
    return success_response(
        request=request,
        message="Execution batch retrieved successfully.",
        data=ExecutionBatchDetail(
            batch=_to_batch_read(batch, executions),
            executions=[ActionExecutionRead.model_validate(item) for item in executions],
            count=len(executions),
        ),
    )


@router.post(
    "/execution-batches/plans/{plan_id}/simulate",
    response_model=SuccessResponse[SimulatedExecutionBatchResponse],
)
async def execute_plan_as_batch(
    plan_id: UUID,
    payload: ExecutionSimulateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Execute one approved plan as a batch transaction."""
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
        message="Execution batch completed successfully.",
        data=SimulatedExecutionBatchResponse(
            batch=_to_batch_read(bundle.batch, bundle.executions),
            executions=[ActionExecutionRead.model_validate(item) for item in bundle.executions],
            feedback=bundle.feedback,
            decision_logs=[DecisionLogRead.model_validate(item) for item in bundle.decision_logs],
            idempotent_replay=bundle.idempotent_replay,
        ),
    )


@router.get("/action-outcomes", response_model=SuccessResponse[ActionOutcomeCollection])
async def list_action_outcomes(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List action outcomes for FE post-execution reporting cards."""
    outcomes = await ActionOutcomeRepository(session).list_recent(limit=limit)
    return success_response(
        request=request,
        message="Action outcomes retrieved successfully.",
        data=ActionOutcomeCollection(
            items=[ActionOutcomeRead.model_validate(item) for item in outcomes],
            count=len(outcomes),
        ),
    )
