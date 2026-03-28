"""Redis connection placeholder for future caching and workers."""

import logging

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

    async def close(self) -> None:
        """Close the Redis connection if it was created."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

