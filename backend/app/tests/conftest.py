"""Shared test fixtures."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import engine, get_db_session
from app.main import app
from app.models.enums import StationStatus
from app.models.region import Region
from app.models.sensor import SensorReading, SensorStation


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a rollback-isolated async session for API tests."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        async with session_factory() as session:
            yield session
        await transaction.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client with the DB session dependency overridden."""

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_sensor_data(db_session: AsyncSession) -> dict[str, object]:
    """Insert a small region/station/reading graph for sensor API tests."""
    now = datetime.now(UTC)
    region = Region(
        code=f"TEST-REGION-{uuid4().hex[:8]}",
        name="Test Monitoring Region",
        province="Tien Giang",
        crop_profile={"dominant_crops": ["rice"]},
    )
    station_a = SensorStation(
        region=region,
        code=f"TEST-STATION-A-{uuid4().hex[:6]}",
        name="Test Station A",
        station_type="salinity-water-level",
        status=StationStatus.ACTIVE,
        latitude=Decimal("10.100001"),
        longitude=Decimal("106.100001"),
    )
    station_b = SensorStation(
        region=region,
        code=f"TEST-STATION-B-{uuid4().hex[:6]}",
        name="Test Station B",
        station_type="salinity-water-level",
        status=StationStatus.ACTIVE,
        latitude=Decimal("10.200001"),
        longitude=Decimal("106.200001"),
    )
    reading_a_old = SensorReading(
        station=station_a,
        recorded_at=now - timedelta(hours=2),
        salinity_dsm=Decimal("2.20"),
        water_level_m=Decimal("1.10"),
        temperature_c=Decimal("28.00"),
    )
    reading_a_latest = SensorReading(
        station=station_a,
        recorded_at=now - timedelta(minutes=15),
        salinity_dsm=Decimal("3.40"),
        water_level_m=Decimal("1.45"),
        temperature_c=Decimal("29.10"),
    )
    reading_b_latest = SensorReading(
        station=station_b,
        recorded_at=now - timedelta(minutes=10),
        salinity_dsm=Decimal("1.80"),
        water_level_m=Decimal("0.95"),
        temperature_c=Decimal("28.50"),
    )
    db_session.add_all(
        [region, station_a, station_b, reading_a_old, reading_a_latest, reading_b_latest]
    )
    await db_session.commit()
    return {
        "region": region,
        "station_a": station_a,
        "station_b": station_b,
        "reading_a_old": reading_a_old,
        "reading_a_latest": reading_a_latest,
        "reading_b_latest": reading_b_latest,
        "now": now,
    }

