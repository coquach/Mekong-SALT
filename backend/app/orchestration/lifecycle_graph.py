"""LangGraph lifecycle orchestration for approval/execution/feedback/memory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.approval import Approval
from app.models.decision import DecisionLog
from app.models.enums import RiskLevel
from app.orchestration.lifecycle_nodes import (
    LifecycleNodeServices,
    approval_gate_node,
    classify_risk_node,
    execute_node,
    feedback_node,
    memory_write_node,
)
from app.repositories.action import ActionPlanRepository
from app.services.execution import SimulatedExecutionBundle

LifecycleAdvanceStatus = Literal[
    "skipped_not_pending",
    "awaiting_human_approval",
    "approved",
    "approved_not_executed",
    "executed",
]


@dataclass(slots=True)
class LifecycleAdvanceResult:
    """Result of advancing a plan through the lifecycle graph."""

    status: LifecycleAdvanceStatus
    plan: ActionPlan
    approval: Approval | None = None
    execution_bundle: SimulatedExecutionBundle | None = None
    memory_log: DecisionLog | None = None
    reason: str | None = None
    transition_log: list[dict[str, Any]] | None = None


class LifecycleState(TypedDict, total=False):
    """Mutable state carried by the lifecycle graph."""

    plan: ActionPlan
    risk_level: RiskLevel | None
    risk_classification: str
    requires_human_approval: bool
    approval: Approval | None
    approved_plan: ActionPlan
    approval_status: str
    execution_bundle: SimulatedExecutionBundle | None
    executed_plan: ActionPlan
    execution_status: str
    feedback_status: str
    feedback_summary: str
    memory_log: DecisionLog | None
    memory_write_status: str
    reason: str
    transition_log: list[dict[str, Any]]


class MonitoringLifecycleWorkflow:
    """classify_risk -> approval_gate -> execute -> feedback -> memory_write graph."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
    ) -> None:
        self._services = LifecycleNodeServices(
            session=session,
            settings=settings,
        )
        self._graph = self._build_graph().compile()

    async def run(self, plan: ActionPlan) -> LifecycleState:
        """Execute lifecycle graph for one plan."""
        initial_state: LifecycleState = {
            "plan": plan,
            "transition_log": [],
        }
        return await self._graph.ainvoke(initial_state)

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(LifecycleState)
        graph.add_node("classify_risk", self._classify_risk)
        graph.add_node("approval_gate", self._approval_gate)
        graph.add_node("execute", self._execute)
        graph.add_node("feedback", self._feedback)
        graph.add_node("memory_write", self._memory_write)

        graph.add_edge(START, "classify_risk")
        graph.add_edge("classify_risk", "approval_gate")
        graph.add_edge("approval_gate", "execute")
        graph.add_edge("execute", "feedback")
        graph.add_edge("feedback", "memory_write")
        graph.add_edge("memory_write", END)
        return graph

    async def _classify_risk(self, state: LifecycleState) -> LifecycleState:
        return await classify_risk_node(state)

    async def _approval_gate(self, state: LifecycleState) -> LifecycleState:
        return await approval_gate_node(state, services=self._services)

    async def _execute(self, state: LifecycleState) -> LifecycleState:
        return await execute_node(state, services=self._services)

    async def _feedback(self, state: LifecycleState) -> LifecycleState:
        return await feedback_node(state)

    async def _memory_write(self, state: LifecycleState) -> LifecycleState:
        return await memory_write_node(state, services=self._services)


async def advance_plan_with_lifecycle_graph(
    session: AsyncSession,
    *,
    plan: ActionPlan,
    settings: Settings,
) -> LifecycleAdvanceResult:
    """Run lifecycle graph and normalize result for monitoring service integration."""
    loaded_plan = await ActionPlanRepository(session).get_with_assessment(plan.id)
    resolved_input_plan = loaded_plan or plan

    workflow = MonitoringLifecycleWorkflow(
        session=session,
        settings=settings,
    )
    state = await workflow.run(resolved_input_plan)

    resolved_plan = state.get("executed_plan") or state.get("approved_plan") or state["plan"]
    status = _resolve_lifecycle_status(state)
    reason = state.get("reason")

    return LifecycleAdvanceResult(
        status=status,
        plan=resolved_plan,
        approval=state.get("approval"),
        execution_bundle=state.get("execution_bundle"),
        memory_log=state.get("memory_log"),
        reason=reason,
        transition_log=state.get("transition_log"),
    )


def _resolve_lifecycle_status(state: LifecycleState) -> LifecycleAdvanceStatus:
    approval_status = state.get("approval_status")
    execution_status = state.get("execution_status")

    if approval_status == "awaiting_human_approval":
        return "awaiting_human_approval"
    if approval_status == "skipped_not_pending":
        return "skipped_not_pending"
    if execution_status == "executed":
        return "executed"
    if approval_status == "approved" and execution_status:
        return "approved_not_executed"
    return "approved"
