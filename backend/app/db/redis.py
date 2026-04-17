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

    async def publish_signal(self, channel: str, payload: dict[str, Any] | None = None) -> None:
        """Publish a lightweight JSON signal for subscribers."""
        try:
            await self.client.publish(channel, json.dumps(payload or {}))
        except Exception:
            logger.exception("Redis publish failed for channel %s", channel)

    async def wait_for_signal(self, channel: str, timeout_seconds: float) -> bool:
        """Wait for one signal message, returning True when any payload is received."""
        pubsub = self.client.pubsub()
        try:
            await pubsub.subscribe(channel)
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=timeout_seconds,
            )
            return message is not None
        except Exception:
            logger.exception("Redis wait failed for channel %s", channel)
            return False
        finally:
            try:
                await pubsub.unsubscribe(channel)
            except Exception:
                logger.exception("Redis unsubscribe failed for channel %s", channel)
            await pubsub.aclose()

    async def acquire_lock(self, key: str, token: str, ttl_seconds: int) -> bool:
        """Acquire a short-lived Redis lock using SET NX EX semantics."""
        try:
            return bool(await self.client.set(key, token, ex=ttl_seconds, nx=True))
        except Exception:
            logger.exception("Redis lock acquire failed for key %s", key)
            return False

    async def release_lock(self, key: str, token: str) -> None:
        """Release a Redis lock only when the token still matches this worker."""
        try:
            current = await self.client.get(key)
            if current == token:
                await self.client.delete(key)
        except Exception:
            logger.exception("Redis lock release failed for key %s", key)

    async def close(self) -> None:
        """Close the Redis connection if it was created."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def get_redis_manager(request: Request) -> RedisManager | None:
    """Return the shared Redis manager when lifespan has attached it."""
    return getattr(request.app.state, "redis", None)

