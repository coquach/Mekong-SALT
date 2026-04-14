"""Tests for Monitoring Goals CRUD and run-once flow."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, RiskLevel, TrendDirection
from app.models.risk import RiskAssessment
from app.models.sensor import SensorReading


@pytest.mark.asyncio
async def test_monitoring_goal_create_update_and_run_once_consistent(
    client,
    seeded_sensor_data,
    monkeypatch,
):
    create_payload = {
        "name": "TienGiang-Salinity-Goal-01",
        "description": "Keep irrigation salinity below warning",
        "region_id": str(seeded_sensor_data["region"].id),
        "station_id": str(seeded_sensor_data["station_a"].id),
        "objective": "Keep salinity below 2.5 dS/m",
        "provider": "mock",
        "thresholds": {
            "warning_threshold_dsm": "2.50",
            "critical_threshold_dsm": "4.00",
        },
        "evaluation_interval_minutes": 15,
        "is_active": True,
    }
    create_response = await client.post("/api/v1/goals", json=create_payload)

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    goal_id = created["id"]
    assert created["thresholds"]["warning_threshold_dsm"] == "2.50"
    assert created["evaluation_interval_minutes"] == 15
    assert created["is_active"] is True

    update_payload = {
        "objective": "Keep salinity below 2.3 dS/m",
        "thresholds": {
            "warning_threshold_dsm": "2.30",
            "critical_threshold_dsm": "3.80",
        },
        "evaluation_interval_minutes": 20,
    }
    update_response = await client.patch(f"/api/v1/goals/{goal_id}", json=update_payload)

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["objective"] == "Keep salinity below 2.3 dS/m"
    assert updated["thresholds"]["warning_threshold_dsm"] == "2.30"
    assert updated["thresholds"]["critical_threshold_dsm"] == "3.80"
    assert updated["evaluation_interval_minutes"] == 20

    async def fake_generate_agent_plan(session, *, payload, redis_manager):
        reading = (
            await session.scalars(
                select(SensorReading)
                .options(selectinload(SensorReading.station))
                .where(SensorReading.id == seeded_sensor_data["reading_a_latest"].id)
            )
        ).first()
        assert reading is not None

        assessment = RiskAssessment(
            region_id=payload.region_id,
            station_id=payload.station_id,
            based_on_reading_id=reading.id,
            based_on_weather_id=None,
            assessed_at=datetime.now(UTC),
            risk_level=RiskLevel.WARNING,
            salinity_dsm=reading.salinity_dsm,
            trend_direction=TrendDirection.STABLE,
            trend_delta_dsm=Decimal("0.00"),
            rule_version="v1",
            summary="Stubbed assessment for run-once.",
            rationale={"source": "test"},
        )
        session.add(assessment)
        await session.flush()

        plan = ActionPlan(
            region_id=assessment.region_id,
            risk_assessment_id=assessment.id,
            incident_id=None,
            status=ActionPlanStatus.PENDING_APPROVAL,
            objective=payload.objective,
            generated_by="test-goal-runner",
            model_provider=payload.provider or "mock",
            summary="Stubbed plan for run-once.",
            assumptions={"source": "test"},
            plan_steps=[
                {
                    "step_index": 1,
                    "action_type": "notify-farmers",
                    "title": "Notify operators",
                    "instructions": "Send warning notice",
                    "rationale": "Protect irrigation intake",
                    "simulated": True,
                }
            ],
            validation_result={"is_valid": True, "errors": [], "warnings": []},
        )
        session.add(plan)
        await session.commit()
        await session.refresh(assessment)
        await session.refresh(plan)

        return SimpleNamespace(
            risk_bundle=SimpleNamespace(
                assessment=assessment,
                reading=reading,
                weather_snapshot=None,
            ),
            plan=plan,
            provider_name=plan.model_provider,
        )

    monkeypatch.setattr(
        "app.services.goals_service.generate_agent_plan",
        fake_generate_agent_plan,
    )

    run_once_response_1 = await client.post(f"/api/v1/goals/{goal_id}/run-once", json={})
    assert run_once_response_1.status_code == 200
    run_once_data_1 = run_once_response_1.json()["data"]

    assert run_once_data_1["goal"]["id"] == goal_id
    assert run_once_data_1["goal"]["objective"] == "Keep salinity below 2.3 dS/m"
    assert run_once_data_1["goal"]["thresholds"]["warning_threshold_dsm"] == "2.30"
    assert run_once_data_1["goal"]["evaluation_interval_minutes"] == 20
    assert run_once_data_1["goal"]["is_active"] is True
    assert run_once_data_1["goal"]["last_run_status"] == "succeeded"
    assert run_once_data_1["result"]["plan"]["objective"] == "Keep salinity below 2.3 dS/m"

    run_once_response_2 = await client.post(f"/api/v1/goals/{goal_id}/run-once", json={})
    assert run_once_response_2.status_code == 200
    run_once_data_2 = run_once_response_2.json()["data"]

    assert run_once_data_2["goal"]["thresholds"] == run_once_data_1["goal"]["thresholds"]
    assert (
        run_once_data_2["goal"]["evaluation_interval_minutes"]
        == run_once_data_1["goal"]["evaluation_interval_minutes"]
    )
    assert run_once_data_2["goal"]["is_active"] == run_once_data_1["goal"]["is_active"]
    assert run_once_data_2["result"]["plan"]["objective"] == run_once_data_1["result"]["plan"]["objective"]


@pytest.mark.asyncio
async def test_monitoring_goal_rejects_invalid_thresholds(client, seeded_sensor_data):
    invalid_payload = {
        "name": "Invalid-Goal-Thresholds",
        "region_id": str(seeded_sensor_data["region"].id),
        "station_id": str(seeded_sensor_data["station_a"].id),
        "objective": "Protect irrigation",
        "thresholds": {
            "warning_threshold_dsm": "3.50",
            "critical_threshold_dsm": "3.00",
        },
        "evaluation_interval_minutes": 10,
        "is_active": True,
    }

    response = await client.post("/api/v1/goals", json=invalid_payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
