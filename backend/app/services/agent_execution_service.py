"""Simulated execution and feedback services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution_policy import validate_execution_plan
from app.core.exceptions import AppException
from app.models.action import ActionExecution, ActionPlan
from app.models.audit import ActionOutcome
from app.models.decision import DecisionLog
from app.models.enums import ActionPlanStatus, ActionType, AuditEventType, DecisionActorType, ExecutionStatus, IncidentStatus
from app.repositories.action import ActionExecutionRepository, ActionPlanRepository
from app.repositories.decision import DecisionLogRepository
from app.repositories.ops import ActionOutcomeRepository
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorReadingRepository
from app.schemas.action import (
    ActionLogCollection,
    ActionLogEntry,
    FeedbackEvaluation,
    SimulatedExecutionRequest,
)
from app.services.audit_service import write_audit_log
from app.services.notification_service import create_execution_alert_notifications


@dataclass(slots=True)
class SimulatedExecutionBundle:
    """Aggregate result returned after simulated execution."""

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
    execution_repo = ActionExecutionRepository(session)
    decision_repo = DecisionLogRepository(session)
    outcome_repo = ActionOutcomeRepository(session)

    if payload.idempotency_key is not None:
        existing = await execution_repo.get_by_idempotency_key(payload.idempotency_key)
        if existing is not None:
            plan = await plan_repo.get_with_assessment(payload.action_plan_id)
            if plan is None:
                raise AppException(
                    status_code=HTTPStatus.NOT_FOUND,
                    code="action_plan_not_found",
                    message=f"Action plan '{payload.action_plan_id}' was not found.",
                )
            feedback = FeedbackEvaluation(
                status="insufficient_new_observation",
                summary="Execution was returned from an existing idempotency key.",
            )
            return SimulatedExecutionBundle(
                plan=plan,
                executions=[existing],
                feedback=feedback,
                decision_logs=[],
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
    executions: list[ActionExecution] = []
    decision_logs: list[DecisionLog] = []
    outcomes: list[ActionOutcome] = []
    if plan.incident is not None:
        plan.incident.status = IncidentStatus.EXECUTING

    for step in steps:
        execution = ActionExecution(
            plan_id=plan.id,
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
                payload.idempotency_key
                if payload.idempotency_key is not None and step.step_index == 1
                else f"{payload.idempotency_key}:{step.step_index}"
                if payload.idempotency_key is not None
                else payload.idempotency_key
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

        decision_log = DecisionLog(
            region_id=plan.region_id,
            risk_assessment_id=plan.risk_assessment_id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            logged_at=now,
            actor_type=DecisionActorType.AGENT,
            actor_name="simulated-execution-engine",
            summary=f"Simulated action executed: {step.action_type.value}",
            outcome="simulated",
            details={
                "step_index": step.step_index,
                "action_type": step.action_type.value,
                "title": step.title,
                "result_summary": execution.result_summary,
            },
            store_as_memory=False,
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

    feedback = await _evaluate_feedback(session, plan)
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
            },
            status=feedback.status,
            summary=feedback.summary,
        )
        await outcome_repo.add(outcome)
        outcomes.append(outcome)
    feedback_log = DecisionLog(
        region_id=plan.region_id,
        risk_assessment_id=plan.risk_assessment_id,
        action_plan_id=plan.id,
        action_execution_id=executions[-1].id if executions else None,
        logged_at=datetime.now(UTC),
        actor_type=DecisionActorType.SYSTEM,
        actor_name="feedback-evaluator",
        summary="Simulated execution feedback evaluated.",
        outcome=feedback.status,
        details=feedback.model_dump(mode="json"),
        store_as_memory=feedback.status == "improved",
    )
    await decision_repo.add(feedback_log)
    decision_logs.append(feedback_log)

    plan.status = ActionPlanStatus.SIMULATED
    if plan.incident is not None:
        plan.incident.status = IncidentStatus.RESOLVED if feedback.status == "improved" else IncidentStatus.EXECUTING
    await session.commit()

    for execution in executions:
        await session.refresh(execution)
    for decision_log in decision_logs:
        await session.refresh(decision_log)
    for outcome in outcomes:
        await session.refresh(outcome)
    await session.refresh(plan)

    return SimulatedExecutionBundle(
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


async def _evaluate_feedback(
    session: AsyncSession,
    plan: ActionPlan,
) -> FeedbackEvaluation:
    """Evaluate whether salinity appears reduced after simulated actions."""
    if plan.risk_assessment is None or plan.risk_assessment.station_id is None:
        return FeedbackEvaluation(
            status="insufficient_new_observation",
            summary="Risk assessment is missing station context for feedback evaluation.",
        )
    if plan.risk_assessment.based_on_reading_id is None:
        return FeedbackEvaluation(
            status="insufficient_new_observation",
            summary="Risk assessment is missing a baseline reading for feedback evaluation.",
        )

    reading_repo = SensorReadingRepository(session)
    baseline = await reading_repo.get_with_station(plan.risk_assessment.based_on_reading_id)
    latest = await reading_repo.get_latest_for_station(plan.risk_assessment.station_id)
    if baseline is None or latest is None:
        return FeedbackEvaluation(
            status="insufficient_new_observation",
            summary="No comparable readings were available for feedback evaluation.",
        )
    if latest.recorded_at <= baseline.recorded_at:
        return FeedbackEvaluation(
            status="insufficient_new_observation",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            summary="No newer sensor reading is available after the simulated actions.",
        )

    delta = latest.salinity_dsm - baseline.salinity_dsm
    if delta < Decimal("0.00"):
        return FeedbackEvaluation(
            status="improved",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Latest observed salinity is lower than the baseline reading.",
        )
    if delta == Decimal("0.00"):
        return FeedbackEvaluation(
            status="no_change",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Latest observed salinity is unchanged after simulated actions.",
        )
    return FeedbackEvaluation(
        status="not_improved",
        baseline_salinity_dsm=baseline.salinity_dsm,
        latest_salinity_dsm=latest.salinity_dsm,
        delta_dsm=delta,
        summary="Latest observed salinity did not decrease after simulated actions.",
    )


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
