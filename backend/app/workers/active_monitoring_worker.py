"""Background worker for goal-driven active monitoring."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.db.redis import RedisManager
from app.db.session import AsyncSessionFactory, close_database_engine
from app.services.active_monitoring_service import run_due_monitoring_goals

logger = logging.getLogger(__name__)


def start_active_monitoring_worker(
    *,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> asyncio.Task[None]:
    """Start the long-running worker loop as an application background task."""
    resolved_settings = settings or get_settings()
    return asyncio.create_task(
        active_monitoring_loop(
            redis_manager=redis_manager,
            settings=resolved_settings,
        ),
        name="active-monitoring-worker",
    )


async def active_monitoring_loop(
    *,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> None:
    """Continuously poll active goals and run due monitoring cycles."""
    resolved_settings = settings or get_settings()
    logger.info(
        "Active monitoring worker started",
        extra={
            "mode": resolved_settings.active_monitoring_mode,
            "poll_seconds": resolved_settings.active_monitoring_poll_seconds,
        },
    )
    while True:
        try:
            async with AsyncSessionFactory() as session:
                tick = await run_due_monitoring_goals(
                    session,
                    redis_manager=redis_manager,
                    settings=resolved_settings,
                )
            logger.info(
                "Active monitoring worker tick completed",
                extra={
                    "scanned": tick.scanned,
                    "due": tick.due,
                    "locked": tick.locked,
                    "results": [
                        {"goal_id": str(result.goal_id), "status": result.status}
                        for result in tick.results
                    ],
                },
            )
        except asyncio.CancelledError:
            logger.info("Active monitoring worker cancellation requested")
            raise
        except Exception:
            logger.exception("Active monitoring worker tick failed")

        await asyncio.sleep(resolved_settings.active_monitoring_poll_seconds)


async def main() -> None:
    """Run the worker as a standalone process with `python -m app.workers.active_monitoring_worker`."""
    settings = get_settings()
    redis_manager = RedisManager(settings.redis_url)
    try:
        await active_monitoring_loop(redis_manager=redis_manager, settings=settings)
    finally:
        await redis_manager.close()
        await close_database_engine()


if __name__ == "__main__":
    asyncio.run(main())
