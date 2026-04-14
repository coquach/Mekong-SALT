"""Agent-assisted planning orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.planning_graph import AgentPlanningWorkflow
from app.agents.providers import get_plan_provider
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, AuditEventType, IncidentStatus
from app.repositories.action import ActionPlanRepository
from app.services.audit_service import write_audit_log
from app.services.incident_service import ensure_incident_for_assessment, get_incident
from app.schemas.agent import AgentPlanRequest
from app.services.risk_service import RiskEvaluationBundle


@dataclass(slots=True)
class AgentPlanBundle:
    """Aggregate result returned from the agent planning service."""

    risk_bundle: RiskEvaluationBundle
    plan: ActionPlan
    provider_name: str


async def generate_agent_plan(
    session: AsyncSession,
    *,
    payload: AgentPlanRequest,
    redis_manager: RedisManager | None,
) -> AgentPlanBundle:
    """Run the LangGraph planning workflow and persist the resulting plan draft."""
    provider = get_plan_provider(payload.provider)
    workflow = AgentPlanningWorkflow(
        session=session,
        redis_manager=redis_manager,
        provider=provider,
    )
    state = await workflow.run(payload)

    risk_bundle = state["risk_bundle"]
    generated_plan = state["draft_plan"]
    validation_result = state["validation_result"]
    incident = (
        await get_incident(session, payload.incident_id)
        if payload.incident_id is not None
        else await ensure_incident_for_assessment(session, risk_bundle.assessment, actor_name="planning-agent")
    )

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
        model_provider=provider.name,
        summary=generated_plan.summary,
        assumptions={"items": generated_plan.assumptions},
        plan_steps=[
            step.model_dump(mode="json")
            for step in generated_plan.steps
        ],
        validation_result=validation_result.model_dump(mode="json"),
    )
    plan_repo = ActionPlanRepository(session)
    await plan_repo.add(plan)
    if incident is not None and validation_result.is_valid:
        incident.status = IncidentStatus.PENDING_APPROVAL
    await write_audit_log(
        session,
        event_type=AuditEventType.PLAN,
        actor_name="planning-agent",
        region_id=plan.region_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        summary="AI plan generated and queued for human approval."
        if validation_result.is_valid
        else "AI plan generated but held as draft due to policy validation errors.",
        payload={
            "provider": provider.name,
            "confidence_score": generated_plan.confidence_score,
            "validation": validation_result.model_dump(mode="json"),
        },
    )
    await session.commit()
    await session.refresh(plan)

    return AgentPlanBundle(
        risk_bundle=risk_bundle,
        plan=plan,
        provider_name=provider.name,
    )
