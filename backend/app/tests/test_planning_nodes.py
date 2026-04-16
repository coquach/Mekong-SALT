"""Node-level tests for planning orchestration services."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.agents.planning_graph import AgentPlanningWorkflow
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, IncidentStatus, RiskLevel, TrendDirection
from app.models.incident import Incident
from app.models.knowledge import EmbeddedChunk, KnowledgeDocument
from app.models.risk import RiskAssessment
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
async def test_retrieve_context_node_includes_ranked_rag_evidence(db_session, seeded_sensor_data):
    now = datetime.now(UTC)
    station = seeded_sensor_data["station_a"]
    region = seeded_sensor_data["region"]
    reading = seeded_sensor_data["reading_a_latest"]

    historical_assessment = RiskAssessment(
        region_id=region.id,
        station_id=station.id,
        based_on_reading_id=reading.id,
        based_on_weather_id=None,
        assessed_at=now - timedelta(hours=6),
        risk_level=RiskLevel.WARNING,
        salinity_dsm=Decimal("3.20"),
        trend_direction=TrendDirection.RISING,
        trend_delta_dsm=Decimal("0.40"),
        rule_version="v1",
        summary="Historical warning risk in same irrigation area.",
        rationale={"source": "test"},
    )
    db_session.add(historical_assessment)
    await db_session.flush()

    historical_incident = Incident(
        region_id=region.id,
        station_id=station.id,
        risk_assessment_id=historical_assessment.id,
        title="Historical salinity response case",
        description="Operators paused intake and waited for safe window.",
        severity=RiskLevel.WARNING,
        status=IncidentStatus.RESOLVED,
        source="risk_engine",
        evidence={"pattern": "rising salinity"},
        opened_at=now - timedelta(hours=5),
        resolved_at=now - timedelta(hours=4),
        created_by="test",
    )
    db_session.add(historical_incident)
    await db_session.flush()

    historical_plan = ActionPlan(
        region_id=region.id,
        risk_assessment_id=historical_assessment.id,
        incident_id=historical_incident.id,
        status=ActionPlanStatus.SIMULATED,
        objective="Protect irrigation water quality",
        generated_by="test",
        model_provider="test-provider",
        summary="Past plan combined advisory and temporary intake pause.",
        assumptions={"items": ["historical case"]},
        plan_steps=[
            {
                "step_index": 1,
                "action_type": "send_alert",
                "priority": 1,
                "title": "Notify",
                "instructions": "Send advisory",
                "rationale": "Reduce exposure",
                "simulated": True,
            }
        ],
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(historical_plan)

    sop_doc = KnowledgeDocument(
        title="Irrigation SOP for salinity events",
        source_uri=f"mekong-salt://knowledge/sop-{uuid4().hex}",
        document_type="guideline",
        summary="SOP for immediate advisories and simulated intake controls.",
        content_text="SOP says send alerts first, then simulate gate response.",
        tags=["sop", "response", "irrigation"],
        metadata_payload={"source": "test"},
    )
    threshold_doc = KnowledgeDocument(
        title="Salinity threshold matrix",
        source_uri=f"mekong-salt://knowledge/threshold-{uuid4().hex}",
        document_type="threshold",
        summary="Warning and critical thresholds in dS/m.",
        content_text="Warning threshold 2.5 dS/m, critical threshold 4.0 dS/m.",
        tags=["threshold", "salinity", "critical"],
        metadata_payload={"source": "test"},
    )
    db_session.add_all([sop_doc, threshold_doc])
    await db_session.flush()

    db_session.add_all(
        [
            EmbeddedChunk(
                document_id=sop_doc.id,
                chunk_index=0,
                content_text=sop_doc.content_text,
                token_count=16,
                embedding=[0.001] * 768,
                metadata_payload={"section": "ops"},
            ),
            EmbeddedChunk(
                document_id=threshold_doc.id,
                chunk_index=0,
                content_text=threshold_doc.content_text,
                token_count=14,
                embedding=[0.001] * 768,
                metadata_payload={"section": "thresholds"},
            ),
        ]
    )
    await db_session.commit()

    current_assessment = SimpleNamespace(
        id=uuid4(),
        region_id=region.id,
        risk_level=RiskLevel.WARNING,
        trend_direction=TrendDirection.RISING,
        trend_delta_dsm=Decimal("0.30"),
        summary="Current warning level requires grounded planning.",
        rationale={"reason": "rising salinity"},
    )
    risk_bundle = SimpleNamespace(
        assessment=current_assessment,
        reading=reading,
        weather_snapshot=None,
    )
    services = PlanningNodeServices(
        session=db_session,
        redis_manager=None,
        provider=SimpleNamespace(),
    )

    result = await retrieve_context_node(
        {
            "objective": "Protect irrigation intake using SOP and threshold guidance",
            "risk_bundle": risk_bundle,
        },
        services=services,
    )

    knowledge_context = result["retrieved_context"]["knowledge_context"]
    assert knowledge_context
    assert any(item["evidence_source"] == "sop_doc" for item in knowledge_context)
    assert any(item["evidence_source"] == "threshold_doc" for item in knowledge_context)
    assert any(item["evidence_source"] == "past_similar_case" for item in knowledge_context)

    first = knowledge_context[0]
    assert "snippet" in first
    assert "citation" in first
    assert "metadata_filters" in first
    assert set(first["metadata_filters"]).issuperset(
        {"region", "station", "severity", "crop", "time"}
    )

    scores = [item["score"] for item in knowledge_context]
    assert scores == sorted(scores, reverse=True)

    retrieval_trace = result["retrieved_context"]["retrieval_trace"]
    assert retrieval_trace["total_evidence"] == len(knowledge_context)
    assert retrieval_trace["top_citations"]


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


@pytest.mark.asyncio
async def test_planning_workflow_uses_injected_services(monkeypatch):
    draft_plan = GeneratedActionPlan(
        objective="Protect irrigation water quality",
        summary="Stub plan",
        assumptions=["stub"],
        steps=[
            PlanStep(
                step_index=1,
                action_type=ActionType.SEND_ALERT,
                title="Send alert",
                instructions="Notify operators",
                rationale="Risk communication first",
                simulated=True,
            )
        ],
    )
    services = PlanningNodeServices(
        session=SimpleNamespace(),
        redis_manager=None,
        provider=SimpleNamespace(),
    )

    async def fake_observe(_state):
        return {
            "filters": RiskEvaluationFilters(station_code="ST-01"),
            "objective": draft_plan.objective,
        }

    async def fake_assess(_state, *, services: PlanningNodeServices):
        assert services is services_ref
        return {"risk_bundle": SimpleNamespace(assessment=SimpleNamespace(risk_level=RiskLevel.WARNING))}

    async def fake_retrieve(_state, *, services: PlanningNodeServices):
        assert services is services_ref
        return {"retrieved_context": {"assessment": {"risk_level": "warning"}}}

    async def fake_draft(_state, *, services: PlanningNodeServices):
        assert services is services_ref
        return {"draft_plan": draft_plan}

    async def fake_validate(_state):
        return {
            "validation_result": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "normalized_steps": [],
            }
        }

    services_ref = services
    monkeypatch.setattr("app.agents.planning_graph.observe_request_node", fake_observe)
    monkeypatch.setattr("app.agents.planning_graph.assess_risk_node", fake_assess)
    monkeypatch.setattr("app.agents.planning_graph.retrieve_context_node", fake_retrieve)
    monkeypatch.setattr("app.agents.planning_graph.draft_plan_node", fake_draft)
    monkeypatch.setattr("app.agents.planning_graph.validate_plan_node", fake_validate)

    workflow = AgentPlanningWorkflow(services=services)
    state = await workflow.run(AgentPlanRequest(station_code="ST-01"))

    assert state["draft_plan"] == draft_plan
    assert state["validation_result"]["is_valid"] is True
