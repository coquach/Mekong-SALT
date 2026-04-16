"""Approval domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.approval.workflow import decide_plan, list_plan_approvals

__all__ = [
    "decide_plan",
    "list_plan_approvals",
]
