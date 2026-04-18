"""Initial LangGraph workflow for agent-assisted planning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.orchestration.planning_nodes import (
    PlanningNodeServices,
    assess_risk_node,
    draft_plan_node,
    observe_request_node,
    retrieve_context_node,
    validate_plan_node,
)
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanValidationResult
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
    transition_log: list[dict[str, Any]]


class AgentPlanningWorkflow:
    """Initial observe -> assess_risk -> retrieve_context -> draft_plan -> validate_plan graph."""

    def __init__(
        self,
        *,
        services: PlanningNodeServices,
    ) -> None:
        self._services = services
        self._graph = self._build_graph().compile()

    async def run(
        self,
        request: AgentPlanRequest,
        *,
        precomputed_risk_bundle: RiskEvaluationBundle | None = None,
    ) -> PlanningState:
        """Execute the planning workflow with an optional precomputed risk bundle."""
        initial_state: PlanningState = {
            "request": request,
            "transition_log": [],
        }
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
        updates = await observe_request_node(state)
        updates["transition_log"] = self._append_transition(
            state,
            "observe",
            details={"objective": updates.get("objective")},
        )
        return updates

    async def _assess_risk(self, state: PlanningState) -> PlanningState:
        updates = await assess_risk_node(state, services=self._services)
        risk_bundle = updates.get("risk_bundle") or state.get("risk_bundle")
        updates["transition_log"] = self._append_transition(
            state,
            "assess_risk",
            details={
                "risk_level": (
                    risk_bundle.assessment.risk_level.value
                    if risk_bundle is not None
                    else None
                ),
                "summary": (
                    risk_bundle.assessment.summary
                    if risk_bundle is not None
                    else None
                ),
            },
        )
        return updates

    async def _retrieve_context(self, state: PlanningState) -> PlanningState:
        updates = await retrieve_context_node(state, services=self._services)
        retrieved_context = updates.get("retrieved_context") or {}
        updates["transition_log"] = self._append_transition(
            state,
            "retrieve_context",
            details={
                "retrieved_context_keys": sorted(retrieved_context.keys()),
                "gate_targets": len(retrieved_context.get("gate_targets") or []),
                "evidence_count": (
                    retrieved_context.get("retrieval_trace", {}).get("total_evidence")
                    if isinstance(retrieved_context.get("retrieval_trace"), dict)
                    else None
                ),
            },
        )
        return updates

    async def _draft_plan(self, state: PlanningState) -> PlanningState:
        updates = await draft_plan_node(state, services=self._services)
        draft_plan = updates.get("draft_plan")
        updates["transition_log"] = self._append_transition(
            state,
            "draft_plan",
            details={
                "step_count": len(getattr(draft_plan, "steps", []) or []),
                "confidence_score": getattr(draft_plan, "confidence_score", None),
            },
        )
        return updates

    async def _validate_plan(self, state: PlanningState) -> PlanningState:
        updates = await validate_plan_node(state)
        validation_result = updates.get("validation_result")
        updates["transition_log"] = self._append_transition(
            state,
            "validate_plan",
            details={
                "is_valid": getattr(validation_result, "is_valid", None),
                "error_count": len(getattr(validation_result, "errors", []) or []),
                "warning_count": len(getattr(validation_result, "warnings", []) or []),
            },
        )
        return updates

    def _append_transition(
        self,
        state: PlanningState,
        node: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        transitions = list(state.get("transition_log") or [])
        transitions.append({
            "node": node,
            "status": "completed",
            "at": datetime.now(UTC).isoformat(),
            "details": details or {},
        })
        return transitions
