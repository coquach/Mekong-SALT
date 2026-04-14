"""Execution batch facade endpoints (Phase 1 compatibility layer)."""

from datetime import datetime
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.session import get_db_session
from app.models.action import ActionExecution
from app.models.enums import ExecutionStatus
from app.repositories.action import ActionExecutionRepository
from app.repositories.ops import ActionOutcomeRepository
from app.schemas.action import ActionExecutionRead
from app.schemas.audit import ActionOutcomeRead
from app.schemas.base import ORMBaseSchema
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["execution-batches"])


class ExecutionBatchRead(ORMBaseSchema):
    """Synthetic batch view built from current action executions."""

    id: str
    plan_id: UUID
    status: str
    requested_by: str | None = None
    idempotency_key: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    step_count: int


class ExecutionBatchCollection(ORMBaseSchema):
    """Collection payload for synthetic batch list."""

    items: list[ExecutionBatchRead]
    count: int


class ExecutionBatchDetail(ORMBaseSchema):
    """Detail payload for one synthetic batch."""

    batch: ExecutionBatchRead
    executions: list[ActionExecutionRead]
    count: int


class ActionOutcomeCollection(ORMBaseSchema):
    """Collection payload for action outcomes."""

    items: list[ActionOutcomeRead]
    count: int


def _batch_key(execution: ActionExecution) -> str:
    if execution.idempotency_key:
        return execution.idempotency_key.split(":", 1)[0]
    return str(execution.id)


def _derive_batch_status(executions: list[ActionExecution]) -> str:
    statuses = {item.status for item in executions}
    if ExecutionStatus.FAILED in statuses:
        return ExecutionStatus.FAILED.value
    if ExecutionStatus.CANCELLED in statuses:
        return ExecutionStatus.CANCELLED.value
    if ExecutionStatus.RUNNING in statuses:
        return ExecutionStatus.RUNNING.value
    if ExecutionStatus.SUCCEEDED in statuses:
        return ExecutionStatus.SUCCEEDED.value
    return ExecutionStatus.PENDING.value


def _to_batch_read(batch_id: str, executions: list[ActionExecution]) -> ExecutionBatchRead:
    first = executions[0]
    started_values = [item.started_at for item in executions if item.started_at is not None]
    completed_values = [item.completed_at for item in executions if item.completed_at is not None]
    return ExecutionBatchRead(
        id=batch_id,
        plan_id=first.plan_id,
        status=_derive_batch_status(executions),
        requested_by=first.requested_by,
        idempotency_key=first.idempotency_key,
        started_at=min(started_values) if started_values else None,
        completed_at=max(completed_values) if completed_values else None,
        step_count=len(executions),
    )


@router.get("/execution-batches", response_model=SuccessResponse[ExecutionBatchCollection])
async def list_execution_batches(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List synthetic execution batches until dedicated `execution_batches` table is added."""
    # Phase 1 note: this groups current per-step executions by idempotency key prefix.
    executions = await ActionExecutionRepository(session).list_for_logs(limit=limit)

    grouped: dict[str, list[ActionExecution]] = {}
    for execution in executions:
        key = _batch_key(execution)
        grouped.setdefault(key, []).append(execution)

    items = [
        _to_batch_read(batch_id, group)
        for batch_id, group in grouped.items()
    ]
    items.sort(key=lambda item: item.started_at or datetime.min, reverse=True)

    return success_response(
        request=request,
        message="Execution batches retrieved successfully.",
        data=ExecutionBatchCollection(items=items, count=len(items)),
    )


@router.get("/execution-batches/{batch_id}", response_model=SuccessResponse[ExecutionBatchDetail])
async def get_execution_batch(
    batch_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return one synthetic batch with all step executions."""
    statement = (
        select(ActionExecution)
        .where(
            or_(
                ActionExecution.idempotency_key == batch_id,
                ActionExecution.idempotency_key.like(f"{batch_id}:%"),
            )
        )
        .order_by(ActionExecution.step_index, desc(ActionExecution.created_at))
    )
    executions = list((await session.scalars(statement)).all())

    # Backward fallback: when no idempotency key is present, allow direct lookup by execution id.
    if not executions:
        try:
            execution_id = UUID(batch_id)
        except ValueError:
            execution_id = None
        if execution_id is not None:
            execution = await ActionExecutionRepository(session).get(execution_id)
            if execution is not None:
                executions = [execution]

    if not executions:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="execution_batch_not_found",
            message=f"Execution batch '{batch_id}' was not found.",
        )

    batch = _to_batch_read(batch_id, executions)
    return success_response(
        request=request,
        message="Execution batch retrieved successfully.",
        data=ExecutionBatchDetail(
            batch=batch,
            executions=[ActionExecutionRead.model_validate(item) for item in executions],
            count=len(executions),
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
