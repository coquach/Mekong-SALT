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
                    {
                        "citation": "{'type': 'knowledge_document', 'source_uri': 'mekong-salt://samples/document/rag_samples/guideline/sensor_confidence_and_calibration_notes-md', 'document_id': 'b9c42c96-d4ab-4832-802c-9683d80a6b2d', 'chunk_id': '62746a65-cb40-45b1-ba22-6938b489726d', 'title': 'Sensor Confidence And Calibration Notes'}",
                        "score": "7.65",
                        "rank": 2,
                    },
                    {
                        "citation": "{'type': 'memory_case', 'memory_case_id': 'd25f85d1-4f1a-4b1a-8ec8-3d4f9b8d0b11', 'incident_id': 'c2ef2caa-3cb2-4c0f-8d5d-7fe7b5f0b0aa', 'plan_id': '8f5a3c75-23c0-4da2-b5c6-77b9f8edab87', 'execution_id': None, 'occurred_at': '2026-04-19T04:21:28.394991Z'}",
                        "score": "6.10",
                        "rank": 3,
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
    assert normalized["retrieval_trace"]["top_citations"][1]["citation"] == "Sensor Confidence And Calibration Notes"
    assert normalized["retrieval_trace"]["top_citations"][1]["source"] == "knowledge_document"
    assert normalized["retrieval_trace"]["top_citations"][1]["source_uri"] == "mekong-salt://samples/document/rag_samples/guideline/sensor_confidence_and_calibration_notes-md"
    assert normalized["retrieval_trace"]["top_citations"][2]["source"] == "memory_case"
    assert normalized["retrieval_trace"]["top_citations"][2]["memory_case_id"] == "d25f85d1-4f1a-4b1a-8ec8-3d4f9b8d0b11"
    assert normalized["planning_transition_log"][0]["node"] == "observe"
    assert normalized["operator_summary"] is not None
    assert normalized["execution_graph"]["graph_type"] == "planning"
    assert normalized["execution_graph"]["status"] == "pending"
    assert normalized["execution_graph"]["current_node"] == "assess_risk"
    assert normalized["execution_graph"]["nodes"][0]["id"] == "observe"


def test_normalize_agent_run_trace_uses_latest_planning_summary():
    normalized = normalize_agent_run_trace(
        {
            "planning_transition_log": [
                {
                    "node": "observe",
                    "status": "completed",
                    "details": {"objective": "Protect irrigation water quality"},
                },
                {
                    "node": "assess_risk",
                    "status": "completed",
                    "details": {
                        "risk_level": "warning",
                        "summary": "Risk evaluation found elevated salinity pressure.",
                    },
                },
            ],
        }
    )

    assert normalized["execution_graph"]["summary"] == "Risk evaluation found elevated salinity pressure."
    assert normalized["execution_graph"]["nodes"][1]["summary"] == "Risk evaluation found elevated salinity pressure."


def test_normalize_agent_run_trace_builds_vietnamese_stage_summaries():
    normalized = normalize_agent_run_trace(
        {
            "planning_transition_log": [
                {
                    "node": "observe",
                    "status": "completed",
                    "details": {
                        "objective": "Bảo vệ chất lượng nước tưới tại cửa lấy nước Gò Công Đông.",
                    },
                },
                {
                    "node": "assess_risk",
                    "status": "completed",
                    "details": {
                        "risk_level": "critical",
                    },
                },
                {
                    "node": "retrieve_context",
                    "status": "completed",
                    "details": {
                        "gate_targets": 4,
                        "evidence_count": 8,
                        "retrieved_context_keys": ["assessment", "reading", "weather_snapshot"],
                    },
                },
                {
                    "node": "draft_plan",
                    "status": "completed",
                    "details": {
                        "step_count": 4,
                        "confidence_score": 1.0,
                    },
                },
                {
                    "node": "validate_plan",
                    "status": "completed",
                    "details": {
                        "is_valid": True,
                        "error_count": 0,
                        "warning_count": 0,
                    },
                },
            ],
        }
    )

    nodes = normalized["execution_graph"]["nodes"]

    assert nodes[0]["summary"] == "Quan sát bối cảnh đầu vào để bám mục tiêu: Bảo vệ chất lượng nước tưới tại cửa lấy nước Gò Công Đông."
    assert nodes[1]["summary"] == "Rủi ro được đánh giá ở mức rất nguy cấp."
    assert "Thu được 8 bằng chứng." in nodes[2]["summary"]
    assert "Phác thảo 4 bước hành động." in nodes[3]["summary"]
    assert "không phát hiện lỗi an toàn đáng chú ý" in nodes[4]["summary"]


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
    assert "ngưỡng tạo sự cố" in run_body["trace"]["incident_decision"]["reason"]
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
        lambda provider_name=None, planner=None: StubProvider(),
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
