"""Background worker for feedback-driven replan requests."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.db.redis import RedisManager
from app.db.session import AsyncSessionFactory, close_database_engine
from app.services.domain_event_service import list_domain_events_after_cursor
from app.services.replan_service import (
    REPLAN_REQUEST_EVENT_TYPE,
    handle_replan_requested_event,
)

logger = logging.getLogger(__name__)
REPLAN_WORKER_CURSOR_KEY = "mekong-salt:replan-worker:cursor"


def start_replan_worker(
    *,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> asyncio.Task[None]:
    """Start the long-running worker loop as an application background task."""
    resolved_settings = settings or get_settings()
    return asyncio.create_task(
        replan_loop(
            redis_manager=redis_manager,
            settings=resolved_settings,
        ),
        name="replan-worker",
    )


async def replan_loop(
    *,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> None:
    """Continuously poll the domain-event stream for replan requests."""
    resolved_settings = settings or get_settings()
    cursor = await _load_cursor(redis_manager)
    logger.info(
        "Replan worker started",
        extra={
            "poll_seconds": resolved_settings.active_monitoring_poll_seconds,
            "cursor": cursor,
        },
    )
    while True:
        try:
            async with AsyncSessionFactory() as session:
                cursor = await _process_pending_replan_events(
                    session,
                    cursor=cursor,
                    redis_manager=redis_manager,
                    settings=resolved_settings,
                )
                await _save_cursor(redis_manager, cursor)
        except asyncio.CancelledError:
            logger.info("Replan worker cancellation requested")
            raise
        except Exception:
            logger.exception("Replan worker tick failed")

        if redis_manager is not None:
            await redis_manager.wait_for_signal(
                resolved_settings.domain_event_signal_channel,
                timeout_seconds=float(resolved_settings.active_monitoring_poll_seconds),
            )
        else:
            await asyncio.sleep(resolved_settings.active_monitoring_poll_seconds)


async def _process_pending_replan_events(
    session,
    *,
    cursor: int,
    redis_manager: RedisManager | None,
    settings: Settings,
) -> int:
    events = await list_domain_events_after_cursor(
        session,
        cursor=cursor,
        limit=100,
    )
    if not events:
        return cursor

    current_cursor = cursor
    for event in events:
        current_cursor = event.sequence
        if event.event_type != REPLAN_REQUEST_EVENT_TYPE:
            continue

        result = await handle_replan_requested_event(
            session,
            event=event,
            redis_manager=redis_manager,
            settings=settings,
        )
        logger.info(
            "Processed replan request event",
            extra={
                "event_sequence": event.sequence,
                "status": result.status,
                "reason": result.reason,
                "plan_id": (
                    str(result.plan_bundle.plan.id)
                    if result.plan_bundle is not None
                    else None
                ),
                "lifecycle_status": result.lifecycle_status,
            },
        )
        await _save_cursor(redis_manager, current_cursor)

    return current_cursor


async def _load_cursor(redis_manager: RedisManager | None) -> int:
    if redis_manager is None:
        return 0
    payload = await redis_manager.get_json(REPLAN_WORKER_CURSOR_KEY)
    if not payload:
        return 0
    cursor = payload.get("cursor")
    try:
        return int(cursor)
    except (TypeError, ValueError):
        return 0


async def _save_cursor(redis_manager: RedisManager | None, cursor: int) -> None:
    if redis_manager is None:
        return
    await redis_manager.set_json(
        REPLAN_WORKER_CURSOR_KEY,
        {"cursor": int(cursor), "updated_at": "cursor-advanced"},
        ttl_seconds=60 * 60 * 24 * 30,
    )


async def main() -> None:
    """Run the worker as a standalone process with `python -m app.workers.replan_worker`."""
    settings = get_settings()
    redis_manager = RedisManager(settings.redis_url)
    try:
        await replan_loop(redis_manager=redis_manager, settings=settings)
    finally:
        await redis_manager.close()
        await close_database_engine()


if __name__ == "__main__":
    asyncio.run(main())
