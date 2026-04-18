"""Agent-assisted planning orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.planning_graph import AgentPlanningWorkflow
from app.agents.providers import get_plan_provider
from app.core.salinity_units import dsm_to_gl
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.agent_run import AgentRun
from app.models.enums import ActionPlanStatus, AuditEventType, IncidentStatus
from app.models.incident import Incident
from app.orchestration.planning_nodes import PlanningNodeServices
from app.repositories.action import ActionPlanRepository
from app.services.agent_trace_service import (
    capture_observation_snapshot,
    finish_agent_run,
    start_agent_run,
)
from app.services.audit_service import write_audit_log
from app.services.db import append_domain_event_and_dispatch
from app.services.incident_service import ensure_incident_for_assessment, get_incident
from app.services.llm import VertexGeminiPlannerAdapter
from app.services.notify import get_domain_event_notification_dispatcher
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanValidationResult
from app.services.risk_service import RiskEvaluationBundle


@dataclass(slots=True)
class AgentPlanBundle:
    """Aggregate result returned from the agent planning service."""

    risk_bundle: RiskEvaluationBundle
    plan: ActionPlan
    provider_name: str
    run_id: UUID | None = None


async def generate_agent_plan(
    session: AsyncSession,
    *,
    payload: AgentPlanRequest,
    redis_manager: RedisManager | None,
    risk_bundle: RiskEvaluationBundle | None = None,
    trigger_source: str = "agent.plan",
    trigger_payload: dict[str, Any] | None = None,
) -> AgentPlanBundle:
    """Run the LangGraph planning workflow and persist the resulting plan draft."""
    run = await start_agent_run(
        session,
        run_type="plan_generation",
        trigger_source=trigger_source,
        payload={
            "request": payload.model_dump(mode="json"),
            "trigger_payload": trigger_payload or {},
        },
        region_id=payload.region_id,
        station_id=payload.station_id,
    )
    try:
        planner = VertexGeminiPlannerAdapter()
        provider = get_plan_provider(payload.provider, planner=planner)
        workflow_services = PlanningNodeServices(
            session=session,
            redis_manager=redis_manager,
            provider=provider,
        )
        workflow = AgentPlanningWorkflow(
            services=workflow_services,
        )
        state = await workflow.run(
            payload,
            precomputed_risk_bundle=risk_bundle,
        )

        resolved_risk_bundle = state["risk_bundle"]
        retrieved_context = state["retrieved_context"]
        generated_plan = state["draft_plan"]
        validation_result = state["validation_result"]
        transition_log = state.get("transition_log") or []

        await _capture_plan_observation(
            session=session,
            run=run,
            risk_bundle=resolved_risk_bundle,
            retrieved_context=retrieved_context,
            transition_log=transition_log,
        )
        incident, incident_decision = await _resolve_plan_incident(
            session=session,
            payload=payload,
            risk_bundle=resolved_risk_bundle,
        )
        plan = await _persist_plan(
            session=session,
            risk_bundle=resolved_risk_bundle,
            incident=incident,
            generated_plan=generated_plan,
            validation_result=validation_result,
            provider_name=provider.name,
        )
        if incident is not None and validation_result.is_valid:
            incident.status = IncidentStatus.PENDING_APPROVAL

        await _write_plan_audit(
            session,
            plan=plan,
            provider_name=provider.name,
            generated_plan=generated_plan,
            validation_result=validation_result,
            retrieved_context=retrieved_context,
            transition_log=transition_log,
        )
        await append_domain_event_and_dispatch(
            session,
            event_type="notification.plan_created",
            source="planning-service",
            summary=f"Kế hoạch hành động đã được tạo ({plan.status.value})",
            payload={
                "event": "plan_created",
                "subject": f"Kế hoạch hành động đã được tạo ({plan.status.value})",
                "message": f"Kế hoạch '{plan.id}' đã được tạo cho mục tiêu: {plan.objective}",
                "channels": ["dashboard", "sms_mock", "zalo_mock", "email_mock"],
                "details": {
                    "action_plan_id": str(plan.id),
                    "status": plan.status.value,
                    "objective": plan.objective,
                },
            },
            aggregate_type="incident" if plan.incident_id is not None else "action_plan",
            aggregate_id=plan.incident_id if plan.incident_id is not None else plan.id,
            region_id=plan.region_id,
            incident_id=plan.incident_id,
            action_plan_id=plan.id,
            dispatcher=get_domain_event_notification_dispatcher(),
        )
        finish_agent_run(
            run,
            status="succeeded",
            trace=_success_trace(
                incident_decision=incident_decision,
                plan=plan,
                validation_result=validation_result,
                retrieved_context=retrieved_context,
                transition_log=transition_log,
            ),
            risk_assessment_id=resolved_risk_bundle.assessment.id,
            incident_id=plan.incident_id,
            action_plan_id=plan.id,
        )
        await session.commit()
        await session.refresh(plan)

        return AgentPlanBundle(
            risk_bundle=resolved_risk_bundle,
            plan=plan,
            provider_name=provider.name,
            run_id=run.id,
        )
    except Exception as exc:
        finish_agent_run(
            run,
            status="failed",
            trace=_failure_trace(exc),
            error_message=str(exc),
        )
        await session.commit()
        raise


async def _capture_plan_observation(
    *,
    session: AsyncSession,
    run: AgentRun,
    risk_bundle: RiskEvaluationBundle,
    retrieved_context: dict[str, Any],
    transition_log: list[dict[str, Any]],
) -> None:
    """Persist the observation snapshot used before committing a plan decision."""
    await capture_observation_snapshot(
        session,
        run=run,
        source="plan.pre_decision",
        payload=_plan_observation_payload(
            risk_bundle,
            retrieved_context,
            transition_log,
        ),
        region_id=risk_bundle.assessment.region_id,
        station_id=risk_bundle.assessment.station_id,
        reading_id=risk_bundle.reading.id,
        weather_snapshot_id=(
            risk_bundle.weather_snapshot.id
            if risk_bundle.weather_snapshot is not None
            else None
        ),
    )


async def _resolve_plan_incident(
    *,
    session: AsyncSession,
    payload: AgentPlanRequest,
    risk_bundle: RiskEvaluationBundle,
) -> tuple[Incident | None, dict[str, Any]]:
    """Resolve the incident target and return a trace-friendly decision payload."""
    if payload.incident_id is not None:
        incident = await get_incident(session, payload.incident_id)
        return incident, {
            "decision": "provided",
            "reason": "Plan request included an incident_id.",
            "incident_id": str(incident.id),
        }

    incident_result = await ensure_incident_for_assessment(
        session,
        risk_bundle.assessment,
        actor_name="planning-agent",
    )
    incident = incident_result.incident
    return incident, {
        "decision": incident_result.decision,
        "reason": incident_result.reason,
        "incident_id": str(incident.id) if incident is not None else None,
    }


async def _persist_plan(
    *,
    session: AsyncSession,
    risk_bundle: RiskEvaluationBundle,
    incident: Incident | None,
    generated_plan: GeneratedActionPlan,
    validation_result: PlanValidationResult,
    provider_name: str,
) -> ActionPlan:
    """Create and flush the ActionPlan row from a validated generated plan."""
    plan = ActionPlan(
        region_id=risk_bundle.assessment.region_id,
        risk_assessment_id=risk_bundle.assessment.id,
        incident_id=incident.id if incident is not None else None,
        status=(
            ActionPlanStatus.PENDING_APPROVAL
            if validation_result.is_valid
            else ActionPlanStatus.DRAFT
        ),
        objective=generated_plan.objective,
        generated_by="langgraph-agent",
        model_provider=provider_name,
        summary=generated_plan.summary,
        assumptions={"items": generated_plan.assumptions},
        plan_steps=[step.model_dump(mode="json") for step in generated_plan.steps],
        validation_result=validation_result.model_dump(mode="json"),
    )
    await ActionPlanRepository(session).add(plan)
    return plan


async def _write_plan_audit(
    session: AsyncSession,
    *,
    plan: ActionPlan,
    provider_name: str,
    generated_plan: GeneratedActionPlan,
    validation_result: PlanValidationResult,
    retrieved_context: dict[str, Any],
    transition_log: list[dict[str, Any]],
) -> None:
    """Write the audit log entry for plan generation."""
    await write_audit_log(
        session,
        event_type=AuditEventType.PLAN,
        actor_name="planning-agent",
        region_id=plan.region_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        summary=(
            "AI plan generated and queued for reactive approval."
            if validation_result.is_valid
            else "AI plan generated but held as draft due to policy validation errors."
        ),
        payload={
            "provider": provider_name,
            "confidence_score": generated_plan.confidence_score,
            "validation": validation_result.model_dump(mode="json"),
            "retrieval_trace": retrieved_context.get("retrieval_trace") or {},
            "planning_transition_log": transition_log,
        },
    )


def _plan_observation_payload(
    risk_bundle: RiskEvaluationBundle,
    retrieved_context: dict[str, Any],
    transition_log: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the observation snapshot payload for a planning run."""
    weather = risk_bundle.weather_snapshot
    return {
        "reading": {
            "id": str(risk_bundle.reading.id),
            "recorded_at": risk_bundle.reading.recorded_at.isoformat(),
            "salinity_dsm": str(risk_bundle.reading.salinity_dsm),
            "salinity_gl": str(dsm_to_gl(risk_bundle.reading.salinity_dsm)),
            "water_level_m": str(risk_bundle.reading.water_level_m),
        },
        "assessment": {
            "risk_assessment_id": str(risk_bundle.assessment.id),
            "risk_level": risk_bundle.assessment.risk_level.value,
            "summary": risk_bundle.assessment.summary,
            "rationale": risk_bundle.assessment.rationale,
        },
        "weather_snapshot": (
            {
                "id": str(weather.id),
                "observed_at": weather.observed_at.isoformat(),
                "wind_speed_mps": (
                    str(weather.wind_speed_mps)
                    if weather.wind_speed_mps is not None
                    else None
                ),
                "tide_level_m": (
                    str(weather.tide_level_m)
                    if weather.tide_level_m is not None
                    else None
                ),
            }
            if weather is not None
            else None
        ),
        "earth_engine_context": retrieved_context.get("earth_engine_context"),
        "retrieval_trace": retrieved_context.get("retrieval_trace") or {},
        "planning_transition_log": transition_log,
        "knowledge_context_preview": [
            {
                "rank": item.get("rank"),
                "evidence_source": item.get("evidence_source"),
                "score": item.get("score"),
                "citation": item.get("citation"),
            }
            for item in (retrieved_context.get("knowledge_context") or [])[:5]
        ],
    }


def _success_trace(
    *,
    incident_decision: dict[str, Any],
    plan: ActionPlan,
    validation_result: PlanValidationResult,
    retrieved_context: dict[str, Any],
    transition_log: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the terminal trace payload for a successful planning run."""
    return {
        "incident_decision": incident_decision,
        "plan_decision": {
            "decision": "created" if validation_result.is_valid else "held_draft",
            "reason": (
                "Policy validation passed; plan is pending reactive approval."
                if validation_result.is_valid
                else "Policy validation failed; plan remains draft."
            ),
            "action_plan_id": str(plan.id),
            "validation": validation_result.model_dump(mode="json"),
        },
        "retrieval_trace": retrieved_context.get("retrieval_trace") or {},
        "planning_transition_log": transition_log,
    }


def _failure_trace(exc: Exception) -> dict[str, Any]:
    """Build the terminal trace payload for a failed planning run."""
    return {
        "incident_decision": {
            "decision": "not_decided",
            "reason": str(exc),
        },
        "plan_decision": {
            "decision": "failed",
            "reason": str(exc),
        },
    }
