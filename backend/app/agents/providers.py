"""LLM provider abstractions for agent planning."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any

from google import genai
from google.genai import types as genai_types
import ollama

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.schemas.agent import GeneratedActionPlan


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
    """Gemini provider using the Google GenAI SDK."""

    name = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        if settings.gemini_api_key is None:
            raise AppException(
                status_code=503,
                code="gemini_api_key_missing",
                message="Gemini provider is not configured.",
            )
        self._client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
        self._model = settings.gemini_model
        self._temperature = settings.llm_temperature

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a plan using Gemini structured JSON output."""
        prompt = _build_plan_prompt(objective=objective, context=context)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=self._temperature,
                    response_mime_type="application/json",
                    response_json_schema=GeneratedActionPlan.model_json_schema(),
                ),
            )
        except Exception as exc:
            raise AppException(
                status_code=503,
                code="gemini_generation_failed",
                message="Gemini plan generation failed.",
            ) from exc

        payload = getattr(response, "text", None)
        if not payload:
            raise AppException(
                status_code=502,
                code="gemini_empty_response",
                message="Gemini did not return a structured plan.",
            )
        try:
            return GeneratedActionPlan.model_validate_json(payload)
        except Exception as exc:
            raise AppException(
                status_code=502,
                code="gemini_invalid_plan_payload",
                message="Gemini returned an invalid plan payload.",
            ) from exc


class OllamaProvider(PlanProvider):
    """Ollama provider using JSON schema-constrained chat output."""

    name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = ollama.AsyncClient(host=settings.ollama_base_url)
        self._model = settings.ollama_model
        self._temperature = settings.llm_temperature

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a plan using Ollama structured JSON output."""
        prompt = _build_plan_prompt(objective=objective, context=context)
        try:
            response = await self._client.chat(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a planning assistant for Mekong-SALT. "
                            "Return only valid JSON matching the requested schema."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                format=GeneratedActionPlan.model_json_schema(),
                options={"temperature": self._temperature},
            )
        except Exception as exc:
            raise AppException(
                status_code=503,
                code="ollama_generation_failed",
                message="Ollama plan generation failed.",
            ) from exc

        payload = response.message.content if response.message else None
        if not payload:
            raise AppException(
                status_code=502,
                code="ollama_empty_response",
                message="Ollama did not return a structured plan.",
            )
        try:
            return GeneratedActionPlan.model_validate_json(payload)
        except Exception as exc:
            raise AppException(
                status_code=502,
                code="ollama_invalid_plan_payload",
                message="Ollama returned an invalid plan payload.",
            ) from exc


def get_plan_provider(provider_name: str | None = None) -> PlanProvider:
    """Resolve the configured planning provider implementation."""
    settings = get_settings()
    resolved = provider_name or settings.llm_provider
    if resolved == "mock":
        return MockProvider()
    if resolved == "gemini":
        return GeminiProvider()
    if resolved == "ollama":
        return OllamaProvider()
    raise AppException(
        status_code=400,
        code="unsupported_plan_provider",
        message=f"Unsupported plan provider '{resolved}'.",
    )


def _build_plan_prompt(*, objective: str, context: dict[str, Any]) -> str:
    """Build a compact prompt for structured plan generation."""
    serialized_context = json.dumps(context, ensure_ascii=True, indent=2, default=str)
    return (
        "Generate a salinity response plan for Mekong-SALT.\n"
        "Requirements:\n"
        "- Use only simulated or informational actions.\n"
        "- Allowed action types: send_alert, notify-farmers, wait-safe-window, "
        "close_gate, open_gate, start_pump, stop_pump, close-gate-simulated, start-pump-simulated.\n"
        "- All actions are simulated in MVP and require human approval before execution.\n"
        "- Keep the plan practical for an MVP decision-support system.\n"
        "- Return 2 to 5 ordered steps.\n"
        "- Every step must include action_type, title, instructions, rationale, and simulated=true.\n"
        f"Objective: {objective}\n"
        f"Context:\n{serialized_context}\n"
    )
