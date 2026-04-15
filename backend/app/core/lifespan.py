"""Application startup and shutdown hooks."""

import asyncio
import logging
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.redis import RedisManager
from app.db.session import close_database_engine
from app.workers.active_monitoring_worker import start_active_monitoring_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Attach shared resources and clean them up on shutdown."""
    settings = get_settings()
    application.state.redis = RedisManager(settings.redis_url)
    application.state.active_monitoring_task = None

    logger.info(
        "Starting Mekong-SALT backend",
        extra={"environment": settings.app_env, "version": settings.app_version},
    )

    if settings.active_monitoring_enabled:
        application.state.active_monitoring_task = start_active_monitoring_worker(
            redis_manager=application.state.redis,
            settings=settings,
        )

    try:
        yield
    finally:
        task = application.state.active_monitoring_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await application.state.redis.close()
        await close_database_engine()
        logger.info("Stopped Mekong-SALT backend")

