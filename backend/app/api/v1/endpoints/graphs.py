"""Realtime graph stream endpoints."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.db.redis import RedisManager, get_redis_manager

router = APIRouter(prefix="/graphs", tags=["graphs"])
logger = logging.getLogger(__name__)


@router.get("/stream")
async def graph_stream(
    request: Request,
    graph_type: str | None = Query(default=None),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Stream live graph transition payloads from Redis pubsub."""

    async def _events():
        yield "retry: 2000\n\n"
        if redis_manager is None:
            while not await request.is_disconnected():
                yield ": keepalive\n\n"
                await asyncio.sleep(1.5)
            return

        pubsub = redis_manager.client.pubsub()
        channel = get_settings().graph_stream_channel
        try:
            await pubsub.subscribe(channel)
            while not await request.is_disconnected():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.5,
                )
                if message is None:
                    yield ": keepalive\n\n"
                    continue

                payload = _parse_pubsub_message(message.get("data"))
                if payload is None:
                    continue
                if graph_type is not None and payload.get("graph_type") != graph_type:
                    continue

                yield _format_sse(
                    event_name="graph_transition",
                    data=payload,
                )
        except Exception:
            logger.exception("Graph stream failed; falling back to keepalive only.")
            while not await request.is_disconnected():
                yield ": keepalive\n\n"
                await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            return
        finally:
            try:
                await pubsub.unsubscribe(channel)
            except Exception:
                pass
            await pubsub.aclose()

    return StreamingResponse(_events(), media_type="text/event-stream")


def _parse_pubsub_message(raw: object) -> dict | None:
    if not isinstance(raw, str):
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _format_sse(*, event_name: str, data: dict) -> str:
    return "\n".join(
        [
            f"event: {event_name}",
            f"data: {json.dumps(data)}",
        ]
    ) + "\n\n"
