"""Knowledge base persistence models."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DocumentStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Document stored for later retrieval and planning context."""

    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(500), nullable=True, unique=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, default="guideline")
    status: Mapped[DocumentStatus] = mapped_column(
        enum_type(DocumentStatus, "document_status"),
        nullable=False,
        default=DocumentStatus.ACTIVE,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    content_text: Mapped[str] = mapped_column(Text(), nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    source_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    effective_date: Mapped[date | None] = mapped_column(Date(), nullable=True, index=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    index_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_document_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_sync_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="pending",
        index=True,
    )
    provider_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    chunks = relationship(
        "EmbeddedChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class EmbeddedChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Vectorized chunk derived from a knowledge document."""

    __tablename__ = "embedded_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_embedded_chunks_document_chunk"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text(), nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="chunks")
