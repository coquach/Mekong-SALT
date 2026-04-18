"""Tests for the agent-assisted planning layer."""

from datetime import UTC, datetime
from decimal import Decimal

from app.agents.policy_guard import validate_generated_plan
from app.models.enums import ActionPlanStatus, ActionType, RiskLevel
from app.models.weather import WeatherSnapshot
import pytest
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanStep
from app.services.agent_planning_service import generate_agent_plan


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
        condition_summary="stubbed planning weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


def test_policy_guard_rejects_critical_plan_without_hydraulic_mitigation():
    plan = GeneratedActionPlan(
        objective="Protect irrigation water quality",
        summary="Notify and wait only.",
        assumptions=["Operators can communicate immediately."],
        steps=[
            PlanStep(
                step_index=1,
                action_type=ActionType.NOTIFY_FARMERS,
                title="Notify farmers",
                instructions="Send an urgent advisory message.",
                rationale="Critical salinity requires immediate communication.",
                simulated=True,
            ),
            PlanStep(
                step_index=2,
                action_type=ActionType.WAIT_SAFE_WINDOW,
                title="Wait for safer tide window",
                instructions="Pause water intake until conditions improve.",
                rationale="Avoid drawing in saline water.",
                simulated=True,
            ),
        ],
    )

    result = validate_generated_plan(plan, risk_level=RiskLevel.CRITICAL)

    assert result.is_valid is False
    assert result.errors


@pytest.mark.asyncio
async def test_agent_planning_service_persists_validated_plan(
    db_session, seeded_sensor_data, monkeypatch
):
    class StubProvider:
        name = "stub-provider"

        async def generate_plan(self, *, objective, context):
            return GeneratedActionPlan(
                objective=objective,
                summary="Protect irrigation canals and communicate promptly.",
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

    bundle = await generate_agent_plan(
        db_session,
        payload=AgentPlanRequest(
            station_code=seeded_sensor_data["station_a"].code,
            objective="Protect irrigation water quality",
        ),
        redis_manager=None,
        trigger_source="test.agent_plan.service",
    )

    assert bundle.plan.status == ActionPlanStatus.PENDING_APPROVAL
    assert bundle.plan.model_provider == "stub-provider"
    assert bundle.plan.validation_result["is_valid"] is True
    assert len(bundle.plan.plan_steps) == 2


@pytest.mark.asyncio
async def test_agent_planning_service_persists_invalid_plan_as_draft(
    db_session, seeded_sensor_data, monkeypatch
):
    class StubProvider:
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

    bundle = await generate_agent_plan(
        db_session,
        payload=AgentPlanRequest(
            station_code=seeded_sensor_data["station_a"].code,
            objective="Protect irrigation water quality",
        ),
        redis_manager=None,
        trigger_source="test.agent_plan.service",
    )

    assert bundle.plan.status == ActionPlanStatus.DRAFT
    assert bundle.plan.validation_result["is_valid"] is False
    assert bundle.plan.validation_result["errors"]
