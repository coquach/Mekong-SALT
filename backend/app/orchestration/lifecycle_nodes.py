"""Node-sized functions for lifecycle orchestration after plan creation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution_policy import is_auto_execution_eligible
from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.approval import Approval
from app.models.decision import DecisionLog
from app.models.enums import ActionPlanStatus, ApprovalDecision, DecisionActorType, RiskLevel
from app.repositories.decision import DecisionLogRepository
from app.schemas.action import SimulatedExecutionRequest
from app.schemas.approval import ApprovalRequest
from app.services.execution import SimulatedExecutionBundle, execute_simulated_plan
from app.services.approval import decide_plan

HIGH_RISK_HITL_LEVELS = {RiskLevel.DANGER, RiskLevel.CRITICAL}


@dataclass(slots=True)
class LifecycleNodeServices:
    """Dependencies required by lifecycle graph node services."""

    session: AsyncSession
    settings: Settings


def _append_transition(
    state: Mapping[str, Any],
    *,
    node: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    transitions = list(state.get("transition_log") or [])
    transitions.append(
        {
            "node": node,
            "status": status,
            "at": datetime.now(UTC).isoformat(),
            "details": details or {},
        }
    )
    return transitions


def _classify_risk_level(risk_level: RiskLevel | None) -> str:
    if risk_level in {RiskLevel.CRITICAL, RiskLevel.DANGER}:
        return "high"
    if risk_level is RiskLevel.WARNING:
        return "moderate"
    if risk_level is RiskLevel.SAFE:
        return "low"
    return "unknown"


async def classify_risk_node(state: Mapping[str, Any]) -> dict[str, Any]:
    """Classify risk to drive downstream approval and execution policy."""
    plan: ActionPlan = state["plan"]
    risk_level = plan.risk_assessment.risk_level if plan.risk_assessment is not None else None
    risk_classification = _classify_risk_level(risk_level)
    requires_human_approval = risk_level in HIGH_RISK_HITL_LEVELS if risk_level is not None else True

    return {
        "risk_level": risk_level,
        "risk_classification": risk_classification,
        "requires_human_approval": requires_human_approval,
        "transition_log": _append_transition(
            state,
            node="classify_risk",
            status="classified",
            details={
                "risk_level": risk_level.value if risk_level is not None else None,
                "risk_classification": risk_classification,
                "requires_human_approval": requires_human_approval,
            },
        ),
    }


async def approval_gate_node(
    state: Mapping[str, Any],
    *,
    services: LifecycleNodeServices,
) -> dict[str, Any]:
    """Apply approval policy with explicit HITL gate for high risk plans."""
    plan: ActionPlan = state.get("approved_plan") or state["plan"]

    if plan.status is not ActionPlanStatus.PENDING_APPROVAL:
        reason = f"Plan status is {plan.status.value}; approval gate skipped."
        return {
            "approved_plan": plan,
            "approval_status": "skipped_not_pending",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="approval_gate",
                status="skipped_not_pending",
                details={"reason": reason},
            ),
        }

    if state.get("requires_human_approval", True):
        reason = "Risk classification requires human approval."
        return {
            "approved_plan": plan,
            "approval_status": "awaiting_human_approval",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="approval_gate",
                status="awaiting_human_approval",
                details={"reason": reason},
            ),
        }

    approval, approved_plan = await decide_plan(
        services.session,
        plan_id=plan.id,
        payload=ApprovalRequest(
            decision=ApprovalDecision.APPROVED,
            comment="Approved automatically by lifecycle orchestration graph.",
        ),
        actor_name="lifecycle-orchestrator",
    )
    return {
        "approval": approval,
        "approved_plan": approved_plan,
        "approval_status": "approved",
        "transition_log": _append_transition(
            state,
            node="approval_gate",
            status="approved",
            details={"approval_id": str(approval.id)},
        ),
    }


async def execute_node(
    state: Mapping[str, Any],
    *,
    services: LifecycleNodeServices,
) -> dict[str, Any]:
    """Execute approved plans when auto-execution policy permits it."""
    plan: ActionPlan = state.get("approved_plan") or state["plan"]

    if plan.status is not ActionPlanStatus.APPROVED:
        reason = f"Plan status is {plan.status.value}; execution skipped."
        return {
            "executed_plan": plan,
            "execution_status": "skipped_not_approved",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="execute",
                status="skipped_not_approved",
                details={"reason": reason},
            ),
        }

    if not services.settings.reactive_auto_execute_enabled:
        reason = "Reactive auto-execution is disabled."
        return {
            "executed_plan": plan,
            "execution_status": "skipped_auto_execute_disabled",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="execute",
                status="skipped_auto_execute_disabled",
                details={"reason": reason},
            ),
        }

    risk_level: RiskLevel | None = state.get("risk_level")
    if risk_level is None:
        reason = "Risk level missing; execution requires explicit review."
        return {
            "executed_plan": plan,
            "execution_status": "skipped_missing_risk_level",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="execute",
                status="skipped_missing_risk_level",
                details={"reason": reason},
            ),
        }

    eligible, reason = is_auto_execution_eligible(
        plan,
        risk_level=risk_level,
    )
    if not eligible:
        return {
            "executed_plan": plan,
            "execution_status": "skipped_policy",
            "reason": reason,
            "transition_log": _append_transition(
                state,
                node="execute",
                status="skipped_policy",
                details={"reason": reason},
            ),
        }

    execution_bundle = await execute_simulated_plan(
        services.session,
        payload=SimulatedExecutionRequest(
            action_plan_id=plan.id,
            idempotency_key=f"lifecycle-graph:{plan.id}",
        ),
        actor_name="lifecycle-orchestrator",
    )
    return {
        "execution_bundle": execution_bundle,
        "executed_plan": execution_bundle.plan,
        "execution_status": "executed",
        "transition_log": _append_transition(
            state,
            node="execute",
            status="executed",
            details={"batch_id": str(execution_bundle.batch.id)},
        ),
    }


async def feedback_node(state: Mapping[str, Any]) -> dict[str, Any]:
    """Extract normalized feedback state from execution output."""
    execution_bundle: SimulatedExecutionBundle | None = state.get("execution_bundle")
    if execution_bundle is None:
        return {
            "feedback_status": "not_available",
            "feedback_summary": "No execution was run; feedback is not available.",
            "transition_log": _append_transition(
                state,
                node="feedback",
                status="not_available",
                details={"reason": "execution_bundle_missing"},
            ),
        }

    feedback = execution_bundle.feedback
    return {
        "feedback_status": feedback.outcome_class,
        "feedback_summary": feedback.summary,
        "transition_log": _append_transition(
            state,
            node="feedback",
            status=feedback.outcome_class,
            details={"summary": feedback.summary},
        ),
    }


async def memory_write_node(
    state: Mapping[str, Any],
    *,
    services: LifecycleNodeServices,
) -> dict[str, Any]:
    """Persist a lifecycle checkpoint as an explicit memory decision log."""
    plan: ActionPlan = state.get("executed_plan") or state.get("approved_plan") or state["plan"]
    execution_bundle: SimulatedExecutionBundle | None = state.get("execution_bundle")
    feedback_status = str(state.get("feedback_status") or "inconclusive")
    transitions = list(state.get("transition_log") or [])

    latest_execution_id = None
    if execution_bundle is not None and execution_bundle.executions:
        latest_execution_id = execution_bundle.executions[-1].id

    memory_log = DecisionLog(
        region_id=plan.region_id,
        risk_assessment_id=plan.risk_assessment_id,
        action_plan_id=plan.id,
        action_execution_id=latest_execution_id,
        logged_at=datetime.now(UTC),
        actor_type=DecisionActorType.SYSTEM,
        actor_name="lifecycle-orchestrator",
        summary="Lifecycle orchestration checkpoint persisted.",
        outcome=feedback_status,
        details={
            "risk_classification": state.get("risk_classification"),
            "approval_status": state.get("approval_status"),
            "execution_status": state.get("execution_status"),
            "feedback_status": feedback_status,
            "feedback_summary": state.get("feedback_summary"),
            "transition_log": transitions,
        },
        store_as_memory=feedback_status == "success",
    )
    await DecisionLogRepository(services.session).add(memory_log)

    return {
        "memory_log": memory_log,
        "memory_write_status": "written",
        "transition_log": _append_transition(
            state,
            node="memory_write",
            status="written",
            details={
                "decision_log_id": str(memory_log.id),
                "store_as_memory": memory_log.store_as_memory,
            },
        ),
    }
