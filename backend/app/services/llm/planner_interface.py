"""Planner adapter interface for LLM-backed plan generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.agent import GeneratedActionPlan


class PlannerInterface(ABC):
    """Abstract boundary for planning adapters used by provider shims."""

    @abstractmethod
    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a structured action plan from objective and retrieved context."""
