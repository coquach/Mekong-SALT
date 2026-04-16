"""Repository helpers for persistent memory case retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import String, cast, desc, or_, select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory_case import MemoryCase
from app.repositories.base import AsyncRepository


class MemoryCaseRepository(AsyncRepository[MemoryCase]):
    """Memory case persistence and retrieval helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MemoryCase)

    async def is_table_ready(self) -> bool:
        """Return true when memory_cases table exists in the current database."""
        result = await self.session.scalar(
            text("SELECT to_regclass('public.memory_cases')")
        )
        return result is not None

    async def list_similar_cases(
        self,
        *,
        region_id: UUID,
        severity: str | None,
        query_terms: Sequence[str],
        limit: int = 6,
    ) -> list[MemoryCase]:
        """Return recent memory cases that match region/severity and query terms."""
        statement = select(MemoryCase).where(MemoryCase.region_id == region_id)
        if severity is not None:
            statement = statement.where(
                or_(
                    MemoryCase.severity == severity,
                    MemoryCase.severity.is_(None),
                )
            )

        term_predicates = []
        for term in query_terms:
            like = f"%{term}%"
            term_predicates.append(
                or_(
                    MemoryCase.objective.ilike(like),
                    MemoryCase.summary.ilike(like),
                    cast(MemoryCase.keywords, String).ilike(like),
                    cast(MemoryCase.context_payload, String).ilike(like),
                    cast(MemoryCase.action_payload, String).ilike(like),
                    cast(MemoryCase.outcome_payload, String).ilike(like),
                )
            )
        if term_predicates:
            statement = statement.where(or_(*term_predicates))

        result = await self.session.scalars(
            statement
            .order_by(desc(MemoryCase.occurred_at), desc(MemoryCase.created_at))
            .limit(limit)
        )
        return list(result.all())

    async def list_by_ids(self, case_ids: Sequence[UUID]) -> list[MemoryCase]:
        """Resolve memory cases by IDs for Vertex-neighbor hydration."""
        if not case_ids:
            return []
        result = await self.session.scalars(
            select(MemoryCase).where(MemoryCase.id.in_(case_ids))
        )
        return list(result.all())
