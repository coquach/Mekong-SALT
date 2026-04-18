"""Tests for feedback-driven replan request handling."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, IncidentStatus, RiskLevel, TrendDirection
from app.models.incident import Incident
from app.models.risk import RiskAssessment
from app.schemas.action import FeedbackEvaluation
from app.services.agent_planning_service import AgentPlanBundle
from app.repositories.action import ActionPlanRepository
from app.services.replan_service import (
    REPLAN_REQUEST_EVENT_TYPE,
    handle_replan_requested_event,
    queue_replan_request_from_feedback,
)
from app.orchestration.lifecycle_graph import LifecycleAdvanceResult
from app.services.risk_service import RiskEvaluationBundle


class _NoopRedisManager:
    async def publish_signal(self, channel, payload=None):
        _ = (channel, payload)
        return None


async def _persist_replan_source_context(db_session, *, seeded_sensor_data):
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
        summary="Replan service test assessment",
        rationale={"source": "test"},
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    incident = Incident(
        region_id=region.id,
        station_id=station.id,
        risk_assessment_id=assessment.id,
        title="Replan test incident",
        description="Test incident for background replan processing.",
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
        status=ActionPlanStatus.SIMULATED,
        objective="Protect irrigation water quality",
        generated_by="test-suite",
        model_provider="mock",
        summary="Source plan that produced the replan request.",
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
            }
        ],
        validation_result={"is_valid": True, "errors": [], "warnings": []},
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    source_plan = await ActionPlanRepository(db_session).get_with_assessment(plan.id)
    assert source_plan is not None
    return assessment, incident, source_plan, reading


@pytest.mark.asyncio
async def test_queue_replan_request_from_feedback_emits_event(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    assessment, incident, plan, _reading = await _persist_replan_source_context(
        db_session,
        seeded_sensor_data=seeded_sensor_data,
    )
    monkeypatch.setattr(
        "app.services.domain_event_service._get_signal_redis_manager",
        lambda: _NoopRedisManager(),
    )

    feedback = FeedbackEvaluation(
        outcome_class="failed_execution",
        status="not_improved",
        summary="Execution did not improve salinity.",
        replan_recommended=True,
        replan_reason="Salinity remained high after execution.",
    )
    event = await queue_replan_request_from_feedback(
        db_session,
        plan=plan,
        feedback=feedback,
        execution_batch_id=uuid4(),
        trigger_source="execution-service.feedback",
        settings=Settings(active_monitoring_feedback_replan_max_attempts=1),
    )

    assert event is not None
    assert event.event_type == REPLAN_REQUEST_EVENT_TYPE
    assert event.incident_id == incident.id
    assert event.action_plan_id == plan.id
    assert event.payload["action_plan_id"] == str(plan.id)
    assert event.payload["feedback_outcome_class"] == "failed_execution"
    assert event.payload["summary"] == "Background replan requested after execution feedback."
    assert event.payload["dedupe_key"] == f"replan-request:{plan.id}:failed_execution:not_improved"
    assert event.payload["risk_assessment_id"] == str(assessment.id)
    assert event.payload["station_id"] == str(incident.station_id)


@pytest.mark.asyncio
async def test_handle_replan_requested_event_creates_completion_event(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    assessment, incident, plan, reading = await _persist_replan_source_context(
        db_session,
        seeded_sensor_data=seeded_sensor_data,
    )

    feedback = FeedbackEvaluation(
        outcome_class="partial_success",
        status="no_change",
        summary="Execution did not materially improve salinity.",
        replan_recommended=True,
        replan_reason="Need another plan iteration.",
    )
    request_event = await queue_replan_request_from_feedback(
        db_session,
        plan=plan,
        feedback=feedback,
        execution_batch_id=uuid4(),
        trigger_source="execution-service.feedback",
        settings=Settings(active_monitoring_feedback_replan_max_attempts=1),
    )
    assert request_event is not None

    async def fake_resolve_target_reading(session, filters):
        return reading

    async def fake_evaluate_current_risk(
        session,
        *,
        filters,
        redis_manager,
        target_reading,
        trigger_source,
        trigger_payload,
    ):
        _ = (session, filters, redis_manager, target_reading, trigger_source, trigger_payload)
        return RiskEvaluationBundle(
            assessment=assessment,
            reading=reading,
            weather_snapshot=None,
        )

    async def fake_generate_agent_plan(
        session,
        *,
        payload,
        redis_manager,
        risk_bundle,
        trigger_source,
        trigger_payload,
    ):
        _ = (redis_manager, trigger_source, trigger_payload)
        new_plan = ActionPlan(
            region_id=plan.region_id,
            risk_assessment_id=risk_bundle.assessment.id,
            incident_id=incident.id,
            status=ActionPlanStatus.PENDING_APPROVAL,
            objective=payload.objective or plan.objective,
            generated_by="replan-test",
            model_provider="mock",
            summary="Background replan generated from event.",
            assumptions={"items": []},
            plan_steps=[
                {
                    "step_index": 1,
                    "action_type": ActionType.SEND_ALERT.value,
                    "priority": 1,
                    "title": "Alert operators",
                    "instructions": "Send a follow-up alert.",
                    "rationale": "Provide a clearer mitigation path.",
                    "simulated": True,
                }
            ],
            validation_result={"is_valid": True, "errors": [], "warnings": []},
        )
        db_session.add(new_plan)
        await db_session.commit()
        await db_session.refresh(new_plan)
        return AgentPlanBundle(
            risk_bundle=risk_bundle,
            plan=new_plan,
            provider_name="mock",
        )

    async def fake_advance_plan_with_lifecycle_graph(session, *, plan, settings):
        _ = (session, settings)
        return LifecycleAdvanceResult(
            status="awaiting_human_approval",
            plan=plan,
            approval=None,
            execution_bundle=None,
            memory_log=None,
            reason="stubbed lifecycle",
            transition_log=[],
        )

    monkeypatch.setattr(
        "app.services.replan_service.resolve_target_reading",
        fake_resolve_target_reading,
    )
    monkeypatch.setattr(
        "app.services.replan_service.evaluate_current_risk",
        fake_evaluate_current_risk,
    )
    monkeypatch.setattr(
        "app.services.replan_service.generate_agent_plan",
        fake_generate_agent_plan,
    )
    monkeypatch.setattr(
        "app.orchestration.lifecycle_graph.advance_plan_with_lifecycle_graph",
        fake_advance_plan_with_lifecycle_graph,
    )
    monkeypatch.setattr(
        "app.services.domain_event_service._get_signal_redis_manager",
        lambda: _NoopRedisManager(),
    )

    result = await handle_replan_requested_event(
        db_session,
        event=request_event,
        redis_manager=None,
        settings=Settings(),
    )

    assert result.status == "completed"
    assert result.plan_bundle is not None
    assert result.completed_event is not None
    assert result.completed_event.event_type == "monitoring.replan_completed"
    assert result.lifecycle_status == "awaiting_human_approval"
