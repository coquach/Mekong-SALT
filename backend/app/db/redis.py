"""Redis connection placeholder for future caching and workers."""

import json
import logging
from typing import Any

from fastapi import Request

from redis.asyncio import Redis, from_url

logger = logging.getLogger(__name__)


class RedisManager:
    """Lazy Redis client wrapper used by the application lifespan."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Redis | None = None

    @property
    def client(self) -> Redis:
        if self._client is None:
            self._client = from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def ping(self) -> bool:
        """Attempt a Redis ping without failing the application."""
        try:
            return bool(await self.client.ping())
        except Exception:
            logger.exception("Redis ping failed")
            return False

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Get a JSON document from Redis if available."""
        try:
            payload = await self.client.get(key)
        except Exception:
            logger.exception("Redis get failed for key %s", key)
            return None
        if payload is None:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Redis payload for key %s was not valid JSON", key)
            return None

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Store a JSON document in Redis with expiration."""
        try:
            await self.client.set(key, json.dumps(value), ex=ttl_seconds)
        except Exception:
            logger.exception("Redis set failed for key %s", key)

    async def close(self) -> None:
        """Close the Redis connection if it was created."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def get_redis_manager(request: Request) -> RedisManager | None:
    """Return the shared Redis manager when lifespan has attached it."""
    return getattr(request.app.state, "redis", None)

