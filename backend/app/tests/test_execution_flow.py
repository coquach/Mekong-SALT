"""Tests for reactive execution and removed manual workflow endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, IncidentStatus, RiskLevel, TrendDirection
from app.models.domain_event import DomainEvent
from app.models.incident import Incident
from app.models.goal import MonitoringGoal
from app.models.risk import RiskAssessment
from app.models.sensor import SensorReading
from app.models.weather import WeatherSnapshot
from app.schemas.agent import GeneratedActionPlan, PlanStep
from app.orchestration.lifecycle_graph import advance_plan_with_lifecycle_graph
from app.services.active_monitoring_service import run_monitoring_goal_cycle
from app.services.replan_service import REPLAN_REQUEST_EVENT_TYPE


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
):
    reading = seeded_sensor_data["reading_a_latest"]
    station = seeded_sensor_data["station_b"]
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
        summary="Approved simulated execution plan.",
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
                "action_type": ActionType.WAIT_SAFE_WINDOW.value,
                "priority": 2,
                "title": "Wait for safe intake window",
                "instructions": "Delay intake until conditions are safer.",
                "rationale": "Low-risk auto-execution only allows informational/safe-window actions.",
                "simulated": True,
            },
        ],
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    lifecycle_result = await advance_plan_with_lifecycle_graph(
        db_session,
        plan=plan,
        settings=Settings(),
    )

    assert lifecycle_result.status == "executed"
    assert lifecycle_result.execution_bundle is not None
    assert plan.status == ActionPlanStatus.SIMULATED

    execution_bundle = lifecycle_result.execution_bundle
    assert len(execution_bundle.executions) == 2
    assert execution_bundle.feedback.outcome_class == "success"
    assert execution_bundle.feedback.status == "improved"
    assert execution_bundle.feedback.replan_recommended is False
    assert len(execution_bundle.decision_logs) == 3

    logs_response = await client.get(
        "/api/v1/actions/logs",
        params={"plan_id": str(plan.id)},
    )

    assert logs_response.status_code == 200
    logs_body = logs_response.json()["data"]
    batch_response = await client.get(f"/api/v1/execution-batches/{lifecycle_result.execution_bundle.batch.id}")
    assert batch_response.status_code == 200
    batch_body = batch_response.json()["data"]
    assert batch_body["execution_graph"]["graph_type"] == "execution_batch"
    assert batch_body["execution_graph"]["status"] == "completed"
    assert logs_body["count"] == 2
    assert all(item["decision_log"] is not None for item in logs_body["items"])


@pytest.mark.asyncio
async def test_reactive_execution_emits_replan_request_event_on_partial_success(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    reading = seeded_sensor_data["reading_a_latest"]
    station = seeded_sensor_data["station_b"]
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

    incident = Incident(
        region_id=region.id,
        station_id=station.id,
        risk_assessment_id=assessment.id,
        title="Execution replan incident",
        description="Incident used to verify replan request emission.",
        severity=RiskLevel.DANGER,
        status=IncidentStatus.OPEN,
        source="test",
        evidence={"source": "test"},
        opened_at=datetime.now(UTC),
        created_by="test-suite",
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    plan = ActionPlan(
        region_id=region.id,
        risk_assessment_id=assessment.id,
        incident_id=incident.id,
        status=ActionPlanStatus.APPROVED,
        objective="Protect irrigation water quality",
        generated_by="test-suite",
        model_provider="mock",
        summary="Approved simulated execution plan.",
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
                "action_type": ActionType.WAIT_SAFE_WINDOW.value,
                "priority": 2,
                "title": "Wait for safe intake window",
                "instructions": "Delay intake until conditions are safer.",
                "rationale": "Low-risk auto-execution only allows informational/safe-window actions.",
                "simulated": True,
            },
        ],
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    db_session.add(
        SensorReading(
            station_id=station.id,
            recorded_at=datetime.now(UTC),
            salinity_dsm=reading.salinity_dsm,
            water_level_m=Decimal("1.55"),
            temperature_c=Decimal("29.40"),
            source="worker-test",
        )
    )
    await db_session.commit()

    monkeypatch.setattr(
        "app.services.replan_service.get_settings",
        lambda: Settings(active_monitoring_feedback_replan_max_attempts=1),
    )
    class _NoopRedisManager:
        async def publish_signal(self, channel, payload=None):
            _ = (channel, payload)
            return None

    monkeypatch.setattr(
        "app.services.domain_event_service._get_signal_redis_manager",
        lambda: _NoopRedisManager(),
    )

    result = await advance_plan_with_lifecycle_graph(
        db_session,
        plan=plan,
        settings=Settings(reactive_auto_execute_enabled=True),
    )

    assert result.status == "executed"
    assert result.execution_bundle is not None
    assert result.execution_bundle.feedback.outcome_class == "partial_success"
    assert result.execution_bundle.feedback.replan_recommended is True

    replan_events = (
        await db_session.scalars(
            select(DomainEvent).where(DomainEvent.event_type == REPLAN_REQUEST_EVENT_TYPE)
        )
    ).all()
    matching_replan_events = [event for event in replan_events if event.payload["action_plan_id"] == str(plan.id)]
    assert len(matching_replan_events) >= 1
    assert matching_replan_events[-1].payload["feedback_outcome_class"] == "partial_success"


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
    assert first_data["batch"]["execution_job_id"] == first_data["batch"]["id"]
    assert first_data["batch"]["execution_job_status"] == first_data["batch"]["status"]
    assert len(first_data["executions"]) == 2
    assert all(item["execution_job_id"] == first_data["batch"]["id"] for item in first_data["executions"])
    batch_id = first_data["batch"]["id"]

    second = await client.post(
        f"/api/v1/execution-batches/plans/{plan.id}/simulate",
        json={"idempotency_key": "phase6-batch-1"},
    )
    assert second.status_code == 200
    second_data = second.json()["data"]
    assert second_data["idempotent_replay"] is True
    assert second_data["batch"]["id"] == batch_id
    assert second_data["batch"]["execution_job_id"] == batch_id
    assert second_data["batch"]["step_count"] == 2

    detail = await client.get(f"/api/v1/execution-batches/{batch_id}")
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["batch"]["id"] == batch_id
    assert detail_data["batch"]["execution_job_id"] == batch_id
    assert detail_data["count"] == 2

    evaluate_feedback = await client.post(f"/api/v1/feedback/execution-batches/{batch_id}/evaluate")
    assert evaluate_feedback.status_code == 200
    evaluate_payload = evaluate_feedback.json()["data"]
    assert evaluate_payload["evaluation"]["batch_id"] == batch_id
    assert evaluate_payload["before_snapshot"]["snapshot_kind"] == "before"
    assert evaluate_payload["after_snapshot"]["snapshot_kind"] == "after"

    latest_feedback = await client.get(f"/api/v1/feedback/execution-batches/{batch_id}/latest")
    assert latest_feedback.status_code == 200
    latest_payload = latest_feedback.json()["data"]
    assert latest_payload["evaluation"]["id"] == evaluate_payload["evaluation"]["id"]
    assert latest_payload["feedback"]["outcome_class"] == evaluate_payload["feedback"]["outcome_class"]
