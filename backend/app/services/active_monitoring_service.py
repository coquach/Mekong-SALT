"""Goal-driven active monitoring orchestration for Phase 4."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.goal import MonitoringGoal
from app.models.incident import Incident
from app.models.enums import ActionPlanStatus, ApprovalDecision
from app.orchestration.lifecycle_graph import (
    LifecycleAdvanceResult,
    advance_plan_with_lifecycle_graph,
)
from app.repositories.action import ActionPlanRepository
from app.repositories.goal import MonitoringGoalRepository
from app.schemas.agent import AgentPlanRequest
from app.schemas.approval import ApprovalRequest
from app.schemas.risk import RiskEvaluationFilters
from app.services.approval_service import decide_plan
from app.services.agent_planning_service import AgentPlanBundle, generate_agent_plan
from app.services.incident_service import ensure_incident_for_assessment
from app.services.risk_service import (
    RiskEvaluationBundle,
    evaluate_current_risk,
    resolve_target_reading,
)

MonitoringMode = Literal["active"]
logger = logging.getLogger(__name__)
AUTO_REPLAN_FEEDBACK_OUTCOMES = {
    "failed_execution",
    "failed_plan",
    "partial_success",
}


@dataclass(slots=True)
class MonitoringCycleResult:
    """Result of one active monitoring cycle for a goal."""

    goal_id: UUID
    mode: MonitoringMode
    status: str
    risk_bundle: RiskEvaluationBundle | None = None
    incident: Incident | None = None
    plan_bundle: AgentPlanBundle | None = None
    lifecycle_result: LifecycleAdvanceResult | None = None
    orchestration_path: Literal["lifecycle_graph"] | None = None
    transition_log: list[dict[str, Any]] | None = None
    existing_plan: ActionPlan | None = None
    replan_attempts: int = 0
    replan_history: list[dict[str, Any]] | None = None
    reason: str | None = None


@dataclass(slots=True)
class WorkerTickResult:
    """Summary returned after one active monitoring scheduler tick."""

    scanned: int
    due: int
    locked: int
    results: list[MonitoringCycleResult]


@dataclass(slots=True)
class FeedbackReplanLoopResult:
    """Result of one optional feedback-driven replan loop."""

    attempts: int
    risk_bundle: RiskEvaluationBundle
    plan_bundle: AgentPlanBundle
    lifecycle_result: LifecycleAdvanceResult
    history: list[dict[str, Any]]


async def run_monitoring_goal_cycle(
    session: AsyncSession,
    *,
    goal: MonitoringGoal,
    mode: MonitoringMode,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> MonitoringCycleResult:
    """Run observe -> risk -> incident -> lifecycle graph advancement for one goal.

    The monitoring cycle always performs autonomous planning when the goal is
    eligible: it records deterministic risk evidence, resolves or creates an
    incident, generates a plan when auto-plan is enabled, and advances that plan
    through approval, execution, feedback, and memory persistence. If feedback
    indicates failed outcomes, an optional capped auto-replan loop can generate
    follow-up plans.
    """
    resolved_settings = settings or get_settings()
    filters = RiskEvaluationFilters(
        station_id=goal.station_id,
        region_id=goal.region_id,
    )
    target_reading = await resolve_target_reading(session, filters)
    if goal.last_processed_reading_id == target_reading.id:
        await _mark_goal_cycle(
            session,
            goal,
            status="skipped_no_new_reading",
            plan_id=goal.last_run_plan_id,
            processed_reading_id=target_reading.id,
        )
        return MonitoringCycleResult(
            goal_id=goal.id,
            mode=mode,
            status="skipped_no_new_reading",
            reason="Latest target reading has already been processed.",
        )

    risk_bundle = await evaluate_current_risk(
        session,
        filters=filters,
        redis_manager=redis_manager,
        target_reading=target_reading,
        trigger_source="monitoring.worker.observe_risk",
        trigger_payload={
            "goal_id": str(goal.id),
            "goal_name": goal.name,
            "mode": mode,
        },
    )
    incident_result = await ensure_incident_for_assessment(
        session,
        risk_bundle.assessment,
        actor_name="active-monitoring-worker",
    )
    incident = incident_result.incident

    if incident is None:
        await _mark_goal_cycle(
            session,
            goal,
            status="succeeded_no_incident",
            plan_id=None,
            processed_reading_id=risk_bundle.reading.id,
        )
        return MonitoringCycleResult(
            goal_id=goal.id,
            mode=mode,
            status="succeeded_no_incident",
            risk_bundle=risk_bundle,
            reason=incident_result.reason,
        )

    if not goal.auto_plan_enabled:
        await _mark_goal_cycle(
            session,
            goal,
            status="succeeded_auto_plan_disabled",
            plan_id=None,
            processed_reading_id=risk_bundle.reading.id,
        )
        return MonitoringCycleResult(
            goal_id=goal.id,
            mode=mode,
            status="succeeded_auto_plan_disabled",
            risk_bundle=risk_bundle,
            incident=incident,
            reason="Goal auto_plan_enabled is false.",
        )

    existing_plan = await ActionPlanRepository(session).get_open_for_incident(incident.id)
    if existing_plan is not None:
        timed_out = await _maybe_auto_reject_stale_pending_plan(
            session,
            plan=existing_plan,
            settings=resolved_settings,
        )
        if timed_out:
            existing_plan = await ActionPlanRepository(session).get_open_for_incident(incident.id)
    if existing_plan is not None:
        await _mark_goal_cycle(
            session,
            goal,
            status="skipped_existing_plan",
            plan_id=existing_plan.id,
            processed_reading_id=risk_bundle.reading.id,
        )
        return MonitoringCycleResult(
            goal_id=goal.id,
            mode=mode,
            status="skipped_existing_plan",
            risk_bundle=risk_bundle,
            incident=incident,
            existing_plan=existing_plan,
            reason="A plan already exists for this incident.",
        )

    plan_bundle = await generate_agent_plan(
        session,
        payload=AgentPlanRequest(
            station_id=goal.station_id,
            region_id=goal.region_id,
            incident_id=incident.id,
            objective=goal.objective,
            provider=goal.provider,
        ),
        redis_manager=redis_manager,
        risk_bundle=risk_bundle,
        trigger_source="monitoring.worker.auto_plan",
        trigger_payload={
            "goal_id": str(goal.id),
            "goal_name": goal.name,
            "source_risk_assessment_id": str(risk_bundle.assessment.id),
            "source_incident_id": str(incident.id),
        },
    )
    lifecycle_result = await advance_plan_with_lifecycle_graph(
        session,
        plan=plan_bundle.plan,
        settings=resolved_settings,
    )
    replan_result = await _maybe_auto_replan_after_feedback(
        session,
        goal=goal,
        filters=filters,
        base_risk_bundle=risk_bundle,
        base_plan_bundle=plan_bundle,
        base_lifecycle_result=lifecycle_result,
        redis_manager=redis_manager,
        settings=resolved_settings,
    )
    replan_attempts = replan_result.attempts
    replan_history = replan_result.history
    risk_bundle = replan_result.risk_bundle
    plan_bundle = replan_result.plan_bundle
    lifecycle_result = replan_result.lifecycle_result
    orchestration_path: Literal["lifecycle_graph"] = "lifecycle_graph"

    if lifecycle_result.status == "executed" and replan_attempts > 0:
        status = "succeeded_plan_replanned_executed"
    elif lifecycle_result.status == "executed":
        status = "succeeded_plan_executed"
    elif lifecycle_result.status == "awaiting_human_approval" and replan_attempts > 0:
        status = "succeeded_replan_pending_human"
    elif lifecycle_result.status == "awaiting_human_approval":
        status = "succeeded_pending_human"
    elif replan_attempts > 0:
        status = "succeeded_plan_replanned"
    else:
        status = "succeeded_plan_created"
    await _mark_goal_cycle(
        session,
        goal,
        status=status,
        plan_id=lifecycle_result.plan.id,
        processed_reading_id=risk_bundle.reading.id,
    )
    return MonitoringCycleResult(
        goal_id=goal.id,
        mode=mode,
        status=status,
        risk_bundle=risk_bundle,
        incident=incident,
        plan_bundle=plan_bundle,
        lifecycle_result=lifecycle_result,
        orchestration_path=orchestration_path,
        transition_log=lifecycle_result.transition_log,
        replan_attempts=replan_attempts,
        replan_history=replan_history,
        reason=lifecycle_result.reason,
    )


async def run_due_monitoring_goals(
    session: AsyncSession,
    *,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> WorkerTickResult:
    """Load active goals, lock each due goal, and execute one cycle per goal."""
    resolved_settings = settings or get_settings()
    current_time = now or datetime.now(UTC)
    goals = list(
        await MonitoringGoalRepository(session).list_active(
            limit=resolved_settings.active_monitoring_batch_size,
        )
    )
    due_goals = [goal for goal in goals if is_goal_due(goal, current_time)]
    results: list[MonitoringCycleResult] = []
    locked = 0

    for goal in due_goals:
        token = uuid4().hex
        lock_key = goal_lock_key(goal.id)
        lock_ttl = max(
            resolved_settings.active_monitoring_lock_ttl_seconds,
            goal.evaluation_interval_minutes * 60,
        )
        has_lock = await acquire_goal_lock(
            redis_manager=redis_manager,
            key=lock_key,
            token=token,
            ttl_seconds=lock_ttl,
        )
        if not has_lock:
            continue
        locked += 1

        try:
            results.append(
                await run_monitoring_goal_cycle(
                    session,
                    goal=goal,
                        mode=resolved_settings.active_monitoring_mode,
                    redis_manager=redis_manager,
                    settings=resolved_settings,
                )
            )
        except Exception as exc:
            logger.exception(
                "Active monitoring goal cycle failed",
                extra={"goal_id": str(goal.id)},
            )
            await mark_goal_cycle_failed(session, goal, reason=str(exc))
        finally:
            await release_goal_lock(
                redis_manager=redis_manager,
                key=lock_key,
                token=token,
            )

    return WorkerTickResult(
        scanned=len(goals),
        due=len(due_goals),
        locked=locked,
        results=results,
    )


async def mark_goal_cycle_failed(
    session: AsyncSession,
    goal: MonitoringGoal,
    *,
    reason: str,
) -> None:
    """Persist a compact failure marker on the goal after a worker exception."""
    goal.last_run_at = datetime.now(UTC)
    goal.last_run_status = "failed"
    await session.commit()


def is_goal_due(goal: MonitoringGoal, now: datetime) -> bool:
    """Return true when a goal should run in the current worker tick."""
    if goal.last_run_at is None:
        return True
    last_run_at = goal.last_run_at
    if last_run_at.tzinfo is None:
        last_run_at = last_run_at.replace(tzinfo=UTC)
    return now >= last_run_at + timedelta(minutes=goal.evaluation_interval_minutes)


def goal_lock_key(goal_id: UUID) -> str:
    """Build the Redis lock key used to prevent duplicate goal cycles."""
    return f"mekong-salt:monitoring-goal:{goal_id}:lock"


async def acquire_goal_lock(
    *,
    redis_manager: RedisManager | None,
    key: str,
    token: str,
    ttl_seconds: int,
) -> bool:
    """Acquire a Redis lock when Redis is available.

    Local development can run without Redis; in that case this returns true and
    relies on a single worker process. Production-like demos should use Redis.
    """
    if redis_manager is None:
        return True
    return await redis_manager.acquire_lock(key, token, ttl_seconds)


async def release_goal_lock(
    *,
    redis_manager: RedisManager | None,
    key: str,
    token: str,
) -> None:
    """Release a goal lock if the current worker still owns it."""
    if redis_manager is not None:
        await redis_manager.release_lock(key, token)


async def _mark_goal_cycle(
    session: AsyncSession,
    goal: MonitoringGoal,
    *,
    status: str,
    plan_id: UUID | None,
    processed_reading_id: UUID | None,
) -> None:
    goal.last_run_at = datetime.now(UTC)
    goal.last_run_status = status
    goal.last_run_plan_id = plan_id
    goal.last_processed_reading_id = processed_reading_id
    await session.commit()


async def _maybe_auto_replan_after_feedback(
    session: AsyncSession,
    *,
    goal: MonitoringGoal,
    filters: RiskEvaluationFilters,
    base_risk_bundle: RiskEvaluationBundle,
    base_plan_bundle: AgentPlanBundle,
    base_lifecycle_result: LifecycleAdvanceResult,
    redis_manager: RedisManager | None,
    settings: Settings,
) -> FeedbackReplanLoopResult:
    """Auto-replan when execution feedback indicates a failed outcome."""
    max_attempts = max(0, int(getattr(settings, "active_monitoring_feedback_replan_max_attempts", 0)))
    current_risk_bundle = base_risk_bundle
    current_plan_bundle = base_plan_bundle
    current_lifecycle_result = base_lifecycle_result
    history: list[dict[str, Any]] = []
    attempts = 0

    while attempts < max_attempts:
        feedback = _extract_feedback(current_lifecycle_result)
        if feedback is None:
            break
        outcome = str(feedback.outcome_class or "").strip().lower()
        if outcome not in AUTO_REPLAN_FEEDBACK_OUTCOMES:
            break

        incident_id = current_plan_bundle.plan.incident_id
        if incident_id is None:
            history.append(
                {
                    "attempt": attempts + 1,
                    "status": "skipped",
                    "reason": "auto-replan requires incident_id on previous plan.",
                    "feedback_outcome": outcome,
                }
            )
            break

        attempts += 1
        latest_reading = await resolve_target_reading(session, filters)
        if latest_reading.id != current_risk_bundle.reading.id:
            current_risk_bundle = await evaluate_current_risk(
                session,
                filters=filters,
                redis_manager=redis_manager,
                target_reading=latest_reading,
                trigger_source="monitoring.worker.auto_replan.observe_risk",
                trigger_payload={
                    "goal_id": str(goal.id),
                    "goal_name": goal.name,
                    "attempt": attempts,
                    "previous_plan_id": str(current_plan_bundle.plan.id),
                    "previous_feedback_outcome": outcome,
                },
            )

        next_plan_bundle = await generate_agent_plan(
            session,
            payload=AgentPlanRequest(
                station_id=goal.station_id,
                region_id=goal.region_id,
                incident_id=incident_id,
                objective=goal.objective,
                provider=goal.provider,
            ),
            redis_manager=redis_manager,
            risk_bundle=current_risk_bundle,
            trigger_source="monitoring.worker.auto_replan",
            trigger_payload={
                "goal_id": str(goal.id),
                "goal_name": goal.name,
                "attempt": attempts,
                "previous_plan_id": str(current_plan_bundle.plan.id),
                "previous_feedback_outcome": outcome,
                "previous_feedback_summary": feedback.summary,
            },
        )
        next_lifecycle_result = await advance_plan_with_lifecycle_graph(
            session,
            plan=next_plan_bundle.plan,
            settings=settings,
        )

        history.append(
            {
                "attempt": attempts,
                "status": "replanned",
                "from_plan_id": str(current_plan_bundle.plan.id),
                "to_plan_id": str(next_plan_bundle.plan.id),
                "feedback_outcome": outcome,
                "lifecycle_status": next_lifecycle_result.status,
                "reason": next_lifecycle_result.reason,
            }
        )
        current_plan_bundle = next_plan_bundle
        current_lifecycle_result = next_lifecycle_result

    return FeedbackReplanLoopResult(
        attempts=attempts,
        risk_bundle=current_risk_bundle,
        plan_bundle=current_plan_bundle,
        lifecycle_result=current_lifecycle_result,
        history=history,
    )


def _extract_feedback(lifecycle_result: LifecycleAdvanceResult):
    """Extract feedback payload from a lifecycle result when execution happened."""
    if lifecycle_result.execution_bundle is None:
        return None
    return lifecycle_result.execution_bundle.feedback


async def _maybe_auto_reject_stale_pending_plan(
    session: AsyncSession,
    *,
    plan: ActionPlan,
    settings: Settings,
) -> bool:
    """Auto-reject stale pending approvals so monitoring can continue in demo runs."""
    if plan.status is not ActionPlanStatus.PENDING_APPROVAL:
        return False

    timeout_minutes = max(0, int(getattr(settings, "active_monitoring_approval_timeout_minutes", 0)))
    timeout_action = str(
        getattr(settings, "active_monitoring_approval_timeout_action", "auto_reject")
    ).strip().lower()

    if timeout_minutes == 0 or timeout_action != "auto_reject":
        return False

    pending_since = plan.updated_at or plan.created_at
    if pending_since.tzinfo is None:
        pending_since = pending_since.replace(tzinfo=UTC)

    if datetime.now(UTC) < pending_since + timedelta(minutes=timeout_minutes):
        return False

    await decide_plan(
        session,
        plan_id=plan.id,
        payload=ApprovalRequest(
            decision=ApprovalDecision.REJECTED,
            comment=(
                "Automatically rejected by approval-timeout policy to unblock "
                "demo monitoring flow."
            ),
        ),
        actor_name="approval-timeout-guard",
    )
    logger.warning(
        "Auto-rejected stale pending approval plan",
        extra={
            "plan_id": str(plan.id),
            "timeout_minutes": timeout_minutes,
        },
    )
    return True
