"""Async SQLAlchemy engine and session management."""

import asyncio
import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

_engine_dispose_lock = asyncio.Lock()
_engine_disposed = False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for request-scoped usage."""
    session = AsyncSessionFactory()
    try:
        yield session
    except asyncio.CancelledError:
        # Client disconnect/cancel can interrupt request handling while session
        # is still in-flight. Roll back transaction state before propagating.
        if session.in_transaction():
            with contextlib.suppress(Exception):
                await asyncio.shield(session.rollback())
        raise
    except Exception:
        if session.in_transaction():
            with contextlib.suppress(Exception):
                await session.rollback()
        raise
    finally:
        # Shield close to reduce cancelled cleanup paths that can surface as
        # noisy pool termination errors.
        with contextlib.suppress(Exception):
            await asyncio.shield(session.close())


async def close_database_engine() -> None:
    """Dispose the shared database engine."""
    global _engine_disposed

    if _engine_disposed:
        return

    async with _engine_dispose_lock:
        if _engine_disposed:
            return

        # Detach the pool during shutdown without forcing asyncpg to terminate
        # every live connection immediately. This avoids noisy shutdown traces
        # when the process is already winding down.
        with contextlib.suppress(Exception):
            await engine.dispose(close=False)

        _engine_disposed = True

