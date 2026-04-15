"""Node-level tests for planning orchestration services."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from app.models.enums import ActionType, RiskLevel, TrendDirection
from app.orchestration.planning_nodes import (
    PlanningNodeServices,
    assess_risk_node,
    draft_plan_node,
    observe_request_node,
    retrieve_context_node,
    validate_plan_node,
)
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanStep
from app.schemas.risk import RiskEvaluationFilters


class _StaticProvider:
    """Simple provider stub returning a predefined plan."""

    name = "test-provider"

    def __init__(self, plan: GeneratedActionPlan) -> None:
        self.plan = plan
        self.calls: list[dict[str, Any]] = []

    async def generate_plan(self, *, objective: str, context: dict[str, Any]) -> GeneratedActionPlan:
        self.calls.append({"objective": objective, "context": context})
        return self.plan


@pytest.mark.asyncio
async def test_observe_request_node_builds_filters_and_default_objective():
    request = AgentPlanRequest(station_code="ST-01")

    result = await observe_request_node({"request": request})

    assert isinstance(result["filters"], RiskEvaluationFilters)
    assert result["filters"].station_code == "ST-01"
    assert result["objective"] == "Protect irrigation water quality and reduce salinity risk."


@pytest.mark.asyncio
async def test_assess_risk_node_skips_when_precomputed_bundle_present(monkeypatch):
    async def should_not_be_called(*args, **kwargs):
        raise AssertionError("evaluate_current_risk must not be called when risk_bundle already exists")

    monkeypatch.setattr(
        "app.orchestration.planning_nodes.evaluate_current_risk",
        should_not_be_called,
    )

    services = PlanningNodeServices(
        session=SimpleNamespace(),
        redis_manager=None,
        provider=SimpleNamespace(),
    )
    result = await assess_risk_node(
        {"risk_bundle": SimpleNamespace()},
        services=services,
    )

    assert result == {}


@pytest.mark.asyncio
async def test_assess_risk_node_calls_risk_service_when_missing_bundle(db_session, monkeypatch):
    fake_bundle = SimpleNamespace(name="bundle")

    async def fake_evaluate(session, *, filters, redis_manager, trigger_source, trigger_payload):
        assert session is db_session
        assert filters.station_code == "ST-02"
        assert redis_manager is None
        assert trigger_source == "agent.plan.workflow"
        assert trigger_payload == {"workflow": "langgraph_planning"}
        return fake_bundle

    monkeypatch.setattr(
        "app.orchestration.planning_nodes.evaluate_current_risk",
        fake_evaluate,
    )

    services = PlanningNodeServices(
        session=db_session,
        redis_manager=None,
        provider=SimpleNamespace(),
    )
    result = await assess_risk_node(
        {"filters": RiskEvaluationFilters(station_code="ST-02")},
        services=services,
    )

    assert result["risk_bundle"] is fake_bundle


@pytest.mark.asyncio
async def test_retrieve_context_node_returns_compact_context(db_session, seeded_sensor_data):
    assessment = SimpleNamespace(
        region_id=seeded_sensor_data["region"].id,
        risk_level=RiskLevel.WARNING,
        trend_direction=TrendDirection.RISING,
        trend_delta_dsm=Decimal("0.40"),
        summary="Warning level reached",
        rationale={"reason": "salinity increased"},
    )
    risk_bundle = SimpleNamespace(
        assessment=assessment,
        reading=seeded_sensor_data["reading_a_latest"],
        weather_snapshot=None,
    )
    provider = _StaticProvider(
        GeneratedActionPlan(
            objective="unused",
            summary="unused",
            assumptions=["unused"],
            steps=[
                PlanStep(
                    step_index=1,
                    action_type=ActionType.SEND_ALERT,
                    title="Alert",
                    instructions="Notify operators",
                    rationale="Fast response",
                    simulated=True,
                )
            ],
        )
    )
    services = PlanningNodeServices(
        session=db_session,
        redis_manager=None,
        provider=provider,
    )

    result = await retrieve_context_node({"risk_bundle": risk_bundle}, services=services)

    context = result["retrieved_context"]
    assert context["region"]["code"] == seeded_sensor_data["region"].code
    assert context["assessment"]["risk_level"] == "warning"
    assert context["assessment"]["trend_direction"] == "rising"
    assert context["weather_snapshot"] is None


@pytest.mark.asyncio
async def test_draft_and_validate_nodes_work_with_rule_policy():
    draft_plan = GeneratedActionPlan(
        objective="Protect irrigation water quality",
        summary="Issue advisory and simulate mitigation",
        assumptions=["Operators are available"],
        steps=[
            PlanStep(
                step_index=1,
                action_type=ActionType.SEND_ALERT,
                title="Send advisory",
                instructions="Notify operators and farmers",
                rationale="Early communication reduces risk",
                simulated=True,
            )
        ],
    )
    provider = _StaticProvider(draft_plan)
    services = PlanningNodeServices(
        session=SimpleNamespace(),
        redis_manager=None,
        provider=provider,
    )

    draft_result = await draft_plan_node(
        {"objective": draft_plan.objective, "retrieved_context": {"k": "v"}},
        services=services,
    )
    assert draft_result["draft_plan"] == draft_plan
    assert provider.calls[0]["objective"] == draft_plan.objective

    validate_result = await validate_plan_node(
        {
            "draft_plan": draft_plan,
            "risk_bundle": SimpleNamespace(
                assessment=SimpleNamespace(risk_level=RiskLevel.WARNING)
            ),
        }
    )
    assert validate_result["validation_result"].is_valid is True
