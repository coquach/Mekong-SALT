"""Application startup and shutdown hooks."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.redis import RedisManager
from app.db.session import close_database_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Attach shared resources and clean them up on shutdown."""
    settings = get_settings()
    application.state.redis = RedisManager(settings.redis_url)

    logger.info(
        "Starting Mekong-SALT backend",
        extra={"environment": settings.app_env, "version": settings.app_version},
    )

    try:
        yield
    finally:
        await application.state.redis.close()
        await close_database_engine()
        logger.info("Stopped Mekong-SALT backend")

