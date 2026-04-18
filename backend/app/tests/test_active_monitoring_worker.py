"""Tests for Phase 4 active monitoring worker behavior."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.models.action import ActionExecution, ActionPlan
from app.models.approval import Approval
from app.models.goal import MonitoringGoal
from app.models.risk import RiskAssessment
from app.models.sensor import SensorReading
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep
from app.models.enums import ActionPlanStatus, ActionType, RiskLevel
from app.services.active_monitoring_service import run_monitoring_goal_cycle
from app.services.active_monitoring_service import should_auto_plan


async def _persist_stub_weather_snapshot(session, *, region_id) -> WeatherSnapshot:
    snapshot = WeatherSnapshot(
        region_id=region_id,
        observed_at=datetime.now(UTC),
        wind_speed_mps=Decimal("4.20"),
        wind_direction_deg=135,
        tide_level_m=Decimal("1.30"),
        rainfall_mm=Decimal("0.00"),
        condition_summary="stubbed active monitoring weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


@pytest.mark.asyncio
async def test_active_monitoring_skips_duplicate_open_plan(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-AutoPlan-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Protect irrigation intake from salinity intrusion",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    class StubProvider:
        name = "phase4-stub-provider"

        async def generate_plan(self, *, objective, context):
            return GeneratedActionPlan(
                objective=objective,
                summary="Active monitoring plan generated once.",
                assumptions=["Operators will approve before simulated execution."],
                steps=[
                    PlanStep(
                        step_index=1,
                        action_type=ActionType.SEND_ALERT,
                        title="Send alert",
                        instructions="Notify operators and farmers.",
                        rationale="Early warning reduces intake exposure.",
                        simulated=True,
                    ),
                    PlanStep(
                        step_index=2,
                        action_type=ActionType.CLOSE_GATE,
                        title="Simulate gate closure",
                        instructions="Run mock gate-close command after approval.",
                        rationale="Reduce saline inflow in simulation.",
                        simulated=True,
                    ),
                ],
            )

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )
    async def fail_if_planning_reassesses_risk(*args, **kwargs):
        raise AssertionError("planning workflow must not call evaluate_current_risk when risk_bundle is precomputed")

    monkeypatch.setattr(
        "app.orchestration.planning_nodes.evaluate_current_risk",
        fail_if_planning_reassesses_risk,
    )
    monkeypatch.setattr(
        "app.services.agent_planning_service.get_plan_provider",
        lambda provider_name=None, planner=None: StubProvider(),
    )

    first = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )
    assert first.status == "succeeded_pending_human"
    assert first.incident is not None
    assert first.plan_bundle is not None
    assert first.lifecycle_result is not None
    assert first.lifecycle_result.status == "awaiting_human_approval"

    db_session.add(
        SensorReading(
            station_id=goal.station_id,
            recorded_at=datetime.now(UTC),
            salinity_dsm=Decimal("3.80"),
            water_level_m=Decimal("1.55"),
            temperature_c=Decimal("29.40"),
            source="worker-test",
        )
    )
    await db_session.commit()

    second = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )
    assert second.status == "skipped_existing_plan"
    assert second.existing_plan is not None

    plans = (
        await db_session.scalars(
            select(ActionPlan).where(ActionPlan.incident_id == first.incident.id)
        )
    ).all()
    assert len(plans) == 1
    assert plans[0].status == ActionPlanStatus.PENDING_APPROVAL

    approvals = (await db_session.scalars(select(Approval))).all()
    assert len(approvals) == 0

    executions = (await db_session.scalars(select(ActionExecution))).all()
    assert len(executions) == 0


@pytest.mark.asyncio
async def test_active_monitoring_creates_plan_when_risk_is_danger(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-AutoPlan-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Observe salinity without auto planning",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    result = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )

    assert result.status in {
        "succeeded_pending_human",
        "succeeded_plan_created",
        "succeeded_plan_executed",
    }
    assert result.plan_bundle is not None
    plans = (
        await db_session.scalars(
            select(ActionPlan).where(ActionPlan.incident_id == result.incident.id)
        )
    ).all()
    assert len(plans) == 1
    assert plans[0].id == result.plan_bundle.plan.id


@pytest.mark.asyncio
async def test_active_monitoring_skips_cycle_when_latest_reading_already_processed(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-Dedup-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Skip duplicate cycles when no new sensor data arrives",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    first = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )
    assert first.status in {
        "succeeded_pending_human",
        "succeeded_plan_created",
        "succeeded_plan_executed",
    }

    assessments_after_first = (
        await db_session.scalars(
            select(RiskAssessment).where(RiskAssessment.station_id == goal.station_id)
        )
    ).all()
    assert len(assessments_after_first) == 1

    second = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )
    assert second.status == "skipped_no_new_reading"

    assessments_after_second = (
        await db_session.scalars(
            select(RiskAssessment).where(RiskAssessment.station_id == goal.station_id)
        )
    ).all()
    assert len(assessments_after_second) == 1

    db_session.add(
        SensorReading(
            station_id=goal.station_id,
            recorded_at=datetime.now(UTC),
            salinity_dsm=Decimal("3.90"),
            water_level_m=Decimal("1.62"),
            temperature_c=Decimal("29.70"),
            source="worker-test",
        )
    )
    await db_session.commit()

    third = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )
    assert third.status == "skipped_existing_plan"
    assert third.existing_plan is not None

    assessments_after_third = (
        await db_session.scalars(
            select(RiskAssessment).where(RiskAssessment.station_id == goal.station_id)
        )
    ).all()
    assert len(assessments_after_third) == 2

    await db_session.refresh(goal)
    assert goal.last_processed_reading_id == third.risk_bundle.reading.id


def test_should_auto_plan_respects_risk_gate():

    assert should_auto_plan(RiskLevel.WARNING) is False
    assert should_auto_plan(RiskLevel.DANGER) is True
    assert should_auto_plan(RiskLevel.CRITICAL) is True
    assert should_auto_plan(RiskLevel.SAFE) is False
    assert should_auto_plan(None) is False


@pytest.mark.asyncio
async def test_active_monitoring_stops_at_incident_when_risk_is_warning(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-Warning-Gate-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Warn operators but do not create a plan yet",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    db_session.add(
        SensorReading(
            station_id=goal.station_id,
            recorded_at=datetime.now(UTC),
            salinity_dsm=Decimal("2.80"),
            water_level_m=Decimal("1.40"),
            temperature_c=Decimal("29.00"),
            source="worker-test",
        )
    )
    await db_session.commit()

    result = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )

    assert result.status == "succeeded_incident_only"
    assert result.incident is not None
    assert result.plan_bundle is None

    plans = (
        await db_session.scalars(
            select(ActionPlan).where(ActionPlan.incident_id == result.incident.id)
        )
    ).all()
    assert plans == []


@pytest.mark.asyncio
async def test_active_monitoring_uses_lifecycle_graph(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-LifecycleGraph-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Protect irrigation intake from salinity intrusion",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    class StubProvider:
        name = "phase4-lifecycle-provider"

        async def generate_plan(self, *, objective, context):
            return GeneratedActionPlan(
                objective=objective,
                summary="Lifecycle graph compatible plan.",
                assumptions=["Operators monitor the dashboard."],
                steps=[
                    PlanStep(
                        step_index=1,
                        action_type=ActionType.NOTIFY_FARMERS,
                        title="Notify farmers",
                        instructions="Send advisory to avoid intake.",
                        rationale="Early communication reduces exposure.",
                        simulated=True,
                    ),
                    PlanStep(
                        step_index=2,
                        action_type=ActionType.WAIT_SAFE_WINDOW,
                        title="Wait safe window",
                        instructions="Delay intake until conditions improve.",
                        rationale="Low-risk execution policy allows waiting actions.",
                        simulated=True,
                    ),
                ],
            )

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )
    monkeypatch.setattr(
        "app.services.agent_planning_service.get_plan_provider",
        lambda provider_name=None, planner=None: StubProvider(),
    )

    result = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
        settings=Settings(
            reactive_auto_execute_enabled=True,
        ),
    )

    assert result.orchestration_path == "lifecycle_graph"
    assert result.status in {
        "succeeded_plan_executed",
        "succeeded_plan_created",
    }
    assert result.lifecycle_result is not None
    assert result.transition_log is not None
    assert [entry["node"] for entry in result.transition_log] == [
        "classify_risk",
        "approval_gate",
        "execute",
        "feedback",
        "memory_write",
    ]


@pytest.mark.asyncio
async def test_active_monitoring_auto_rejects_stale_pending_approval_for_demo(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-ApprovalTimeout-Demo",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Keep worker progressing during demo timeout",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        is_active=True,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    class StubProvider:
        name = "phase4-timeout-provider"

        async def generate_plan(self, *, objective, context):
            return GeneratedActionPlan(
                objective=objective,
                summary="Plan for approval timeout demonstration.",
                assumptions=["Human reviewer might not respond during demo."],
                steps=[
                    PlanStep(
                        step_index=1,
                        action_type=ActionType.SEND_ALERT,
                        title="Notify operators",
                        instructions="Send warning to control room.",
                        rationale="Immediate visibility is required.",
                        simulated=True,
                    ),
                    PlanStep(
                        step_index=2,
                        action_type=ActionType.CLOSE_GATE,
                        title="Simulate gate closure",
                        instructions="Run simulated closure after approval.",
                        rationale="Provide a mitigation step for higher-risk conditions.",
                        simulated=True,
                    ),
                ],
            )

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )
    monkeypatch.setattr(
        "app.services.agent_planning_service.get_plan_provider",
        lambda provider_name=None, planner=None: StubProvider(),
    )

    first = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
        settings=Settings(
            reactive_auto_execute_enabled=True,
            active_monitoring_approval_timeout_minutes=1,
            active_monitoring_approval_timeout_action="auto_reject",
        ),
    )
    assert first.status == "succeeded_pending_human"
    assert first.plan_bundle is not None

    stale_plan = first.plan_bundle.plan
    stale_plan.created_at = datetime.now(UTC) - timedelta(minutes=5)
    stale_plan.updated_at = datetime.now(UTC) - timedelta(minutes=5)
    await db_session.commit()

    db_session.add(
        SensorReading(
            station_id=goal.station_id,
            recorded_at=datetime.now(UTC),
            salinity_dsm=Decimal("3.95"),
            water_level_m=Decimal("1.60"),
            temperature_c=Decimal("29.55"),
            source="worker-test",
        )
    )
    await db_session.commit()

    second = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
        settings=Settings(
            reactive_auto_execute_enabled=True,
            active_monitoring_approval_timeout_minutes=1,
            active_monitoring_approval_timeout_action="auto_reject",
        ),
    )

    assert second.status == "succeeded_pending_human"
    assert second.plan_bundle is not None
    assert second.plan_bundle.plan.id != stale_plan.id

    refreshed_stale = await db_session.get(ActionPlan, stale_plan.id)
    assert refreshed_stale is not None
    assert refreshed_stale.status == ActionPlanStatus.REJECTED

    approvals = (await db_session.scalars(select(Approval))).all()
    timeout_approvals = [
        item for item in approvals if item.decided_by_name == "approval-timeout-guard"
    ]
    assert timeout_approvals
