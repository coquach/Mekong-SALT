"""Tests for reactive execution and removed manual workflow endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType
from app.models.goal import MonitoringGoal
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep
from app.services.active_monitoring_service import run_monitoring_goal_cycle


async def _persist_stub_weather_snapshot(
    session,
    *,
    region_id,
    wind_speed_mps: str,
    tide_level_m: str,
) -> WeatherSnapshot:
    snapshot = WeatherSnapshot(
        region_id=region_id,
        observed_at=datetime.now(UTC),
        wind_speed_mps=Decimal(wind_speed_mps),
        wind_direction_deg=135,
        tide_level_m=Decimal(tide_level_m),
        rainfall_mm=Decimal("0.20"),
        condition_summary="stubbed execution weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


class _ValidatedPlanProvider:
    name = "stub-provider"

    async def generate_plan(self, *, objective, context):
        return GeneratedActionPlan(
            objective=objective,
            summary="Protect irrigation canals with simulated mitigation.",
            assumptions=["Reactive monitoring is enabled."],
            steps=[
                PlanStep(
                    step_index=1,
                    action_type=ActionType.NOTIFY_FARMERS,
                    title="Notify farmers",
                    instructions="Send advisory to avoid intake.",
                    rationale="Communication reduces exposure.",
                    simulated=True,
                ),
                PlanStep(
                    step_index=2,
                    action_type=ActionType.CLOSE_GATE_SIMULATED,
                    title="Simulate gate closure",
                    instructions="Model temporary gate closure.",
                    rationale="Mitigate saline inflow in simulation.",
                    simulated=True,
                ),
            ],
        )


@pytest.mark.asyncio
async def test_manual_workflow_trigger_endpoints_are_not_public(client):
    plan_id = uuid4()

    checks = [
        await client.get("/api/v1/risk/current"),
        await client.post("/api/v1/alerts/evaluate", json={}),
        await client.post("/api/v1/agent/plan", json={}),
        await client.post("/api/v1/agent/execute-simulated", json={}),
        await client.post(f"/api/v1/approvals/plans/{plan_id}", json={"decision": "approved"}),
        await client.post(f"/api/v1/plans/{plan_id}/approve", json={}),
        await client.post(f"/api/v1/plans/{plan_id}/execute-simulated", json={}),
    ]

    assert all(response.status_code == 404 for response in checks)


@pytest.mark.asyncio
async def test_reactive_monitoring_persists_executions_feedback_and_logs(
    client,
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps="5.50",
            tide_level_m="1.70",
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )
    monkeypatch.setattr(
        "app.services.agent_planning_service.get_plan_provider",
        lambda provider_name=None: _ValidatedPlanProvider(),
    )

    goal = MonitoringGoal(
        name="Reactive-Execution-Goal",
        region_id=seeded_sensor_data["region"].id,
        station_id=seeded_sensor_data["station_a"].id,
        objective="Protect irrigation water quality",
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

    result = await run_monitoring_goal_cycle(
        db_session,
        goal=goal,
        mode="active",
        redis_manager=None,
    )

    assert result.status == "succeeded_plan_executed"
    assert result.reactive_result is not None
    assert result.reactive_result.execution_bundle is not None

    plan = await db_session.get(ActionPlan, result.plan_bundle.plan.id)
    assert plan is not None
    assert plan.status == ActionPlanStatus.SIMULATED

    execution_bundle = result.reactive_result.execution_bundle
    assert len(execution_bundle.executions) == 2
    assert execution_bundle.feedback.status == "insufficient_new_observation"
    assert len(execution_bundle.decision_logs) == 3

    logs_response = await client.get(
        "/api/v1/actions/logs",
        params={"plan_id": str(plan.id)},
    )

    assert logs_response.status_code == 200
    logs_body = logs_response.json()["data"]
    assert logs_body["count"] == 2
    assert all(item["decision_log"] is not None for item in logs_body["items"])
