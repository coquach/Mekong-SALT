"""External weather and tide context integration."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import asyncio
import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.redis import RedisManager
from app.models.region import Region
from app.models.sensor import SensorStation
from app.models.weather import WeatherSnapshot
from app.repositories.weather import WeatherSnapshotRepository

logger = logging.getLogger(__name__)


async def get_or_fetch_weather_snapshot(
    session: AsyncSession,
    *,
    region: Region,
    station: SensorStation,
    redis_manager: RedisManager | None,
) -> WeatherSnapshot | None:
    """Get a recent normalized weather/tide snapshot or fetch one externally."""
    settings = get_settings()
    weather_repo = WeatherSnapshotRepository(session)

    fresh_snapshot = await weather_repo.get_recent_for_region(
        region.id,
        freshness_minutes=settings.weather_snapshot_freshness_minutes,
    )
    if fresh_snapshot is not None:
        return fresh_snapshot

    payload = await _get_cached_or_fetch_context(
        latitude=station.latitude,
        longitude=station.longitude,
        redis_manager=redis_manager,
    )
    if payload is None:
        return None

    observed_at = datetime.fromisoformat(payload["observed_at"].replace("Z", "+00:00"))
    existing_snapshot = await weather_repo.get_by_region_and_observed_at(
        region.id,
        observed_at,
    )
    if existing_snapshot is not None:
        return existing_snapshot

    snapshot = WeatherSnapshot(
        region_id=region.id,
        observed_at=observed_at,
        wind_speed_mps=_to_decimal(payload.get("wind_speed_mps")),
        wind_direction_deg=payload.get("wind_direction_deg"),
        tide_level_m=_to_decimal(payload.get("tide_level_m")),
        rainfall_mm=_to_decimal(payload.get("rainfall_mm")),
        condition_summary=payload.get("condition_summary"),
        source_payload={
            "provider": "open-meteo",
            "cache_hit": payload.get("cache_hit", False),
            "weather": payload.get("weather"),
            "marine": payload.get("marine"),
        },
    )
    await weather_repo.add(snapshot)
    await session.commit()
    logger.info("Persisted normalized weather snapshot for region %s", region.code)
    return snapshot


async def _get_cached_or_fetch_context(
    *,
    latitude: Decimal,
    longitude: Decimal,
    redis_manager: RedisManager | None,
) -> dict[str, Any] | None:
    settings = get_settings()
    cache_key = (
        "external-context:"
        f"{_coordinate_key(latitude)}:"
        f"{_coordinate_key(longitude)}"
    )

    if redis_manager is not None:
        cached_payload = await redis_manager.get_json(cache_key)
        if cached_payload is not None:
            cached_payload["cache_hit"] = True
            return cached_payload

    payload = await _fetch_context(latitude=float(latitude), longitude=float(longitude))
    if payload is None:
        return None

    if redis_manager is not None:
        await redis_manager.set_json(
            cache_key,
            payload,
            ttl_seconds=settings.external_context_cache_ttl_seconds,
        )
    payload["cache_hit"] = False
    return payload


async def _fetch_context(*, latitude: float, longitude: float) -> dict[str, Any] | None:
    settings = get_settings()
    timeout = httpx.Timeout(10.0, connect=5.0)

    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wind_speed_10m,wind_direction_10m,precipitation",
        "timezone": "UTC",
    }
    marine_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "sea_level_height_msl",
        "timezone": "UTC",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            weather_response, marine_response = await asyncio.gather(
                client.get(settings.open_meteo_weather_base_url, params=weather_params),
                client.get(settings.open_meteo_marine_base_url, params=marine_params),
            )
            weather_response.raise_for_status()
            marine_response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("External weather/tide fetch failed")
            raise AppException(
                status_code=503,
                code="external_context_unavailable",
                message="Weather and tide context is temporarily unavailable.",
            ) from exc

    weather_payload = weather_response.json()
    marine_payload = marine_response.json()
    weather_current = weather_payload.get("current", {})
    marine_current = marine_payload.get("current", {})

    observed_at = weather_current.get("time") or marine_current.get("time")
    if observed_at is None:
        return None

    wind_speed_kmh = weather_current.get("wind_speed_10m")
    wind_speed_mps = None
    if wind_speed_kmh is not None:
        wind_speed_mps = round(float(wind_speed_kmh) / 3.6, 2)

    return {
        "observed_at": observed_at if observed_at.endswith("Z") else f"{observed_at}Z",
        "wind_speed_mps": wind_speed_mps,
        "wind_direction_deg": weather_current.get("wind_direction_10m"),
        "rainfall_mm": weather_current.get("precipitation"),
        "tide_level_m": marine_current.get("sea_level_height_msl"),
        "condition_summary": _build_summary(weather_current, marine_current),
        "weather": weather_current,
        "marine": marine_current,
    }


def _coordinate_key(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _build_summary(weather_current: dict[str, Any], marine_current: dict[str, Any]) -> str:
    wind = weather_current.get("wind_speed_10m")
    tide = marine_current.get("sea_level_height_msl")
    return f"wind={wind} km/h, tide={tide} m"

