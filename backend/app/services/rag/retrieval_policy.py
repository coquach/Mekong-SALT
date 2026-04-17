"""Retrieval lane policy and defaults derived from application settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetrievalLanePolicy:
    """Runtime policy controlling retrieval lane behavior."""

    use_vector_search: bool
    enable_local_fallback: bool
    top_k: int
    static_local_limit: int
    memory_local_limit: int
    memory_vector_max_evidence: int
    memory_vector_timeout_seconds: float
    vector_neighbor_multiplier: int
    vector_neighbor_floor: int


def build_retrieval_lane_policy(settings) -> RetrievalLanePolicy:
    """Build retrieval policy from settings with robust defaults."""
    return RetrievalLanePolicy(
        use_vector_search=bool(getattr(settings, "rag_use_vertex_vector_search", True)),
        enable_local_fallback=bool(getattr(settings, "rag_enable_local_fallback", True)),
        top_k=max(1, int(getattr(settings, "rag_retrieval_top_k", 8))),
        static_local_limit=max(1, int(getattr(settings, "rag_static_local_limit", 4))),
        memory_local_limit=max(1, int(getattr(settings, "rag_memory_local_limit", 4))),
        memory_vector_max_evidence=max(1, int(getattr(settings, "rag_memory_vector_max_evidence", 4))),
        memory_vector_timeout_seconds=max(
            0.1,
            float(getattr(settings, "rag_memory_vector_timeout_seconds", 2.5)),
        ),
        vector_neighbor_multiplier=max(1, int(getattr(settings, "rag_vector_neighbor_multiplier", 2))),
        vector_neighbor_floor=max(1, int(getattr(settings, "rag_vector_neighbor_floor", 12))),
    )
