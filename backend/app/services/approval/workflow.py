"""Approval workflow wrappers.

This module re-exports the current implementation without logic changes.
"""

from app.services.approval_service import decide_plan, list_plan_approvals

__all__ = [
    "decide_plan",
    "list_plan_approvals",
]
