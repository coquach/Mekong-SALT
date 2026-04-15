"""Reactive monitoring orchestration.

This module owns cross-service automation that should not live in an endpoint:
approval and simulated execution are consequences of a monitoring cycle, not
operator-triggered API actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.action import ActionPlan
from app.models.approval import Approval
from app.models.enums import ActionPlanStatus, ApprovalDecision
from app.schemas.action import SimulatedExecutionRequest
from app.schemas.approval import ApprovalRequest
from app.services.agent_execution_service import SimulatedExecutionBundle, execute_simulated_plan
from app.services.approval_service import decide_plan

ReactiveAdvanceStatus = Literal[
    "skipped_not_pending",
    "pending_approval",
    "approved",
    "executed",
]


@dataclass(slots=True)
class ReactiveAdvanceResult:
    """Result of advancing a plan through the reactive pipeline."""

    status: ReactiveAdvanceStatus
    plan: ActionPlan
    approval: Approval | None = None
    execution_bundle: SimulatedExecutionBundle | None = None
    reason: str | None = None


async def advance_plan_reactively(
    session: AsyncSession,
    *,
    plan: ActionPlan,
    settings: Settings,
) -> ReactiveAdvanceResult:
    """Advance a freshly generated plan without waiting for API triggers."""
    if plan.status is not ActionPlanStatus.PENDING_APPROVAL:
        return ReactiveAdvanceResult(
            status="skipped_not_pending",
            plan=plan,
            reason=f"Plan status is {plan.status.value}.",
        )

    if not settings.reactive_auto_approve_enabled:
        return ReactiveAdvanceResult(
            status="pending_approval",
            plan=plan,
            reason="Reactive auto-approval is disabled.",
        )

    approval, approved_plan = await decide_plan(
        session,
        plan_id=plan.id,
        payload=ApprovalRequest(
            decision=ApprovalDecision.APPROVED,
            comment="Approved automatically by the reactive monitoring pipeline.",
        ),
        actor_name="reactive-monitoring",
    )

    if not settings.reactive_auto_execute_enabled:
        return ReactiveAdvanceResult(
            status="approved",
            plan=approved_plan,
            approval=approval,
            reason="Reactive auto-execution is disabled.",
        )

    execution_bundle = await execute_simulated_plan(
        session,
        payload=SimulatedExecutionRequest(
            action_plan_id=approved_plan.id,
            idempotency_key=f"reactive-monitoring:{approved_plan.id}",
        ),
        actor_name="reactive-monitoring",
    )
    return ReactiveAdvanceResult(
        status="executed",
        plan=execution_bundle.plan,
        approval=approval,
        execution_bundle=execution_bundle,
    )

