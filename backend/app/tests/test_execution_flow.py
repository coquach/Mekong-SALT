"""Tests for simulated execution and feedback flow."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType
from app.models.sensor import SensorReading
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep


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
            assumptions=["Operators are available."],
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


class _DraftPlanProvider:
    name = "stub-provider"

    async def generate_plan(self, *, objective, context):
        return GeneratedActionPlan(
            objective=objective,
            summary="Notify and wait only.",
            assumptions=["Operators are available."],
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
                    title="Wait for safer tide window",
                    instructions="Pause intake until conditions improve.",
                    rationale="Avoid saline intake during peak pressure.",
                    simulated=True,
                ),
            ],
        )


@pytest.mark.asyncio
async def test_execute_simulated_rejects_draft_plan(
    client, seeded_sensor_data, monkeypatch
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
        lambda provider_name=None: _DraftPlanProvider(),
    )

    plan_response = await client.post(
        "/api/v1/agent/plan",
        json={
            "station_code": seeded_sensor_data["station_a"].code,
            "objective": "Protect irrigation water quality",
        },
    )
    plan_id = plan_response.json()["data"]["plan"]["id"]

    execute_response = await client.post(
        "/api/v1/agent/execute-simulated",
        json={"action_plan_id": plan_id},
    )

    assert execute_response.status_code == 400
    body = execute_response.json()
    assert body["error"]["code"] == "action_plan_not_validated"


@pytest.mark.asyncio
async def test_execute_simulated_persists_executions_feedback_and_logs(
    client, db_session, seeded_sensor_data, monkeypatch
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

    plan_response = await client.post(
        "/api/v1/agent/plan",
        json={
            "station_code": seeded_sensor_data["station_a"].code,
            "objective": "Protect irrigation water quality",
        },
    )

    plan_body = plan_response.json()["data"]["plan"]
    plan_id = plan_body["id"]
    assert plan_body["status"] == ActionPlanStatus.VALIDATED.value

    follow_up_reading = SensorReading(
        station_id=seeded_sensor_data["station_a"].id,
        recorded_at=datetime.now(UTC),
        salinity_dsm=Decimal("2.40"),
        water_level_m=Decimal("1.30"),
        temperature_c=Decimal("28.10"),
    )
    db_session.add(follow_up_reading)
    await db_session.commit()

    execute_response = await client.post(
        "/api/v1/agent/execute-simulated",
        json={"action_plan_id": plan_id},
    )

    assert execute_response.status_code == 200
    execute_body = execute_response.json()["data"]
    assert execute_body["plan"]["status"] == ActionPlanStatus.SIMULATED.value
    assert len(execute_body["executions"]) == 2
    assert execute_body["feedback"]["status"] == "improved"
    assert len(execute_body["decision_logs"]) == 3

    logs_response = await client.get(
        "/api/v1/actions/logs",
        params={"plan_id": plan_id},
    )

    assert logs_response.status_code == 200
    logs_body = logs_response.json()["data"]
    assert logs_body["count"] == 2
    assert all(item["decision_log"] is not None for item in logs_body["items"])

    persisted_plan = await db_session.get(ActionPlan, UUID(plan_id))
    assert persisted_plan is not None
    assert persisted_plan.status == ActionPlanStatus.SIMULATED
