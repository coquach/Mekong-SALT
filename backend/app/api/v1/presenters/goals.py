"""Response mapping helpers for monitoring goal endpoints."""

from app.models.goal import MonitoringGoal
from app.schemas.goal import GoalThresholds, MonitoringGoalRead


def goal_to_read(goal: MonitoringGoal) -> MonitoringGoalRead:
    """Map a monitoring goal ORM instance to its API read schema."""
    return MonitoringGoalRead(
        id=goal.id,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        name=goal.name,
        description=goal.description,
        region_id=goal.region_id,
        station_id=goal.station_id,
        objective=goal.objective,
        provider=goal.provider,
        thresholds=GoalThresholds(
            warning_threshold_dsm=goal.warning_threshold_dsm,
            critical_threshold_dsm=goal.critical_threshold_dsm,
        ),
        evaluation_interval_minutes=goal.evaluation_interval_minutes,
        is_active=goal.is_active,
        last_run_at=goal.last_run_at,
        last_run_status=goal.last_run_status,
        last_run_plan_id=goal.last_run_plan_id,
        last_processed_reading_id=goal.last_processed_reading_id,
    )
