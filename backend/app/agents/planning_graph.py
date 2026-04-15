"""Initial LangGraph workflow for agent-assisted planning."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.providers import PlanProvider
from app.db.redis import RedisManager
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanValidationResult
from app.orchestration.planning_nodes import (
    PlanningNodeServices,
    assess_risk_node,
    draft_plan_node,
    observe_request_node,
    retrieve_context_node,
    validate_plan_node,
)
from app.schemas.risk import RiskEvaluationFilters
from app.services.risk_service import RiskEvaluationBundle


class PlanningState(TypedDict, total=False):
    """Mutable state carried through the LangGraph planning workflow."""

    request: AgentPlanRequest
    objective: str
    filters: RiskEvaluationFilters
    risk_bundle: RiskEvaluationBundle
    retrieved_context: dict[str, Any]
    draft_plan: GeneratedActionPlan
    validation_result: PlanValidationResult


class AgentPlanningWorkflow:
    """Initial observe -> assess_risk -> retrieve_context -> draft_plan -> validate_plan graph."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        redis_manager: RedisManager | None,
        provider: PlanProvider,
    ) -> None:
        self._services = PlanningNodeServices(
            session=session,
            redis_manager=redis_manager,
            provider=provider,
        )
        self._graph = self._build_graph().compile()

    async def run(
        self,
        request: AgentPlanRequest,
        *,
        precomputed_risk_bundle: RiskEvaluationBundle | None = None,
    ) -> PlanningState:
        """Execute the planning workflow with an optional precomputed risk bundle."""
        initial_state: PlanningState = {"request": request}
        if precomputed_risk_bundle is not None:
            initial_state["risk_bundle"] = precomputed_risk_bundle
        return await self._graph.ainvoke(initial_state)

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(PlanningState)
        graph.add_node("observe", self._observe)
        graph.add_node("assess_risk", self._assess_risk)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("draft_plan", self._draft_plan)
        graph.add_node("validate_plan", self._validate_plan)
        graph.add_edge(START, "observe")
        graph.add_edge("observe", "assess_risk")
        graph.add_edge("assess_risk", "retrieve_context")
        graph.add_edge("retrieve_context", "draft_plan")
        graph.add_edge("draft_plan", "validate_plan")
        graph.add_edge("validate_plan", END)
        return graph

    async def _observe(self, state: PlanningState) -> PlanningState:
        return await observe_request_node(state)

    async def _assess_risk(self, state: PlanningState) -> PlanningState:
        return await assess_risk_node(state, services=self._services)

    async def _retrieve_context(self, state: PlanningState) -> PlanningState:
        return await retrieve_context_node(state, services=self._services)

    async def _draft_plan(self, state: PlanningState) -> PlanningState:
        return await draft_plan_node(state, services=self._services)

    async def _validate_plan(self, state: PlanningState) -> PlanningState:
        return await validate_plan_node(state)
