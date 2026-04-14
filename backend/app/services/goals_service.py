"""Monitoring goal services for CRUD and run-once orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.db.redis import RedisManager
from app.models.goal import MonitoringGoal
from app.repositories.goal import MonitoringGoalRepository
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository
from app.schemas.agent import AgentPlanRequest
from app.schemas.goal import MonitoringGoalCreate, MonitoringGoalUpdate, GoalRunOnceRequest
from app.services.agent_planning_service import AgentPlanBundle, generate_agent_plan


@dataclass(slots=True)
class MonitoringGoalRunOnceBundle:
    """Aggregate payload returned from run-once execution."""

    goal: MonitoringGoal
    plan_bundle: AgentPlanBundle


async def create_monitoring_goal(
    session: AsyncSession,
    payload: MonitoringGoalCreate,
) -> MonitoringGoal:
    """Create and persist a monitoring goal."""
    repo = MonitoringGoalRepository(session)
    await _validate_goal_target(session, region_id=payload.region_id, station_id=payload.station_id)
    await _ensure_goal_name_is_unique(session, payload.name)

    goal = MonitoringGoal(
        name=payload.name,
        description=payload.description,
        region_id=payload.region_id,
        station_id=payload.station_id,
        objective=payload.objective,
        provider=payload.provider,
        warning_threshold_dsm=payload.thresholds.warning_threshold_dsm,
        critical_threshold_dsm=payload.thresholds.critical_threshold_dsm,
        evaluation_interval_minutes=payload.evaluation_interval_minutes,
        is_active=payload.is_active,
    )
    await repo.add(goal)
    await session.commit()

    created = await repo.get_with_relations(goal.id)
    if created is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="monitoring_goal_reload_failed",
            message="Monitoring goal was stored but could not be reloaded.",
        )
    return created


async def list_monitoring_goals(
    session: AsyncSession,
    *,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[MonitoringGoal]:
    """List monitoring goals."""
    return list(await MonitoringGoalRepository(session).list_recent(limit=limit, is_active=is_active))


async def get_monitoring_goal(session: AsyncSession, goal_id: UUID) -> MonitoringGoal:
    """Load one monitoring goal by ID."""
    goal = await MonitoringGoalRepository(session).get_with_relations(goal_id)
    if goal is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="monitoring_goal_not_found",
            message=f"Monitoring goal '{goal_id}' was not found.",
        )
    return goal


async def update_monitoring_goal(
    session: AsyncSession,
    goal_id: UUID,
    payload: MonitoringGoalUpdate,
) -> MonitoringGoal:
    """Update an existing monitoring goal."""
    repo = MonitoringGoalRepository(session)
    goal = await get_monitoring_goal(session, goal_id)

    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] != goal.name:
        await _ensure_goal_name_is_unique(session, updates["name"])

    if "thresholds" in updates:
        thresholds = updates.pop("thresholds")
        goal.warning_threshold_dsm = thresholds["warning_threshold_dsm"]
        goal.critical_threshold_dsm = thresholds["critical_threshold_dsm"]

    for field, value in updates.items():
        setattr(goal, field, value)

    await _validate_goal_target(session, region_id=goal.region_id, station_id=goal.station_id)
    _validate_threshold_order(goal.warning_threshold_dsm, goal.critical_threshold_dsm)

    await session.commit()
    updated = await repo.get_with_relations(goal.id)
    if updated is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="monitoring_goal_reload_failed",
            message="Monitoring goal was updated but could not be reloaded.",
        )
    return updated


async def delete_monitoring_goal(session: AsyncSession, goal_id: UUID) -> None:
    """Delete a monitoring goal."""
    repo = MonitoringGoalRepository(session)
    goal = await get_monitoring_goal(session, goal_id)
    await repo.delete(goal)
    await session.commit()


async def run_monitoring_goal_once(
    session: AsyncSession,
    *,
    goal_id: UUID,
    payload: GoalRunOnceRequest,
    redis_manager: RedisManager | None,
) -> MonitoringGoalRunOnceBundle:
    """Execute one planning cycle using persisted monitoring goal configuration."""
    goal = await get_monitoring_goal(session, goal_id)
    if not goal.is_active:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="monitoring_goal_inactive",
            message=f"Monitoring goal '{goal_id}' is inactive and cannot be run.",
        )

    objective = payload.objective or goal.objective
    provider = payload.provider or goal.provider

    plan_request = AgentPlanRequest(
        station_id=goal.station_id,
        region_id=goal.region_id,
        incident_id=payload.incident_id,
        objective=objective,
        provider=provider,
    )
    try:
        plan_bundle = await generate_agent_plan(
            session,
            payload=plan_request,
            redis_manager=redis_manager,
            trigger_source="goals.run_once",
            trigger_payload={"goal_id": str(goal.id), "goal_name": goal.name},
        )
    except TypeError as exc:
        if "trigger_source" not in str(exc) and "trigger_payload" not in str(exc):
            raise
        plan_bundle = await generate_agent_plan(
            session,
            payload=plan_request,
            redis_manager=redis_manager,
        )

    goal.last_run_at = datetime.now(UTC)
    goal.last_run_status = "succeeded"
    goal.last_run_plan_id = plan_bundle.plan.id
    await session.commit()

    refreshed_goal = await MonitoringGoalRepository(session).get_with_relations(goal.id)
    if refreshed_goal is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="monitoring_goal_reload_failed",
            message="Monitoring goal run completed but goal could not be reloaded.",
        )

    return MonitoringGoalRunOnceBundle(goal=refreshed_goal, plan_bundle=plan_bundle)


async def _ensure_goal_name_is_unique(session: AsyncSession, name: str) -> None:
    if await MonitoringGoalRepository(session).get_by_name(name) is not None:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="monitoring_goal_name_exists",
            message=f"Monitoring goal '{name}' already exists.",
        )


async def _validate_goal_target(
    session: AsyncSession,
    *,
    region_id: UUID,
    station_id: UUID | None,
) -> None:
    region = await RegionRepository(session).get(region_id)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Region '{region_id}' was not found.",
        )

    if station_id is None:
        return

    station = await SensorStationRepository(session).get(station_id)
    if station is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="sensor_station_not_found",
            message=f"Sensor station '{station_id}' was not found.",
        )
    if station.region_id != region_id:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="station_region_mismatch",
            message="station and region filters do not refer to the same region.",
        )


def _validate_threshold_order(warning_threshold, critical_threshold) -> None:
    if critical_threshold <= warning_threshold:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="invalid_goal_thresholds",
            message="critical_threshold_dsm must be greater than warning_threshold_dsm.",
        )
