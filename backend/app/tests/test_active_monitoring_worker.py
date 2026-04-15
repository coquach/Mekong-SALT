"""Tests for Phase 4 active monitoring worker behavior."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.action import ActionExecution, ActionPlan
from app.models.approval import Approval
from app.models.goal import MonitoringGoal
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep
from app.models.enums import ActionPlanStatus, ActionType
from app.services.active_monitoring_service import run_monitoring_goal_cycle


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
        auto_plan_enabled=True,
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
        lambda provider_name=None: StubProvider(),
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
    assert first.reactive_result is not None
    assert first.reactive_result.status == "awaiting_human_approval"

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
async def test_active_monitoring_dry_run_skips_plan_creation(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    goal = MonitoringGoal(
        name="Phase4-DryRun-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Observe salinity without auto planning",
        provider="mock",
        warning_threshold_dsm=Decimal("2.50"),
        critical_threshold_dsm=Decimal("4.00"),
        evaluation_interval_minutes=1,
        auto_plan_enabled=True,
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
        mode="dry_run",
        redis_manager=None,
    )

    assert result.status == "dry_run_observed"
    assert result.plan_bundle is None
    plans = (await db_session.scalars(select(ActionPlan))).all()
    assert plans == []
