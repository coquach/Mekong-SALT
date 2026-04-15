"""Goal-driven active monitoring orchestration for Phase 4."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.goal import MonitoringGoal
from app.models.incident import Incident
from app.orchestration.reactive import ReactiveAdvanceResult, advance_plan_reactively
from app.repositories.action import ActionPlanRepository
from app.repositories.goal import MonitoringGoalRepository
from app.schemas.agent import AgentPlanRequest
from app.schemas.risk import RiskEvaluationFilters
from app.services.agent_planning_service import AgentPlanBundle, generate_agent_plan
from app.services.incident_service import ensure_incident_for_assessment
from app.services.risk_service import RiskEvaluationBundle, evaluate_current_risk

MonitoringMode = Literal["dry_run", "active"]
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MonitoringCycleResult:
    """Result of one active monitoring cycle for a goal."""

    goal_id: UUID
    mode: MonitoringMode
    status: str
    risk_bundle: RiskEvaluationBundle | None = None
    incident: Incident | None = None
    plan_bundle: AgentPlanBundle | None = None
    reactive_result: ReactiveAdvanceResult | None = None
    existing_plan: ActionPlan | None = None
    reason: str | None = None


@dataclass(slots=True)
class WorkerTickResult:
    """Summary returned after one active monitoring scheduler tick."""

    scanned: int
    due: int
    locked: int
    results: list[MonitoringCycleResult]


async def run_monitoring_goal_cycle(
    session: AsyncSession,
    *,
    goal: MonitoringGoal,
    mode: MonitoringMode,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> MonitoringCycleResult:
    """Run observe -> risk -> incident -> optional reactive plan execution for one goal.

    Dry-run still records deterministic risk and incident evidence so operators can
    inspect stability over time, but it deliberately skips autonomous plan creation.
    Active mode creates one plan when auto-plan is enabled and no active/simulated plan
    already exists for the same incident, then advances it through the reactive
    approval/execution pipeline according to settings.
    """
    resolved_settings = settings or get_settings()
    risk_bundle = await evaluate_current_risk(
        session,
        filters=RiskEvaluationFilters(
            station_id=goal.station_id,
            region_id=goal.region_id,
        ),
        redis_manager=redis_manager,
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

    if mode == "dry_run":
        await _mark_goal_cycle(
            session,
            goal,
            status="dry_run_observed",
            plan_id=None,
        )
        return MonitoringCycleResult(
            goal_id=goal.id,
            mode=mode,
            status="dry_run_observed",
            risk_bundle=risk_bundle,
            incident=incident,
            reason="Dry-run mode skips auto-plan creation.",
        )

    if incident is None:
        await _mark_goal_cycle(
            session,
            goal,
            status="succeeded_no_incident",
            plan_id=None,
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
        await _mark_goal_cycle(
            session,
            goal,
            status="skipped_existing_plan",
            plan_id=existing_plan.id,
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
        trigger_source="monitoring.worker.auto_plan",
        trigger_payload={
            "goal_id": str(goal.id),
            "goal_name": goal.name,
            "source_risk_assessment_id": str(risk_bundle.assessment.id),
            "source_incident_id": str(incident.id),
        },
    )
    reactive_result = await advance_plan_reactively(
        session,
        plan=plan_bundle.plan,
        settings=resolved_settings,
    )
    status = (
        "succeeded_plan_executed"
        if reactive_result.status == "executed"
        else "succeeded_plan_created"
    )
    await _mark_goal_cycle(
        session,
        goal,
        status=status,
        plan_id=plan_bundle.plan.id,
    )
    return MonitoringCycleResult(
        goal_id=goal.id,
        mode=mode,
        status=status,
        risk_bundle=risk_bundle,
        incident=incident,
        plan_bundle=plan_bundle,
        reactive_result=reactive_result,
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
) -> None:
    goal.last_run_at = datetime.now(UTC)
    goal.last_run_status = status
    goal.last_run_plan_id = plan_id
    await session.commit()
