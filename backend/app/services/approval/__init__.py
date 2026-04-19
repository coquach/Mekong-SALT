"""Approval domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.approval.workflow import decide_plan, list_plan_approvals
from app.services.approval.policy import (
    ApprovalGatePolicy,
    classify_risk_level,
    resolve_approval_gate_policy,
)

__all__ = [
    "ApprovalGatePolicy",
    "classify_risk_level",
    "decide_plan",
    "list_plan_approvals",
    "resolve_approval_gate_policy",
]
