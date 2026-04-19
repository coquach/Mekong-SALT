"""Schemas for knowledge documents and embedded chunks."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import DocumentStatus
from app.schemas.base import EntityReadSchema, ORMBaseSchema


class KnowledgeDocumentBase(ORMBaseSchema):
    """Shared knowledge document fields."""

    title: str = Field(max_length=255)
    source_uri: str | None = Field(default=None, max_length=500)
    document_type: str = Field(default="guideline", max_length=100)
    status: DocumentStatus = DocumentStatus.ACTIVE
    summary: str | None = None
    content_text: str
    tags: list[str] | None = None
    metadata_payload: dict[str, Any] | None = None


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """Schema for creating a knowledge document."""


class KnowledgeDocumentRead(EntityReadSchema, KnowledgeDocumentBase):
    """Schema for returning a knowledge document."""


class EmbeddedChunkBase(ORMBaseSchema):
    """Shared embedded chunk fields."""

    document_id: UUID
    chunk_index: int
    content_text: str
    token_count: int | None = None
    embedding: list[float]
    metadata_payload: dict[str, Any] | None = None


class EmbeddedChunkCreate(EmbeddedChunkBase):
    """Schema for creating an embedded chunk."""


class EmbeddedChunkRead(EntityReadSchema, EmbeddedChunkBase):
    """Schema for returning an embedded chunk."""

