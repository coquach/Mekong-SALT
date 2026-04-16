"""Tests for lifecycle LangGraph orchestration after plan generation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, RiskLevel, TrendDirection
from app.models.risk import RiskAssessment
from app.orchestration.lifecycle_graph import advance_plan_with_lifecycle_graph


def _build_plan_steps() -> list[dict[str, object]]:
    return [
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
            "title": "Wait for safer intake window",
            "instructions": "Delay intake until tide risk reduces.",
            "rationale": "Low-risk policy allows safe-window delay.",
            "simulated": True,
        },
    ]


async def _persist_plan_with_assessment(
    db_session,
    *,
    seeded_sensor_data,
    risk_level: RiskLevel,
) -> ActionPlan:
    reading = seeded_sensor_data["reading_a_latest"]
    station = seeded_sensor_data["station_a"]
    region = seeded_sensor_data["region"]

    assessment = RiskAssessment(
        region_id=region.id,
        station_id=station.id,
        based_on_reading_id=reading.id,
        based_on_weather_id=None,
        assessed_at=datetime.now(UTC),
        risk_level=risk_level,
        salinity_dsm=reading.salinity_dsm,
        trend_direction=TrendDirection.RISING,
        trend_delta_dsm=Decimal("0.40"),
        rule_version="v1",
        summary="Lifecycle graph test assessment",
        rationale={"source": "test"},
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    plan = ActionPlan(
        region_id=region.id,
        risk_assessment_id=assessment.id,
        incident_id=None,
        status=ActionPlanStatus.PENDING_APPROVAL,
        objective="Protect irrigation water quality",
        generated_by="test-suite",
        model_provider="mock",
        summary="Lifecycle graph test plan.",
        assumptions={"items": ["Operators are available"]},
        plan_steps=_build_plan_steps(),
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.mark.asyncio
async def test_lifecycle_graph_high_risk_requires_human_approval(
    db_session,
    seeded_sensor_data,
):
    plan = await _persist_plan_with_assessment(
        db_session,
        seeded_sensor_data=seeded_sensor_data,
        risk_level=RiskLevel.DANGER,
    )

    result = await advance_plan_with_lifecycle_graph(
        db_session,
        plan=plan,
        settings=Settings(),
    )

    assert result.status == "awaiting_human_approval"
    assert result.approval is None
    assert result.execution_bundle is None
    assert result.memory_log is not None
    assert result.memory_log.details["approval_status"] == "awaiting_human_approval"

    node_names = [entry["node"] for entry in (result.transition_log or [])]
    assert node_names == [
        "classify_risk",
        "approval_gate",
        "execute",
        "feedback",
        "memory_write",
    ]


@pytest.mark.asyncio
async def test_lifecycle_graph_low_risk_auto_executes(
    db_session,
    seeded_sensor_data,
):
    plan = await _persist_plan_with_assessment(
        db_session,
        seeded_sensor_data=seeded_sensor_data,
        risk_level=RiskLevel.WARNING,
    )

    result = await advance_plan_with_lifecycle_graph(
        db_session,
        plan=plan,
        settings=Settings(),
    )

    assert result.status == "executed"
    assert result.approval is not None
    assert result.execution_bundle is not None
    assert result.plan.status == ActionPlanStatus.SIMULATED
    assert result.memory_log is not None
    assert result.memory_log.details["execution_status"] == "executed"
