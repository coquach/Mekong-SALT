"""Health service for liveness/readiness metadata."""

from __future__ import annotations

from typing import Literal

from sqlalchemy import text

from app.core.config import get_settings
from app.db.redis import RedisManager
from app.db.session import AsyncSessionFactory
from app.schemas.system import HealthPayload


async def get_health_status(*, mode: Literal["liveness", "readiness"] = "liveness") -> HealthPayload:
    """Return service health payload with optional dependency reachability checks.

    - liveness: static configuration status (fast, no network probes)
    - readiness: real dependency reachability checks (database/redis pings)
    """
    settings = get_settings()
    dependencies = {
        "database": "configured",
        "redis": "configured",
    }

    if mode == "readiness":
        dependencies["database"] = await _ping_database()
        dependencies["redis"] = await _ping_redis(settings.redis_url)

    return HealthPayload(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        dependencies=dependencies,
    )


async def _ping_database() -> str:
    """Check database reachability using a trivial query."""
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        return "ready"
    except Exception:
        return "unreachable"


async def _ping_redis(redis_url: str) -> str:
    """Check redis reachability with ping and close client cleanly."""
    manager = RedisManager(redis_url)
    try:
        ok = await manager.ping()
        return "ready" if ok else "unreachable"
    except Exception:
        return "unreachable"
    finally:
        await manager.close()

