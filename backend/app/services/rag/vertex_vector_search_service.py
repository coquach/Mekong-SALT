"""Vertex AI managed embedding + Vector Search adapter for RAG."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException


@dataclass(slots=True)
class VertexNeighbor:
    """Resolved neighbor from Vertex Vector Search."""

    datapoint_id: str
    distance: float


class VertexVectorSearchService:
    """Adapter for Vertex-managed embedding and nearest-neighbor retrieval."""

    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def is_configured(self) -> bool:
        """Return whether the minimum Vertex Vector Search config is present."""
        return bool(
            self._settings.vertex_ai_project
            and self._settings.vertex_vector_search_index
            and self._settings.vertex_vector_search_index_endpoint
            and self._settings.vertex_vector_search_deployed_index_id
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed input texts with Vertex-managed embedding model."""
        if not texts:
            return []

        project = self._settings.vertex_ai_project
        if not project:
            raise AppException(
                status_code=503,
                code="vertex_project_missing",
                message="RAG embedding requires VERTEX_AI_PROJECT.",
            )

        try:
            from google import genai
        except Exception as exc:  # pragma: no cover - dependency/runtime safety
            raise AppException(
                status_code=503,
                code="vertex_genai_dependency_missing",
                message="google-genai dependency is required for Vertex embeddings.",
            ) from exc

        try:
            client = genai.Client(
                vertexai=True,
                project=project,
                location=self._settings.vertex_ai_location,
            )
            response = await client.aio.models.embed_content(
                model=self._settings.rag_embedding_model,
                contents=texts,
            )
        except Exception as exc:
            raise AppException(
                status_code=503,
                code="vertex_embedding_failed",
                message="Vertex embedding request failed.",
            ) from exc

        vectors: list[list[float]] = []
        embeddings = getattr(response, "embeddings", None)
        if embeddings is None:
            single = getattr(response, "embedding", None)
            if single is not None:
                embeddings = [single]

        for item in embeddings or []:
            values = getattr(item, "values", None)
            if values is None:
                values = getattr(item, "embedding", None)
            if values is None:
                raise AppException(
                    status_code=502,
                    code="vertex_embedding_invalid_payload",
                    message="Vertex embedding payload is missing vector values.",
                )
            vectors.append([float(v) for v in values])

        if len(vectors) != len(texts):
            raise AppException(
                status_code=502,
                code="vertex_embedding_count_mismatch",
                message="Vertex embedding count does not match requested texts.",
            )
        return vectors

    async def upsert_datapoints(self, datapoints: list[dict[str, Any]]) -> None:
        """Upsert datapoints into Vertex Vector Search index."""
        if not datapoints:
            return
        if not self.is_configured():
            raise AppException(
                status_code=503,
                code="vertex_vector_search_not_configured",
                message=(
                    "Vertex Vector Search requires VERTEX_VECTOR_SEARCH_INDEX, "
                    "VERTEX_VECTOR_SEARCH_INDEX_ENDPOINT, and "
                    "VERTEX_VECTOR_SEARCH_DEPLOYED_INDEX_ID."
                ),
            )

        await asyncio.to_thread(self._sync_upsert_datapoints, datapoints)

    async def remove_datapoints(self, datapoint_ids: list[str]) -> None:
        """Remove datapoints from Vertex Vector Search index."""
        if not datapoint_ids:
            return
        if not self.is_configured():
            return
        await asyncio.to_thread(self._sync_remove_datapoints, datapoint_ids)

    async def find_neighbors(
        self,
        *,
        query_embedding: list[float],
        neighbor_count: int,
    ) -> list[VertexNeighbor]:
        """Query Vertex Vector Search for nearest neighbors."""
        if not self.is_configured():
            return []
        if not query_embedding:
            return []

        return await asyncio.to_thread(
            self._sync_find_neighbors,
            query_embedding,
            neighbor_count,
        )

    def _sync_upsert_datapoints(self, datapoints: list[dict[str, Any]]) -> None:
        try:
            from google.cloud import aiplatform_v1
        except Exception as exc:  # pragma: no cover - dependency/runtime safety
            raise AppException(
                status_code=503,
                code="vertex_aiplatform_dependency_missing",
                message="google-cloud-aiplatform dependency is required for Vector Search.",
            ) from exc

        client = aiplatform_v1.IndexServiceClient(
            client_options={"api_endpoint": f"{self._settings.vertex_ai_location}-aiplatform.googleapis.com"}
        )

        built: list[aiplatform_v1.IndexDatapoint] = []
        for item in datapoints:
            restricts = []
            for namespace, values in (item.get("restricts") or {}).items():
                if not values:
                    continue
                restricts.append(
                    aiplatform_v1.IndexDatapoint.Restriction(
                        namespace=namespace,
                        allow_list=[str(v) for v in values],
                    )
                )

            built.append(
                aiplatform_v1.IndexDatapoint(
                    datapoint_id=str(item["datapoint_id"]),
                    feature_vector=[float(v) for v in item["feature_vector"]],
                    restricts=restricts,
                )
            )

        request = aiplatform_v1.UpsertDatapointsRequest(
            index=self._settings.vertex_vector_search_index,
            datapoints=built,
        )
        client.upsert_datapoints(request=request)

    def _sync_find_neighbors(
        self,
        query_embedding: list[float],
        neighbor_count: int,
    ) -> list[VertexNeighbor]:
        try:
            from google.cloud import aiplatform_v1
        except Exception as exc:  # pragma: no cover - dependency/runtime safety
            raise AppException(
                status_code=503,
                code="vertex_aiplatform_dependency_missing",
                message="google-cloud-aiplatform dependency is required for Vector Search.",
            ) from exc

        match_client = aiplatform_v1.MatchServiceClient(
            client_options={"api_endpoint": f"{self._settings.vertex_ai_location}-aiplatform.googleapis.com"}
        )

        query = aiplatform_v1.FindNeighborsRequest.Query(
            datapoint=aiplatform_v1.IndexDatapoint(
                datapoint_id="query",
                feature_vector=[float(v) for v in query_embedding],
            ),
            neighbor_count=max(1, int(neighbor_count)),
        )

        request = aiplatform_v1.FindNeighborsRequest(
            index_endpoint=self._settings.vertex_vector_search_index_endpoint,
            deployed_index_id=self._settings.vertex_vector_search_deployed_index_id,
            queries=[query],
            return_full_datapoint=False,
        )
        response = match_client.find_neighbors(request=request)

        neighbors: list[VertexNeighbor] = []
        nearest = response.nearest_neighbors[0].neighbors if response.nearest_neighbors else []
        for item in nearest:
            datapoint = getattr(item, "datapoint", None)
            datapoint_id = getattr(datapoint, "datapoint_id", None)
            if not datapoint_id:
                continue
            neighbors.append(
                VertexNeighbor(
                    datapoint_id=str(datapoint_id),
                    distance=float(getattr(item, "distance", 0.0)),
                )
            )
        return neighbors

    def _sync_remove_datapoints(self, datapoint_ids: list[str]) -> None:
        try:
            from google.cloud import aiplatform_v1
        except Exception as exc:  # pragma: no cover - dependency/runtime safety
            raise AppException(
                status_code=503,
                code="vertex_aiplatform_dependency_missing",
                message="google-cloud-aiplatform dependency is required for Vector Search.",
            ) from exc

        client = aiplatform_v1.IndexServiceClient(
            client_options={"api_endpoint": f"{self._settings.vertex_ai_location}-aiplatform.googleapis.com"}
        )
        request = aiplatform_v1.RemoveDatapointsRequest(
            index=self._settings.vertex_vector_search_index,
            datapoint_ids=[str(item) for item in datapoint_ids],
        )
        client.remove_datapoints(request=request)
