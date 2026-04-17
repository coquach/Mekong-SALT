"""Static corpus provider boundary for institutional knowledge retrieval/indexing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.services.rag.vertex_vector_search_service import VertexNeighbor, VertexVectorSearchService


@dataclass(slots=True)
class StaticCorpusNeighbor:
    """Canonical nearest-neighbor result from a static corpus provider."""

    datapoint_id: str
    distance: float


class StaticCorpusProvider(Protocol):
    """Provider contract for static knowledge corpus operations."""

    def is_configured(self) -> bool:
        """Return whether provider is configured."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for one or more texts."""

    async def upsert_datapoints(self, datapoints: list[dict[str, Any]]) -> None:
        """Upsert static corpus datapoints."""

    async def remove_datapoints(self, datapoint_ids: list[str]) -> None:
        """Remove static corpus datapoints."""

    async def find_neighbors(
        self,
        *,
        query_embedding: list[float],
        neighbor_count: int,
        restricts: dict[str, list[str]] | None = None,
    ) -> list[StaticCorpusNeighbor]:
        """Return nearest neighbors for the query embedding."""


class VertexStaticCorpusProvider:
    """Static corpus provider backed by Vertex embeddings + Vector Search."""

    def __init__(self, *, vector_service: VertexVectorSearchService | None = None) -> None:
        self._vector_service = vector_service or VertexVectorSearchService()

    def is_configured(self) -> bool:
        return self._vector_service.is_configured()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._vector_service.embed_texts(texts)

    async def upsert_datapoints(self, datapoints: list[dict[str, Any]]) -> None:
        await self._vector_service.upsert_datapoints(datapoints)

    async def remove_datapoints(self, datapoint_ids: list[str]) -> None:
        await self._vector_service.remove_datapoints(datapoint_ids)

    async def find_neighbors(
        self,
        *,
        query_embedding: list[float],
        neighbor_count: int,
        restricts: dict[str, list[str]] | None = None,
    ) -> list[StaticCorpusNeighbor]:
        neighbors: list[VertexNeighbor] = await self._vector_service.find_neighbors(
            query_embedding=query_embedding,
            neighbor_count=neighbor_count,
            restricts=restricts,
        )
        return [
            StaticCorpusNeighbor(datapoint_id=item.datapoint_id, distance=item.distance)
            for item in neighbors
        ]


class VertexRagEngineAdapterStaticCorpusProvider:
    """Static corpus provider adapter for Vertex RAG Engine integration.

    Transitional behavior currently delegates to Vector Search adapter while preserving
    a dedicated integration boundary for future managed-corpus ingestion APIs.
    """

    def __init__(self, *, vector_service: VertexVectorSearchService | None = None) -> None:
        self._fallback = VertexStaticCorpusProvider(vector_service=vector_service)

    def is_configured(self) -> bool:
        return self._fallback.is_configured()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._fallback.embed_texts(texts)

    async def upsert_datapoints(self, datapoints: list[dict[str, Any]]) -> None:
        enriched: list[dict[str, Any]] = []
        for item in datapoints:
            next_item = dict(item)
            restricts = dict(next_item.get("restricts") or {})
            restricts.setdefault("provider_path", ["vertex_rag_engine_adapter"])
            next_item["restricts"] = restricts
            enriched.append(next_item)
        await self._fallback.upsert_datapoints(enriched)

    async def remove_datapoints(self, datapoint_ids: list[str]) -> None:
        await self._fallback.remove_datapoints(datapoint_ids)

    async def find_neighbors(
        self,
        *,
        query_embedding: list[float],
        neighbor_count: int,
        restricts: dict[str, list[str]] | None = None,
    ) -> list[StaticCorpusNeighbor]:
        return await self._fallback.find_neighbors(
            query_embedding=query_embedding,
            neighbor_count=neighbor_count,
            restricts=restricts,
        )


def get_static_corpus_provider(
    *,
    settings=None,
    vector_service: VertexVectorSearchService | None = None,
) -> StaticCorpusProvider:
    """Return configured static corpus provider adapter."""
    provider_name = str(getattr(settings, "rag_static_corpus_provider", "vector_search")).strip().lower()
    if provider_name in {"vertex_rag_engine", "vertex_rag_engine_adapter"}:
        return VertexRagEngineAdapterStaticCorpusProvider(vector_service=vector_service)
    return VertexStaticCorpusProvider(vector_service=vector_service)


# Backward-compatible alias for older imports.
VertexRagEngineStaticCorpusProvider = VertexRagEngineAdapterStaticCorpusProvider
