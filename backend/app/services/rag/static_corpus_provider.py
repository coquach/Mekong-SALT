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


def get_static_corpus_provider(
    *,
    vector_service: VertexVectorSearchService | None = None,
) -> StaticCorpusProvider:
    """Return configured static corpus provider adapter."""
    return VertexStaticCorpusProvider(vector_service=vector_service)
