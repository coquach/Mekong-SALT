"""Monitoring goal configuration services."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.goal import MonitoringGoal
from app.repositories.goal import MonitoringGoalRepository
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository
from app.schemas.goal import MonitoringGoalCreate, MonitoringGoalUpdate


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
        provider="gemini",
        warning_threshold_dsm=payload.thresholds.warning_threshold_dsm,
        critical_threshold_dsm=payload.thresholds.critical_threshold_dsm,
        evaluation_interval_minutes=payload.evaluation_interval_minutes,
        auto_plan_enabled=payload.auto_plan_enabled,
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

    goal.provider = "gemini"

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
