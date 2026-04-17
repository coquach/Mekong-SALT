"""Gemini planner adapter with Vertex-first configuration support."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

from google import genai
from google.genai import types as genai_types

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.schemas.agent import GeneratedActionPlan
from app.services.llm.planner_interface import PlannerInterface


class PlanPromptBuilder(Protocol):
    """Boundary for planner prompt construction."""

    def build(self, *, objective: str, context: dict[str, Any]) -> str:
        """Build planner prompt text from objective and context."""


class VertexPlanPromptBuilder:
    """Default prompt builder for Vertex Gemini planning."""

    def build(self, *, objective: str, context: dict[str, Any]) -> str:
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
            "- Return all human-readable fields in Vietnamese, including objective, summary, context_summary, risk_summary, assumptions, reasoning_summary, title, instructions, and rationale.\n"
            "- Keep JSON keys and action_type values in English.\n"
            "- Every step must include action_type, title, instructions, rationale, and simulated=true.\n"
            f"Objective: {objective}\n"
            f"Context:\n{serialized_context}\n"
        )


class VertexGeminiPlannerAdapter(PlannerInterface):
    """LLM planner adapter for Vertex AI Gemini plan generation."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        prompt_builder: PlanPromptBuilder | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._prompt_builder = prompt_builder or VertexPlanPromptBuilder()
        self._client = self._build_client(self._settings)

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate one structured plan via Gemini using a JSON schema contract."""
        prompt = self._prompt_builder.build(objective=objective, context=context)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=self._settings.llm_temperature,
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

    @staticmethod
    def _build_client(settings: Settings):
        """Create a Gemini client in Vertex mode only."""
        project = settings.vertex_ai_project or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise AppException(
                status_code=503,
                code="vertex_project_missing",
                message="Vertex Gemini planner requires VERTEX_AI_PROJECT or GOOGLE_CLOUD_PROJECT.",
            )
        try:
            return genai.Client(
                vertexai=True,
                project=project,
                location=settings.vertex_ai_location,
            )
        except Exception as exc:
            raise AppException(
                status_code=503,
                code="vertex_client_init_failed",
                message="Vertex Gemini client initialization failed.",
            ) from exc


def build_plan_prompt(*, objective: str, context: dict[str, Any]) -> str:
    """Backward-compatible function wrapper for prompt construction."""
    return VertexPlanPromptBuilder().build(objective=objective, context=context)
