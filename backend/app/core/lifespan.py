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
from app.workers.replan_worker import start_replan_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Attach shared resources and clean them up on shutdown."""
    settings = get_settings()
    application.state.redis = RedisManager(settings.redis_url)
    application.state.active_monitoring_task = None
    application.state.mqtt_ingest_task = None
    application.state.pubsub_ingest_task = None
    application.state.replan_task = None

    logger.info(
        "Starting Mekong-SALT backend",
        extra={"environment": settings.app_env, "version": settings.app_version},
    )

    if settings.active_monitoring_enabled:
        application.state.active_monitoring_task = start_active_monitoring_worker(
            redis_manager=application.state.redis,
            settings=settings,
        )
        application.state.replan_task = start_replan_worker(
            redis_manager=application.state.redis,
            settings=settings,
        )
    if settings.mqtt_enabled and settings.iot_ingest_mode in {"mqtt", "hybrid"}:
        from app.workers.mqtt_ingest_worker import start_mqtt_ingest_worker

        application.state.mqtt_ingest_task = start_mqtt_ingest_worker(settings=settings)
    if settings.pubsub_enabled and settings.iot_ingest_mode in {"pubsub", "hybrid"}:
        from app.workers.pubsub_ingest_worker import start_pubsub_ingest_worker

        application.state.pubsub_ingest_task = start_pubsub_ingest_worker(settings=settings)

    try:
        yield
    finally:
        mqtt_task = application.state.mqtt_ingest_task
        if mqtt_task is not None:
            mqtt_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await mqtt_task
        pubsub_task = application.state.pubsub_ingest_task
        if pubsub_task is not None:
            pubsub_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await pubsub_task
        replan_task = application.state.replan_task
        if replan_task is not None:
            replan_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await replan_task
        task = application.state.active_monitoring_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await application.state.redis.close()
        await close_database_engine()
        logger.info("Stopped Mekong-SALT backend")

