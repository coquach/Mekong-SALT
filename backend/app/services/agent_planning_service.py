"""Agent-assisted planning orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.planning_graph import AgentPlanningWorkflow
from app.agents.providers import get_plan_provider
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus
from app.repositories.action import ActionPlanRepository
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

    plan = ActionPlan(
        region_id=risk_bundle.assessment.region_id,
        risk_assessment_id=risk_bundle.assessment.id,
        status=(
            ActionPlanStatus.VALIDATED
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
    await session.commit()
    await session.refresh(plan)

    return AgentPlanBundle(
        risk_bundle=risk_bundle,
        plan=plan,
        provider_name=provider.name,
    )
