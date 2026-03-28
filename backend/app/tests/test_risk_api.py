"""API tests for risk evaluation and alert creation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models.enums import RiskLevel
from app.models.weather import WeatherSnapshot


async def _persist_stub_weather_snapshot(
    session,
    *,
    region_id,
    wind_speed_mps: str,
    tide_level_m: str,
) -> WeatherSnapshot:
    snapshot = WeatherSnapshot(
        region_id=region_id,
        observed_at=datetime.now(UTC),
        wind_speed_mps=Decimal(wind_speed_mps),
        wind_direction_deg=135,
        tide_level_m=Decimal(tide_level_m),
        rainfall_mm=Decimal("0.20"),
        condition_summary="stubbed weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


@pytest.mark.asyncio
async def test_get_current_risk_persists_assessment_and_returns_weather_context(
    client, seeded_sensor_data, monkeypatch
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps="5.50",
            tide_level_m="1.70",
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    response = await client.get(
        "/api/v1/risk/current",
        params={"station_code": seeded_sensor_data["station_a"].code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["assessment"]["risk_level"] == RiskLevel.CRITICAL.value
    assert body["data"]["assessment"]["trend_direction"] == "rising"
    assert body["data"]["reading"]["station"]["code"] == seeded_sensor_data["station_a"].code
    assert body["data"]["weather_snapshot"]["tide_level_m"] == "1.70"


@pytest.mark.asyncio
async def test_alert_evaluate_creates_alert_for_high_risk_station(
    client, seeded_sensor_data, monkeypatch
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps="5.50",
            tide_level_m="1.70",
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    response = await client.post(
        "/api/v1/alerts/evaluate",
        json={"station_code": seeded_sensor_data["station_a"].code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["assessment"]["risk_level"] == RiskLevel.CRITICAL.value
    assert body["data"]["alert_created"] is True
    assert body["data"]["alert"]["severity"] == RiskLevel.CRITICAL.value


@pytest.mark.asyncio
async def test_alert_evaluate_skips_alert_for_warning_level_station(
    client, seeded_sensor_data, monkeypatch
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps="2.00",
            tide_level_m="0.80",
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    response = await client.post(
        "/api/v1/alerts/evaluate",
        json={"station_code": seeded_sensor_data["station_b"].code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["assessment"]["risk_level"] == RiskLevel.WARNING.value
    assert body["data"]["alert_created"] is False
    assert body["data"]["alert"] is None
