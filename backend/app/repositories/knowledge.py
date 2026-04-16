"""Repositories for knowledge retrieval and similar-case lookup."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import String, cast, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DocumentStatus, RiskLevel
from app.models.incident import Incident
from app.models.knowledge import EmbeddedChunk, KnowledgeDocument
from app.repositories.base import AsyncRepository


class KnowledgeDocumentRepository(AsyncRepository[KnowledgeDocument]):
    """Knowledge document query helpers used by planning-time retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, KnowledgeDocument)

    async def get_by_source_uri(self, source_uri: str) -> KnowledgeDocument | None:
        """Return one knowledge document by stable source URI."""
        result = await self.session.scalars(
            select(KnowledgeDocument).where(KnowledgeDocument.source_uri == source_uri)
        )
        return result.first()

    async def list_ranked_chunk_candidates(
        self,
        *,
        category: str,
        query_terms: Sequence[str],
        limit: int = 6,
    ) -> list[tuple[EmbeddedChunk, KnowledgeDocument]]:
        """Return active chunk candidates for one retrieval category."""
        statement = (
            select(EmbeddedChunk, KnowledgeDocument)
            .join(KnowledgeDocument, EmbeddedChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.status == DocumentStatus.ACTIVE)
        )

        if category == "sop":
            statement = statement.where(
                or_(
                    func.lower(KnowledgeDocument.document_type).in_(
                        ["sop", "guideline", "procedure", "protocol", "playbook"]
                    ),
                    KnowledgeDocument.title.ilike("%sop%"),
                    KnowledgeDocument.title.ilike("%guideline%"),
                    cast(KnowledgeDocument.tags, String).ilike("%sop%"),
                    cast(KnowledgeDocument.tags, String).ilike("%procedure%"),
                )
            )
        elif category == "threshold":
            statement = statement.where(
                or_(
                    func.lower(KnowledgeDocument.document_type).in_(
                        ["threshold", "policy", "rule", "guideline"]
                    ),
                    KnowledgeDocument.title.ilike("%threshold%"),
                    KnowledgeDocument.title.ilike("%critical%"),
                    KnowledgeDocument.content_text.ilike("%dsm%"),
                    cast(KnowledgeDocument.tags, String).ilike("%threshold%"),
                    cast(KnowledgeDocument.tags, String).ilike("%salinity%"),
                )
            )

        term_predicates = []
        for term in query_terms:
            like = f"%{term}%"
            term_predicates.append(
                or_(
                    KnowledgeDocument.title.ilike(like),
                    KnowledgeDocument.summary.ilike(like),
                    EmbeddedChunk.content_text.ilike(like),
                    cast(KnowledgeDocument.tags, String).ilike(like),
                )
            )
        if term_predicates:
            statement = statement.where(or_(*term_predicates))

        statement = statement.order_by(
            desc(KnowledgeDocument.updated_at),
            EmbeddedChunk.chunk_index,
        ).limit(max(limit * 3, limit))

        rows = (await self.session.execute(statement)).all()
        return [(row[0], row[1]) for row in rows]

    async def list_chunks_with_documents_by_ids(
        self,
        chunk_ids: Sequence[UUID],
    ) -> list[tuple[EmbeddedChunk, KnowledgeDocument]]:
        """Resolve chunks and their documents by embedded chunk IDs."""
        if not chunk_ids:
            return []

        rows = (
            await self.session.execute(
                select(EmbeddedChunk, KnowledgeDocument)
                .join(KnowledgeDocument, EmbeddedChunk.document_id == KnowledgeDocument.id)
                .where(
                    EmbeddedChunk.id.in_(chunk_ids),
                    KnowledgeDocument.status == DocumentStatus.ACTIVE,
                )
            )
        ).all()
        return [(row[0], row[1]) for row in rows]

    async def list_chunk_ids_for_document(self, document_id: UUID) -> list[UUID]:
        """Return all chunk IDs for one knowledge document."""
        result = await self.session.scalars(
            select(EmbeddedChunk.id)
            .where(EmbeddedChunk.document_id == document_id)
            .order_by(EmbeddedChunk.chunk_index)
        )
        return list(result.all())

    async def count_chunks_for_document(self, document_id: UUID) -> int:
        """Return embedded chunk count for one knowledge document."""
        result = await self.session.scalar(
            select(func.count())
            .select_from(EmbeddedChunk)
            .where(EmbeddedChunk.document_id == document_id)
        )
        return int(result or 0)

    async def delete_chunks_for_document(self, document_id: UUID) -> None:
        """Delete all embedded chunks for one knowledge document."""
        await self.session.execute(
            delete(EmbeddedChunk).where(EmbeddedChunk.document_id == document_id)
        )


class SimilarCaseRepository(AsyncRepository[Incident]):
    """Incident query helpers used for case-based retrieval context."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Incident)

    async def list_similar_incidents(
        self,
        *,
        region_id: UUID,
        severity: RiskLevel,
        exclude_assessment_id: UUID | None = None,
        limit: int = 4,
    ) -> list[Incident]:
        """Return recent incidents in the same region and severity bucket."""
        statement = select(Incident).where(
            Incident.region_id == region_id,
            Incident.severity == severity,
        )
        if exclude_assessment_id is not None:
            statement = statement.where(Incident.risk_assessment_id != exclude_assessment_id)

        result = await self.session.scalars(
            statement
            .order_by(desc(Incident.opened_at), desc(Incident.created_at))
            .limit(limit)
        )
        return list(result.all())
