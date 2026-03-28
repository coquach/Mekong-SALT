"""Phase 1 seed script."""

import asyncio
import logging

from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import AsyncSessionFactory, close_database_engine

logger = logging.getLogger(__name__)


async def run_seed() -> None:
    """Verify database connectivity and leave room for later seed data."""
    settings = get_settings()
    configure_logging(settings.log_level)

    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))

    logger.info("Phase 1 seed completed. No domain seed data is defined yet.")
    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(run_seed())
