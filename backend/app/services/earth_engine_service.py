"""Earth Engine spatial context adapter with resilient fallback behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging
from typing import Any

from app.core.config import get_settings
from app.db.redis import RedisManager
from app.models.region import Region
from app.models.sensor import SensorStation
from app.models.weather import WeatherSnapshot

logger = logging.getLogger(__name__)


async def get_or_fetch_earth_engine_context(
    *,
    region: Region,
    station: SensorStation,
    weather_snapshot: WeatherSnapshot | None,
    redis_manager: RedisManager | None,
) -> dict[str, Any] | None:
    """Return Earth Engine context when enabled, with cache and graceful fallback."""
    settings = get_settings()
    if not settings.earth_engine_enabled:
        return None

    now = datetime.now(UTC).replace(microsecond=0)
    cache_key = (
        "earth-engine-context:"
        f"{region.id}:"
        f"{station.id}:"
        f"{_round_coord(station.latitude)}:"
        f"{_round_coord(station.longitude)}"
    )
    if redis_manager is not None:
        cached_payload = await redis_manager.get_json(cache_key)
        if cached_payload is not None:
            cached_payload["cache_hit"] = True
            return cached_payload

    payload = await _fetch_with_fallback(
        region=region,
        station=station,
        weather_snapshot=weather_snapshot,
        observed_at=now,
    )
    payload["cache_hit"] = False

    if redis_manager is not None:
        await redis_manager.set_json(
            cache_key,
            payload,
            ttl_seconds=settings.external_context_cache_ttl_seconds,
        )

    return payload


async def _fetch_with_fallback(
    *,
    region: Region,
    station: SensorStation,
    weather_snapshot: WeatherSnapshot | None,
    observed_at: datetime,
) -> dict[str, Any]:
    """Try Earth Engine and fall back to deterministic context if unavailable."""
    settings = get_settings()
    try:
        ee_context = await _query_earth_engine(
            latitude=float(station.latitude),
            longitude=float(station.longitude),
            buffer_m=settings.earth_engine_region_buffer_m,
            dataset=settings.earth_engine_default_dataset,
            project_id=settings.earth_engine_project_id,
            service_account_email=settings.earth_engine_service_account_email,
            service_account_key_path=settings.earth_engine_service_account_key_path,
            observed_at=observed_at,
        )
        ee_context.update(
            {
                "region_code": region.code,
                "station_code": station.code,
                "source": "earth-engine",
                "fallback_used": False,
            }
        )
        return ee_context
    except Exception as exc:
        logger.warning("Earth Engine context fetch failed; using fallback", extra={"reason": str(exc)})
        return _fallback_context(
            region=region,
            station=station,
            weather_snapshot=weather_snapshot,
            observed_at=observed_at,
            reason=str(exc),
        )


async def _query_earth_engine(
    *,
    latitude: float,
    longitude: float,
    buffer_m: int,
    dataset: str,
    project_id: str | None,
    service_account_email: str | None,
    service_account_key_path: str | None,
    observed_at: datetime,
) -> dict[str, Any]:
    """Query a compact Earth Engine summary around station location.

    This adapter intentionally keeps output compact and optional. If authentication
    or dataset access is unavailable, caller will use fallback context.
    """
    try:
        import ee  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("earthengine-api is not installed.") from exc

    if service_account_email and service_account_key_path:
        credentials = ee.ServiceAccountCredentials(service_account_email, service_account_key_path)
        ee.Initialize(credentials=credentials, project=project_id)
    else:
        ee.Initialize(project=project_id)

    point = ee.Geometry.Point([longitude, latitude])
    roi = point.buffer(max(500, int(buffer_m)))
    start = (observed_at - timedelta(days=30)).date().isoformat()
    end = observed_at.date().isoformat()

    collection = (
        ee.ImageCollection(dataset)
        .filterBounds(roi)
        .filterDate(start, end)
        .sort("system:time_start", False)
    )
    image = collection.first()
    if image is None:
        raise RuntimeError("No Earth Engine imagery available for region/date window.")

    ndwi = image.normalizedDifference(["B3", "B8"]).rename("ndwi")
    ndmi = image.normalizedDifference(["B8", "B11"]).rename("ndmi")
    combined = ndwi.addBands(ndmi)
    stats = combined.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=30,
        maxPixels=1_000_000,
    ).getInfo() or {}

    ndwi_mean = _to_float(stats.get("ndwi"))
    ndmi_mean = _to_float(stats.get("ndmi"))

    return {
        "generated_at": observed_at.isoformat(),
        "dataset": dataset,
        "window_days": 30,
        "roi_buffer_m": max(500, int(buffer_m)),
        "proxies": {
            "surface_water_proxy_ndwi": ndwi_mean,
            "soil_water_proxy_ndmi": ndmi_mean,
        },
        "summary": _build_summary_from_proxies(ndwi_mean=ndwi_mean, ndmi_mean=ndmi_mean),
    }


def _fallback_context(
    *,
    region: Region,
    station: SensorStation,
    weather_snapshot: WeatherSnapshot | None,
    observed_at: datetime,
    reason: str,
) -> dict[str, Any]:
    """Deterministic fallback context for continuity when Earth Engine fails."""
    wind = _to_float(weather_snapshot.wind_speed_mps) if weather_snapshot is not None else None
    tide = _to_float(weather_snapshot.tide_level_m) if weather_snapshot is not None else None
    pressure = _intrusion_pressure_score(wind_speed_mps=wind, tide_level_m=tide)

    return {
        "generated_at": observed_at.isoformat(),
        "dataset": get_settings().earth_engine_default_dataset,
        "window_days": 30,
        "roi_buffer_m": max(500, int(get_settings().earth_engine_region_buffer_m)),
        "region_code": region.code,
        "station_code": station.code,
        "source": "earth-engine-fallback",
        "fallback_used": True,
        "fallback_reason": reason,
        "proxies": {
            "surface_water_proxy_ndwi": None,
            "soil_water_proxy_ndmi": None,
            "intrusion_pressure_score": pressure,
        },
        "summary": "Fallback hydro-context used (weather/tide derived) because Earth Engine query was unavailable.",
    }


def _build_summary_from_proxies(*, ndwi_mean: float | None, ndmi_mean: float | None) -> str:
    if ndwi_mean is None and ndmi_mean is None:
        return "Earth Engine context available, but proxy statistics were empty."
    return (
        "Earth Engine proxy summary: "
        f"surface_water_proxy_ndwi={ndwi_mean}, "
        f"soil_water_proxy_ndmi={ndmi_mean}."
    )


def _intrusion_pressure_score(*, wind_speed_mps: float | None, tide_level_m: float | None) -> float | None:
    if wind_speed_mps is None and tide_level_m is None:
        return None
    wind_factor = min(max((wind_speed_mps or 0.0) / 8.0, 0.0), 1.0)
    tide_factor = min(max((tide_level_m or 0.0) / 2.0, 0.0), 1.0)
    return round((0.55 * tide_factor) + (0.45 * wind_factor), 3)


def _round_coord(value: Decimal) -> str:
    return f"{float(value):.3f}"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None
