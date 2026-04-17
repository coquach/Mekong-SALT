"""Vertex indexing helper for memory case semantic retrieval."""

from __future__ import annotations

from typing import Any

from app.models.memory_case import MemoryCase
from app.services.rag.vertex_vector_search_service import VertexVectorSearchService


class MemoryCaseVectorService:
    """Upsert and remove memory-case vectors in Vertex Vector Search."""

    def __init__(self, *, vector_service: VertexVectorSearchService | None = None) -> None:
        self._vector_service = vector_service or VertexVectorSearchService()

    def is_enabled(self) -> bool:
        """Return true when Vertex vector config is available."""
        return self._vector_service.is_configured()

    async def upsert_memory_case(self, memory_case: MemoryCase) -> None:
        """Project a memory case to text, embed, and upsert a Vertex datapoint."""
        if not self.is_enabled():
            return

        projection = self._build_projection_text(memory_case)
        vectors = await self._vector_service.embed_texts([projection])
        if not vectors:
            return

        datapoint = {
            "datapoint_id": str(memory_case.id),
            "feature_vector": vectors[0],
            "restricts": {
                "entity_type": ["memory_case"],
                "region_scope": [str(memory_case.region_id)],
                "severity": [str(memory_case.severity or "unknown")],
                "outcome_class": [str(memory_case.outcome_class)],
            },
        }
        await self._vector_service.upsert_datapoints([datapoint])

    async def remove_memory_case(self, memory_case_id: str) -> None:
        """Delete one memory-case datapoint from Vertex index."""
        if not self.is_enabled():
            return
        await self._vector_service.remove_datapoints([memory_case_id])

    def _build_projection_text(self, memory_case: MemoryCase) -> str:
        """Build retrieval-optimized text projection from structured memory-case fields."""
        context_payload = memory_case.context_payload or {}
        action_payload = memory_case.action_payload or {}
        outcome_payload = memory_case.outcome_payload or {}

        steps = action_payload.get("steps") or []
        action_types: list[str] = []
        for step in steps:
            value = str(step.get("action_type") or "").strip()
            if value:
                action_types.append(value)

        lines = [
            f"objective: {memory_case.objective or ''}",
            f"summary: {memory_case.summary}",
            f"severity: {memory_case.severity or 'unknown'}",
            f"outcome_class: {memory_case.outcome_class}",
            f"legacy_status: {memory_case.outcome_status_legacy or ''}",
            f"actions: {', '.join(action_types)}",
            f"keywords: {', '.join(memory_case.keywords or [])}",
            f"region_id: {memory_case.region_id}",
            f"station_id: {memory_case.station_id or ''}",
            f"context: {self._jsonish(context_payload)}",
            f"outcome: {self._jsonish(outcome_payload)}",
        ]
        return "\n".join(lines)

    def _jsonish(self, payload: dict[str, Any]) -> str:
        pairs: list[str] = []
        for key, value in payload.items():
            pairs.append(f"{key}={value}")
        return "; ".join(pairs)
