"""Execution domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.execution.simulated import (
    SimulatedExecutionBundle,
    execute_simulated_plan,
    list_action_logs,
)

__all__ = [
    "SimulatedExecutionBundle",
    "execute_simulated_plan",
    "list_action_logs",
]
