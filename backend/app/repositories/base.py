"""Shared repository primitives."""

from collections.abc import Sequence
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AsyncRepository(Generic[ModelT]):
    """Small async repository base for common persistence operations."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def add(self, instance: ModelT) -> ModelT:
        """Add an instance to the current unit of work."""
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, entity_id: UUID) -> ModelT | None:
        """Load a single entity by primary key."""
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """List entities with simple pagination."""
        statement = select(self.model).offset(offset).limit(limit)
        result = await self.session.scalars(statement)
        return result.all()

    async def delete(self, instance: ModelT) -> None:
        """Delete an entity within the current unit of work."""
        await self.session.delete(instance)

    async def exists(self, statement: Select[tuple[ModelT]]) -> bool:
        """Check whether a statement returns at least one row."""
        result = await self.session.scalars(statement.limit(1))
        return result.first() is not None

