"""Schemas for human approval workflow."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import ApprovalDecision
from app.schemas.action import ActionPlanRead
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class ApprovalBase(ORMBaseSchema):
    """Shared approval fields."""

    plan_id: UUID
    decided_by_name: str = Field(max_length=255)
    decision: ApprovalDecision
    comment: str | None = None
    decided_at: datetime


class ApprovalRequest(ORMBaseSchema):
    """Approve or reject a pending plan."""

    decision: ApprovalDecision
    comment: str | None = None


class ApprovalRead(EntityReadSchema, ApprovalBase):
    """Approval response payload."""


class ApprovalDecisionResponse(ORMBaseSchema):
    """Approval response containing updated plan status."""

    approval: ApprovalRead
    plan: ActionPlanRead
