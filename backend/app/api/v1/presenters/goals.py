"""Response mapping helpers for monitoring goal endpoints."""

from app.models.goal import MonitoringGoal
from app.schemas.action import ActionPlanRead
from app.schemas.agent import AgentPlanResponse
from app.schemas.goal import GoalRunOnceResponse, GoalThresholds, MonitoringGoalRead
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.agent_planning_service import AgentPlanBundle
from app.services.goals_service import MonitoringGoalRunOnceBundle


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
        auto_plan_enabled=goal.auto_plan_enabled,
        is_active=goal.is_active,
        last_run_at=goal.last_run_at,
        last_run_status=goal.last_run_status,
        last_run_plan_id=goal.last_run_plan_id,
    )


def agent_plan_bundle_to_response(bundle: AgentPlanBundle) -> AgentPlanResponse:
    """Map a persisted planning bundle to the public plan response schema."""
    return AgentPlanResponse(
        assessment=RiskAssessmentRead.model_validate(bundle.risk_bundle.assessment),
        reading=SensorReadingRead.model_validate(bundle.risk_bundle.reading),
        weather_snapshot=(
            WeatherSnapshotRead.model_validate(bundle.risk_bundle.weather_snapshot)
            if bundle.risk_bundle.weather_snapshot is not None
            else None
        ),
        plan=ActionPlanRead.model_validate(bundle.plan),
        agent_run_id=getattr(bundle, "run_id", None),
    )


def goal_run_once_to_response(bundle: MonitoringGoalRunOnceBundle) -> GoalRunOnceResponse:
    """Map a goal run-once service bundle to the endpoint response schema."""
    return GoalRunOnceResponse(
        goal=goal_to_read(bundle.goal),
        result=agent_plan_bundle_to_response(bundle.plan_bundle),
    )
