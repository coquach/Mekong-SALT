"""Simulated execution and feedback services."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution_policy import validate_execution_plan
from app.core.exceptions import AppException
from app.models.action import ActionExecution, ActionPlan, ExecutionBatch
from app.models.audit import ActionOutcome
from app.models.decision import DecisionLog
from app.models.enums import ActionPlanStatus, ActionType, AuditEventType, ExecutionStatus, IncidentStatus
from app.repositories.action import ActionExecutionRepository, ActionPlanRepository, ExecutionBatchRepository
from app.repositories.decision import DecisionLogRepository
from app.repositories.memory_case import MemoryCaseRepository
from app.repositories.ops import ActionOutcomeRepository
from app.repositories.region import RegionRepository
from app.schemas.action import (
    ActionLogCollection,
    ActionLogEntry,
    FeedbackEvaluation,
    SimulatedExecutionRequest,
)
from app.services.feedback.evaluation_service import evaluate_execution_feedback
from app.services.memory_case_vector_service import MemoryCaseVectorService
from app.services.internal_memory_service import (
    build_execution_decision_log,
    build_feedback_decision_log,
    build_feedback_memory_case,
)
from app.services.audit_service import write_audit_log
from app.services.notification_service import create_execution_alert_notifications


@dataclass(slots=True)
class SimulatedExecutionBundle:
    """Aggregate result returned after simulated execution."""

    batch: ExecutionBatch
    plan: ActionPlan
    executions: list[ActionExecution]
    feedback: FeedbackEvaluation
    decision_logs: list[DecisionLog]
    outcomes: list[ActionOutcome]
    idempotent_replay: bool = False


async def execute_simulated_plan(
    session: AsyncSession,
    *,
    payload: SimulatedExecutionRequest,
    actor_name: str = "operator",
) -> SimulatedExecutionBundle:
    """Execute a validated plan in simulated mode only."""
    plan_repo = ActionPlanRepository(session)
    batch_repo = ExecutionBatchRepository(session)
    execution_repo = ActionExecutionRepository(session)
    decision_repo = DecisionLogRepository(session)
    outcome_repo = ActionOutcomeRepository(session)

    if payload.idempotency_key is not None:
        existing_batch = await batch_repo.get_by_idempotency_key(payload.idempotency_key)
        if existing_batch is not None:
            if existing_batch.plan_id != payload.action_plan_id:
                raise AppException(
                    status_code=HTTPStatus.CONFLICT,
                    code="idempotency_key_conflict",
                    message="Provided idempotency key is already used for another action plan.",
                )

            plan = await plan_repo.get_with_assessment(existing_batch.plan_id)
            if plan is None:
                raise AppException(
                    status_code=HTTPStatus.NOT_FOUND,
                    code="action_plan_not_found",
                    message=f"Action plan '{existing_batch.plan_id}' was not found.",
                )
            executions = await execution_repo.list_for_batch(existing_batch.id)
            decision_logs = await decision_repo.list_for_execution_ids(
                [execution.id for execution in executions]
            ) if executions else []
            feedback = FeedbackEvaluation(
                outcome_class="inconclusive",
                status="insufficient_new_observation",
                summary="Execution batch was returned from an existing idempotency key.",
                replan_recommended=True,
                replan_reason="Execution batch was returned from an existing idempotency key.",
            )
            return SimulatedExecutionBundle(
                batch=existing_batch,
                plan=plan,
                executions=executions,
                feedback=feedback,
                decision_logs=decision_logs,
                outcomes=[],
                idempotent_replay=True,
            )

    plan = await plan_repo.get_with_assessment(payload.action_plan_id)
    if plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{payload.action_plan_id}' was not found.",
        )

    steps = validate_execution_plan(plan)
    now = datetime.now(UTC)
    batch = ExecutionBatch(
        plan_id=plan.id,
        region_id=plan.region_id,
        status=ExecutionStatus.RUNNING,
        simulated=True,
        started_at=now,
        completed_at=None,
        idempotency_key=payload.idempotency_key,
        requested_by=actor_name,
    )
    await batch_repo.add(batch)

    executions: list[ActionExecution] = []
    decision_logs: list[DecisionLog] = []
    outcomes: list[ActionOutcome] = []
    if plan.incident is not None:
        plan.incident.status = IncidentStatus.EXECUTING

    for step in steps:
        execution = ActionExecution(
            plan_id=plan.id,
            batch_id=batch.id,
            region_id=plan.region_id,
            action_type=step.action_type,
            status=ExecutionStatus.SUCCEEDED,
            simulated=True,
            step_index=step.step_index,
            started_at=now,
            completed_at=now,
            result_summary=_build_execution_summary(step.action_type),
            result_payload={
                "title": step.title,
                "instructions": step.instructions,
                "rationale": step.rationale,
                "simulated": True,
            },
            idempotency_key=(
                f"{payload.idempotency_key}:{step.step_index}"
                if payload.idempotency_key is not None
                else f"{batch.id}:{step.step_index}"
            ),
            requested_by=actor_name,
        )
        await execution_repo.add(execution)
        executions.append(execution)

        if step.action_type in {ActionType.SEND_ALERT, ActionType.NOTIFY_FARMERS}:
            await create_execution_alert_notifications(
                session,
                incident_id=plan.incident_id,
                execution_id=execution.id,
                message=step.instructions,
            )

        decision_log = build_execution_decision_log(
            region_id=plan.region_id,
            risk_assessment_id=plan.risk_assessment_id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            logged_at=now,
            step_index=step.step_index,
            action_type=step.action_type,
            title=step.title,
            result_summary=execution.result_summary,
        )
        await decision_repo.add(decision_log)
        decision_logs.append(decision_log)
        await write_audit_log(
            session,
            event_type=AuditEventType.EXECUTION,
            actor_name=actor_name,
            region_id=plan.region_id,
            incident_id=plan.incident_id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            summary=f"Simulated action executed: {step.action_type.value}.",
            payload=execution.result_payload,
        )

    feedback = await evaluate_execution_feedback(session, plan)
    if executions:
        outcome = ActionOutcome(
            execution_id=executions[-1].id,
            recorded_at=datetime.now(UTC),
            pre_metrics={
                "baseline_salinity_dsm": str(feedback.baseline_salinity_dsm)
                if feedback.baseline_salinity_dsm is not None
                else None,
            },
            post_metrics={
                "latest_salinity_dsm": str(feedback.latest_salinity_dsm)
                if feedback.latest_salinity_dsm is not None
                else None,
                "delta_dsm": str(feedback.delta_dsm) if feedback.delta_dsm is not None else None,
                "legacy_status": feedback.status,
            },
            status=feedback.outcome_class,
            summary=feedback.summary,
        )
        await outcome_repo.add(outcome)
        outcomes.append(outcome)
    feedback_log = build_feedback_decision_log(
        region_id=plan.region_id,
        risk_assessment_id=plan.risk_assessment_id,
        action_plan_id=plan.id,
        action_execution_id=executions[-1].id if executions else None,
        logged_at=datetime.now(UTC),
        feedback=feedback,
    )
    await decision_repo.add(feedback_log)
    decision_logs.append(feedback_log)

    memory_case = build_feedback_memory_case(
        region_id=plan.region_id,
        station_id=(plan.risk_assessment.station_id if plan.risk_assessment is not None else None),
        risk_assessment_id=plan.risk_assessment_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        action_execution_id=(executions[-1].id if executions else None),
        decision_log_id=feedback_log.id,
        objective=plan.objective,
        severity=(
            plan.risk_assessment.risk_level.value
            if plan.risk_assessment is not None
            else None
        ),
        feedback=feedback,
        context_payload={
            "incident_id": str(plan.incident_id) if plan.incident_id is not None else None,
            "risk_assessment_id": str(plan.risk_assessment_id),
            "weather_linked": plan.risk_assessment.based_on_weather_id is not None
            if plan.risk_assessment is not None
            else False,
        },
        action_payload={
            "steps": plan.plan_steps,
            "execution_count": len(executions),
            "batch_id": str(batch.id),
        },
        occurred_at=datetime.now(UTC),
    )
    memory_case_repo = MemoryCaseRepository(session)
    if await memory_case_repo.is_table_ready():
        try:
            await memory_case_repo.add(memory_case)
            await asyncio.wait_for(
                MemoryCaseVectorService().upsert_memory_case(memory_case),
                timeout=2.5,
            )
        except SQLAlchemyError:
            # Keep execution path resilient during phased rollout before migration is applied.
            pass
        except Exception:
            # Vector indexing is best-effort and must not fail execution pipeline.
            pass

    plan.status = ActionPlanStatus.SIMULATED
    batch.status = ExecutionStatus.SUCCEEDED
    batch.completed_at = datetime.now(UTC)
    if plan.incident is not None:
        plan.incident.status = (
            IncidentStatus.RESOLVED
            if feedback.outcome_class == "success"
            else IncidentStatus.EXECUTING
        )
    await session.commit()

    for execution in executions:
        await session.refresh(execution)
    for decision_log in decision_logs:
        await session.refresh(decision_log)
    for outcome in outcomes:
        await session.refresh(outcome)
    await session.refresh(batch)
    await session.refresh(plan)

    return SimulatedExecutionBundle(
        batch=batch,
        plan=plan,
        executions=executions,
        feedback=feedback,
        decision_logs=decision_logs,
        outcomes=outcomes,
    )


async def list_action_logs(
    session: AsyncSession,
    *,
    plan_id: UUID | None = None,
    region_id: UUID | None = None,
    region_code: str | None = None,
    limit: int = 50,
) -> ActionLogCollection:
    """Return simulated execution logs with linked decision entries."""
    resolved_region_id = region_id
    if region_code is not None:
        region = await RegionRepository(session).get_by_code(region_code)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{region_code}' was not found.",
            )
        resolved_region_id = region.id

    execution_repo = ActionExecutionRepository(session)
    executions = await execution_repo.list_for_logs(
        region_id=resolved_region_id,
        plan_id=plan_id,
        limit=limit,
    )
    decision_logs = await DecisionLogRepository(session).list_for_execution_ids(
        [execution.id for execution in executions]
    )
    latest_log_by_execution: dict[UUID, DecisionLog] = {}
    for log in decision_logs:
        if log.action_execution_id is not None and log.action_execution_id not in latest_log_by_execution:
            latest_log_by_execution[log.action_execution_id] = log

    items = [
        ActionLogEntry(
            execution=execution,
            decision_log=latest_log_by_execution.get(execution.id),
        )
        for execution in executions
    ]
    return ActionLogCollection(items=items, count=len(items))


def _build_execution_summary(action_type) -> str:
    """Return a fixed summary for each simulated action type."""
    summaries = {
        "close_gate": "Mock gate close command accepted.",
        "open_gate": "Mock gate open command accepted.",
        "start_pump": "Mock pump start command accepted.",
        "stop_pump": "Mock pump stop command accepted.",
        "send_alert": "Mock stakeholder alert sent.",
        "notify-farmers": "Simulated advisory notification sent to farmers.",
        "wait-safe-window": "Simulated wait window applied pending safer intake conditions.",
        "close-gate-simulated": "Simulated temporary gate closure scenario completed.",
        "start-pump-simulated": "Simulated pump activation scenario completed.",
    }
    return summaries[action_type.value]
