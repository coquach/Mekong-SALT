"""Tests for Phase 3 run tracing and observation snapshots."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.enums import ActionType, StationStatus
from app.models.goal import MonitoringGoal
from app.models.sensor import SensorReading, SensorStation
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep
from app.schemas.risk import RiskEvaluationFilters
from app.services.active_monitoring_service import run_monitoring_goal_cycle
from app.services.agent_trace_service import normalize_agent_run_trace
from app.services.risk_service import evaluate_current_risk


@pytest.mark.asyncio
async def test_agent_plans_route_removed(client):
    response = await client.get("/api/v1/agent/plans")
    assert response.status_code == 404


def test_normalize_agent_run_trace_produces_stable_shape():
    normalized = normalize_agent_run_trace(
        {
            "incident_decision": "not-a-dict",
            "plan_decision": {
                "decision": "created",
                "reason": None,
                "action_plan_id": 123,
                "validation": {
                    "is_valid": True,
                    "errors": ["one", None, "two"],
                    "warnings": "ignore-me",
                },
            },
            "retrieval_trace": {
                "total_evidence": "4",
                "source_counts": {"rag": "3", "bad": "skip"},
                "top_citations": [
                    {
                        "citation": "Doc A",
                        "source": "rag",
                        "score": "0.92",
                        "rank": 1,
                    },
                    "ignored-entry",
                ],
            },
            "planning_transition_log": [
                {"node": "observe", "status": "completed"},
                "bad-entry",
            ],
        }
    )

    assert normalized["incident_decision"] == {"decision": None, "reason": None}
    assert normalized["plan_decision"]["action_plan_id"] == "123"
    assert normalized["plan_decision"]["validation"]["errors"] == ["one", "two"]
    assert normalized["plan_decision"]["validation"]["warnings"] == []
    assert normalized["retrieval_trace"]["total_evidence"] == 4
    assert normalized["retrieval_trace"]["source_counts"] == {"rag": 3}
    assert normalized["retrieval_trace"]["top_citations"][0]["citation"] == "Doc A"
    assert normalized["planning_transition_log"][0]["node"] == "observe"
    assert normalized["operator_summary"] is not None


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
        condition_summary="stubbed trace weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


@pytest.mark.asyncio
async def test_risk_run_trace_records_snapshot_and_incident_skip_reason(
    client,
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    safe_station = SensorStation(
        region=seeded_sensor_data["region"],
        code=f"TEST-STATION-SAFE-{uuid4().hex[:6]}",
        name="Safe Station",
        station_type="salinity-water-level",
        status=StationStatus.ACTIVE,
        latitude=Decimal("10.300001"),
        longitude=Decimal("106.300001"),
    )
    safe_reading = SensorReading(
        station=safe_station,
        recorded_at=datetime.now(UTC) - timedelta(minutes=5),
        salinity_dsm=Decimal("0.80"),
        water_level_m=Decimal("1.05"),
        temperature_c=Decimal("27.00"),
    )
    db_session.add_all([safe_station, safe_reading])
    await db_session.commit()

    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps="1.20",
            tide_level_m="0.70",
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    bundle = await evaluate_current_risk(
        db_session,
        filters=RiskEvaluationFilters(station_code=safe_station.code),
        redis_manager=None,
        trigger_source="monitoring.worker.observe_risk",
    )
    run_id = bundle.run_id
    assert run_id is not None

    run_response = await client.get(f"/api/v1/agent/runs/{run_id}")
    assert run_response.status_code == 200
    run_body = run_response.json()["data"]

    assert run_body["status"] == "succeeded"
    assert run_body["trigger_source"] == "monitoring.worker.observe_risk"
    assert run_body["trace"]["incident_decision"]["decision"] == "skipped"
    assert "below incident threshold" in run_body["trace"]["incident_decision"]["reason"]
    assert run_body["trace"]["plan_decision"]["decision"] == "not_applicable"
    assert run_body["observation_snapshot"] is not None
    assert run_body["observation_snapshot"]["reading_id"] == str(safe_reading.id)


@pytest.mark.asyncio
async def test_monitoring_plan_run_trace_records_plan_decision_and_snapshot(
    client,
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    class StubProvider:
        name = "trace-stub-provider"

        async def generate_plan(self, *, objective, context):
            return GeneratedActionPlan(
                objective=objective,
                summary="Plan with clear trace output.",
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
        lambda provider_name=None: StubProvider(),
    )

    goal = MonitoringGoal(
        name="Trace-Reactive-Goal",
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
    assert result.plan_bundle is not None
    run_id = result.plan_bundle.run_id
    plan_id = str(result.plan_bundle.plan.id)

    run_response = await client.get(f"/api/v1/agent/runs/{run_id}")
    assert run_response.status_code == 200
    run_body = run_response.json()["data"]

    assert run_body["status"] == "succeeded"
    assert run_body["trigger_source"] == "monitoring.worker.auto_plan"
    assert run_body["trace"]["plan_decision"]["decision"] == "created"
    assert run_body["trace"]["plan_decision"]["action_plan_id"] == plan_id
    assert run_body["trace"]["incident_decision"]["decision"] in {"created", "existing", "provided"}
    assert run_body["observation_snapshot"] is not None
    assert run_body["observation_snapshot"]["source"] == "plan.pre_decision"
