"""Focused tests for Earth Engine spatial context adapter behavior."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.earth_engine_service import get_or_fetch_earth_engine_context


class _FakeRedisManager:
    def __init__(self, cached_payload: dict | None = None) -> None:
        self.cached_payload = cached_payload
        self.last_get_key: str | None = None
        self.last_set: tuple[str, dict, int] | None = None

    async def get_json(self, key: str):
        self.last_get_key = key
        return self.cached_payload

    async def set_json(self, key: str, value: dict, ttl_seconds: int) -> None:
        self.last_set = (key, value, ttl_seconds)


def _build_settings():
    return SimpleNamespace(
        earth_engine_enabled=True,
        external_context_cache_ttl_seconds=600,
        earth_engine_region_buffer_m=3000,
        earth_engine_default_dataset="COPERNICUS/S2_SR_HARMONIZED",
        earth_engine_project_id=None,
        earth_engine_service_account_email=None,
        earth_engine_service_account_key_path=None,
    )


def _build_region_station_weather():
    region = SimpleNamespace(
        id=uuid4(),
        code="REG-01",
    )
    station = SimpleNamespace(
        id=uuid4(),
        code="ST-01",
        latitude=Decimal("10.1234"),
        longitude=Decimal("106.4321"),
    )
    weather_snapshot = SimpleNamespace(
        wind_speed_mps=Decimal("8.0"),
        tide_level_m=Decimal("2.0"),
    )
    return region, station, weather_snapshot


@pytest.mark.asyncio
async def test_get_or_fetch_earth_engine_context_returns_cache_hit(monkeypatch):
    region, station, weather_snapshot = _build_region_station_weather()
    redis_manager = _FakeRedisManager(
        cached_payload={
            "source": "earth-engine",
            "fallback_used": False,
            "dataset": "COPERNICUS/S2_SR_HARMONIZED",
        }
    )

    monkeypatch.setattr("app.services.earth_engine_service.get_settings", _build_settings)

    async def should_not_fetch(*args, **kwargs):
        raise AssertionError("Fetch path must not run when cache payload exists.")

    monkeypatch.setattr(
        "app.services.earth_engine_service._fetch_with_fallback",
        should_not_fetch,
    )

    payload = await get_or_fetch_earth_engine_context(
        region=region,
        station=station,
        weather_snapshot=weather_snapshot,
        redis_manager=redis_manager,
    )

    assert payload is not None
    assert payload["cache_hit"] is True
    assert payload["source"] == "earth-engine"
    assert redis_manager.last_get_key is not None
    assert redis_manager.last_set is None


@pytest.mark.asyncio
async def test_get_or_fetch_earth_engine_context_sets_fallback_reason(monkeypatch):
    region, station, weather_snapshot = _build_region_station_weather()
    redis_manager = _FakeRedisManager(cached_payload=None)

    monkeypatch.setattr("app.services.earth_engine_service.get_settings", _build_settings)

    async def failing_query(**kwargs):
        raise RuntimeError("ee backend unavailable")

    monkeypatch.setattr(
        "app.services.earth_engine_service._query_earth_engine",
        failing_query,
    )

    payload = await get_or_fetch_earth_engine_context(
        region=region,
        station=station,
        weather_snapshot=weather_snapshot,
        redis_manager=redis_manager,
    )

    assert payload is not None
    assert payload["cache_hit"] is False
    assert payload["source"] == "earth-engine-fallback"
    assert payload["fallback_used"] is True
    assert "ee backend unavailable" in payload["fallback_reason"]
    assert payload["proxies"]["intrusion_pressure_score"] == 1.0
    assert redis_manager.last_set is not None
