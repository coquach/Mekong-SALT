"""Schemas for planning-time RAG retrieval contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import ORMBaseSchema


class RetrievalEvidence(ORMBaseSchema):
    """Single normalized evidence row used by planning."""

    rank: int = Field(ge=1)
    score: float
    snippet: str
    citation: dict[str, Any]
    metadata_filters: dict[str, str]
    evidence_type: str
    evidence_source: str
    title: str | None = None
    summary: str | None = None
    content_excerpt: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    source_uri: str | None = None
    incident_id: str | None = None
    risk_assessment_id: str | None = None
    memory_case_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    ranking_metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalProvenance(ORMBaseSchema):
    """Retrieval provenance for audit and replay."""

    generated_at: datetime
    retrieval_backend: str = "rag_retrieval_service"
    vector_search_enabled: bool
    vector_search_used: bool
    static_corpus_provider: str = "vector_search"
    local_fallback_enabled: bool
    local_fallback_used: bool
    source_counts: dict[str, int] = Field(default_factory=dict)
    total_candidates: int = 0


class RetrievalRankingMetadata(ORMBaseSchema):
    """Ranking and trace metadata shared across all evidence."""

    algorithm: str = "heuristic_rank_v1"
    score_version: str = "v1"
    max_evidence: int = Field(ge=1)
    top_k: int = Field(ge=1)
    query_terms: list[str] = Field(default_factory=list)
    sorted_descending: bool = True
    dedupe_applied: bool = True
    top_citations: list[dict[str, Any]] = Field(default_factory=list)


class RetrievalPolicyFlags(ORMBaseSchema):
    """Policy constraints attached to retrieved planning context."""

    simulation_only: bool = True
    requires_human_approval: bool = True
    allow_hardware_execution: bool = False
    evidence_minimum_required: int = 1
    deterministic_ranking: bool = True


class RetrievalContext(ORMBaseSchema):
    """Deterministic retrieval payload consumed by planning."""

    evidence: list[RetrievalEvidence] = Field(default_factory=list)
    provenance: RetrievalProvenance
    ranking_metadata: RetrievalRankingMetadata
    policy_flags: RetrievalPolicyFlags
