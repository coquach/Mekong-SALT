"""API tests for read-only risk views."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models.enums import RiskLevel
from app.models.weather import WeatherSnapshot
from app.schemas.risk import RiskEvaluationFilters
from app.services.risk_service import evaluate_current_risk


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
async def test_get_latest_risk_returns_worker_persisted_assessment(
    client,
    db_session,
    seeded_sensor_data,
    monkeypatch,
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

    await evaluate_current_risk(
        db_session,
        filters=RiskEvaluationFilters(station_code=seeded_sensor_data["station_a"].code),
        redis_manager=None,
        trigger_source="test.risk.evaluate",
    )

    response = await client.get(
        "/api/v1/risk/latest",
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
async def test_get_latest_risk_returns_404_before_monitoring_produces_assessment(
    client,
    seeded_sensor_data,
):
    response = await client.get(
        "/api/v1/risk/latest",
        params={"station_code": seeded_sensor_data["station_a"].code},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "risk_assessment_not_found"
