"""Tests for reactive execution and removed manual workflow endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, RiskLevel, TrendDirection
from app.models.goal import MonitoringGoal
from app.models.risk import RiskAssessment
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
                    action_type=ActionType.WAIT_SAFE_WINDOW,
                    title="Wait for safe intake window",
                    instructions="Delay intake until conditions are safer.",
                    rationale="Low-risk auto-execution only allows informational/safe-window actions.",
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
            wind_speed_mps="4.20",
            tide_level_m="1.10",
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
        station_id=seeded_sensor_data["station_b"].id,
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


@pytest.mark.asyncio
async def test_execute_simulated_returns_batch_transaction_and_replays_idempotency(
    client,
    db_session,
    seeded_sensor_data,
):
    reading = seeded_sensor_data["reading_a_latest"]
    station = seeded_sensor_data["station_a"]
    region = seeded_sensor_data["region"]

    assessment = RiskAssessment(
        region_id=region.id,
        station_id=station.id,
        based_on_reading_id=reading.id,
        based_on_weather_id=None,
        assessed_at=datetime.now(UTC),
        risk_level=RiskLevel.DANGER,
        salinity_dsm=reading.salinity_dsm,
        trend_direction=TrendDirection.RISING,
        trend_delta_dsm=Decimal("0.60"),
        rule_version="v1",
        summary="Danger risk requires simulated execution.",
        rationale={"source": "test"},
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    plan = ActionPlan(
        region_id=region.id,
        risk_assessment_id=assessment.id,
        incident_id=None,
        status=ActionPlanStatus.APPROVED,
        objective="Protect irrigation water quality",
        generated_by="test-suite",
        model_provider="mock",
        summary="Simulated execution transaction for FE batch view.",
        assumptions={"items": ["Operators are available"]},
        plan_steps=[
            {
                "step_index": 1,
                "action_type": ActionType.NOTIFY_FARMERS.value,
                "priority": 1,
                "title": "Notify farmers",
                "instructions": "Send advisory to avoid intake.",
                "rationale": "Communication reduces exposure.",
                "simulated": True,
            },
            {
                "step_index": 2,
                "action_type": ActionType.CLOSE_GATE_SIMULATED.value,
                "priority": 2,
                "title": "Simulate gate closure",
                "instructions": "Model temporary gate closure.",
                "rationale": "Mitigate saline inflow in simulation.",
                "simulated": True,
            },
        ],
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    first = await client.post(
        f"/api/v1/execution-batches/plans/{plan.id}/simulate",
        json={"idempotency_key": "phase6-batch-1"},
    )
    assert first.status_code == 200
    first_data = first.json()["data"]
    assert first_data["idempotent_replay"] is False
    assert first_data["batch"]["plan_id"] == str(plan.id)
    assert first_data["batch"]["step_count"] == 2
    assert len(first_data["executions"]) == 2
    batch_id = first_data["batch"]["id"]

    second = await client.post(
        f"/api/v1/execution-batches/plans/{plan.id}/simulate",
        json={"idempotency_key": "phase6-batch-1"},
    )
    assert second.status_code == 200
    second_data = second.json()["data"]
    assert second_data["idempotent_replay"] is True
    assert second_data["batch"]["id"] == batch_id
    assert second_data["batch"]["step_count"] == 2

    detail = await client.get(f"/api/v1/execution-batches/{batch_id}")
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["batch"]["id"] == batch_id
    assert detail_data["count"] == 2
