"""Plan approval workflow services."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.action import ActionPlan
from app.models.approval import Approval
from app.models.enums import ApprovalDecision, AuditEventType, IncidentStatus
from app.models.enums import ActionPlanStatus
from app.repositories.action import ActionPlanRepository
from app.repositories.approval import ApprovalRepository
from app.schemas.approval import ApprovalRequest
from app.services.audit_service import write_audit_log


async def decide_plan(
    session: AsyncSession,
    *,
    plan_id: UUID,
    payload: ApprovalRequest,
    actor_name: str = "supervisor",
) -> tuple[Approval, ActionPlan]:
    """Approve or reject a pending plan."""
    plan = await ActionPlanRepository(session).get_with_assessment(plan_id)
    if plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{plan_id}' was not found.",
        )
    if plan.status is not ActionPlanStatus.PENDING_APPROVAL:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="action_plan_not_pending_approval",
            message="Only pending-approval plans can be approved or rejected.",
        )

    approval = Approval(
        plan_id=plan.id,
        decided_by_name=actor_name,
        decision=payload.decision,
        comment=payload.comment,
        decided_at=datetime.now(UTC),
    )
    await ApprovalRepository(session).add(approval)

    if payload.decision is ApprovalDecision.APPROVED:
        plan.status = ActionPlanStatus.APPROVED
        if plan.incident is not None:
            plan.incident.status = IncidentStatus.APPROVED
    else:
        plan.status = ActionPlanStatus.REJECTED
        if plan.incident is not None:
            plan.incident.status = IncidentStatus.PENDING_PLAN

    await write_audit_log(
        session,
        event_type=AuditEventType.APPROVAL,
        actor_name=actor_name,
        region_id=plan.region_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        summary=f"Plan {payload.decision.value} by {actor_name}.",
        payload={"comment": payload.comment},
    )
    await session.commit()
    await session.refresh(approval)
    await session.refresh(plan)
    return approval, plan


async def list_plan_approvals(session: AsyncSession, plan_id: UUID) -> list[Approval]:
    """Return approval history for a plan."""
    return await ApprovalRepository(session).list_for_plan(plan_id)
