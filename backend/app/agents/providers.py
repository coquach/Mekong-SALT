"""LLM provider abstractions for agent planning."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.schemas.agent import GeneratedActionPlan
from app.services.llm import VertexGeminiPlannerAdapter


class PlanProvider(ABC):
    """Base interface for planning providers."""

    name: str

    @abstractmethod
    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a structured plan for the given objective and context."""


class MockProvider(PlanProvider):
    """Deterministic planner for local demos and tests."""

    name = "mock"

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a structured plan without calling an external LLM."""
        assessment = context.get("assessment") or {}
        risk_level = assessment.get("risk_level", "warning")
        mitigation_action = (
            "close_gate"
            if risk_level in {"danger", "critical"}
            else "send_alert"
        )
        return GeneratedActionPlan.model_validate(
            {
                "objective": objective,
                "summary": "Coordinate salinity response with operator approval before any simulated action.",
                "context_summary": "Latest sensor, weather, and rules context were assembled for the incident.",
                "risk_summary": assessment.get("summary", "Salinity risk requires operator review."),
                "confidence_score": 0.76,
                "assumptions": [
                    "Sensor readings are recent enough for MVP planning.",
                    "All device actions are simulated and require human approval.",
                ],
                "reasoning_summary": "Threshold risk and recent trend suggest prompt notification and simulated mitigation.",
                "steps": [
                    {
                        "step_index": 1,
                        "action_type": "send_alert",
                        "priority": 1,
                        "title": "Send operator and farmer alert",
                        "instructions": "Notify dashboard, SMS mock, Zalo mock, and email mock recipients.",
                        "rationale": "Stakeholders need an immediate advisory before changing intake behavior.",
                        "simulated": True,
                    },
                    {
                        "step_index": 2,
                        "action_type": mitigation_action,
                        "priority": 2,
                        "title": "Simulate hydraulic mitigation",
                        "instructions": "Run the mock execution pathway and record the outcome.",
                        "rationale": "MVP execution must remain simulated until operators approve hardware integration.",
                        "simulated": True,
                    },
                    {
                        "step_index": 3,
                        "action_type": "stop_pump",
                        "priority": 3,
                        "title": "Confirm safe intake pause",
                        "instructions": "Simulate a temporary pump stop if intake salinity remains elevated.",
                        "rationale": "A conservative intake pause can reduce exposure during salinity peaks.",
                        "simulated": True,
                    },
                ],
            }
        )


class GeminiProvider(PlanProvider):
    """Compatibility shim delegating Gemini planning to LLM service adapter."""

    name = "gemini"

    def __init__(self) -> None:
        self._adapter = VertexGeminiPlannerAdapter()

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a plan via centralized LLM adapter boundary."""
        return await self._adapter.generate_plan(objective=objective, context=context)


def get_plan_provider(provider_name: str | None = None) -> PlanProvider:
    """Resolve the configured planning provider implementation."""
    _ = provider_name
    settings = get_settings()
    if settings.llm_provider != "gemini":
        raise AppException(
            status_code=500,
            code="invalid_llm_provider_configuration",
            message="Runtime configuration must use Gemini provider.",
        )
    return GeminiProvider()
