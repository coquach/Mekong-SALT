"""Tests for risk service orchestration helpers."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.models.sensor import SensorReading
from app.schemas.risk import RiskEvaluationFilters
from app.services.risk_service import evaluate_current_risk, resolve_target_reading


async def _persist_stub_weather_snapshot(
    session,
    *,
    region_id,
    wind_speed_mps: Decimal = Decimal("5.20"),
    tide_level_m: Decimal = Decimal("1.60"),
) -> object:
    from app.models.weather import WeatherSnapshot

    snapshot = WeatherSnapshot(
        region_id=region_id,
        observed_at=datetime.now(UTC),
        wind_speed_mps=wind_speed_mps,
        wind_direction_deg=120,
        tide_level_m=tide_level_m,
        rainfall_mm=Decimal("0.00"),
        condition_summary="stubbed weather context",
        source_payload={"provider": "test"},
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


async def test_resolve_target_reading_prefers_newest_reading_for_region_scope(
    db_session,
    seeded_sensor_data,
):
    reading = await resolve_target_reading(
        db_session,
        RiskEvaluationFilters(region_id=seeded_sensor_data["region"].id),
    )

    assert reading.station.code == seeded_sensor_data["station_b"].code
    assert reading.id == seeded_sensor_data["reading_b_latest"].id


@pytest.mark.asyncio
async def test_evaluate_current_risk_persists_confidence_metadata(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(session, region_id=region.id)

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    reading = SensorReading(
        station_id=seeded_sensor_data["station_a"].id,
        recorded_at=datetime.now(UTC) - timedelta(minutes=95),
        salinity_dsm=Decimal("4.20"),
        water_level_m=Decimal("1.55"),
        temperature_c=Decimal("29.20"),
        battery_level_pct=Decimal("14.00"),
        source="test",
    )
    db_session.add(reading)
    await db_session.commit()
    await db_session.refresh(reading)

    bundle = await evaluate_current_risk(
        db_session,
        filters=RiskEvaluationFilters(station_id=seeded_sensor_data["station_a"].id),
        redis_manager=None,
        target_reading=reading,
        trigger_source="test.risk.evaluate",
    )

    assert bundle.assessment.rationale["confidence"]["level"] == "low"
    assert bundle.assessment.rationale["battery_level_pct"] == "14.00"
    assert bundle.assessment.rationale["reading_age_minutes"] is not None


@pytest.mark.asyncio
async def test_evaluate_current_risk_uses_trend_window_to_avoid_noisy_escalation(
    db_session,
    seeded_sensor_data,
    monkeypatch,
):
    async def fake_weather_snapshot(session, *, region, station, redis_manager):
        return await _persist_stub_weather_snapshot(
            session,
            region_id=region.id,
            wind_speed_mps=Decimal("2.10"),
            tide_level_m=Decimal("0.70"),
        )

    monkeypatch.setattr(
        "app.services.risk_service.get_or_fetch_weather_snapshot",
        fake_weather_snapshot,
    )

    station = seeded_sensor_data["station_b"]
    older_reading = SensorReading(
        station_id=station.id,
        recorded_at=datetime.now(UTC) - timedelta(minutes=60),
        salinity_dsm=Decimal("3.00"),
        water_level_m=Decimal("0.98"),
        temperature_c=Decimal("28.60"),
        battery_level_pct=Decimal("81.00"),
        source="test",
    )
    noisy_mid_reading = SensorReading(
        station_id=station.id,
        recorded_at=datetime.now(UTC) - timedelta(minutes=30),
        salinity_dsm=Decimal("2.60"),
        water_level_m=Decimal("1.02"),
        temperature_c=Decimal("28.90"),
        battery_level_pct=Decimal("80.00"),
        source="test",
    )
    current_reading = SensorReading(
        station_id=station.id,
        recorded_at=datetime.now(UTC) - timedelta(minutes=5),
        salinity_dsm=Decimal("3.00"),
        water_level_m=Decimal("1.08"),
        temperature_c=Decimal("29.10"),
        battery_level_pct=Decimal("79.00"),
        source="test",
    )
    db_session.add_all([older_reading, noisy_mid_reading, current_reading])
    await db_session.commit()
    await db_session.refresh(current_reading)

    bundle = await evaluate_current_risk(
        db_session,
        filters=RiskEvaluationFilters(station_id=station.id),
        redis_manager=None,
        target_reading=current_reading,
        trigger_source="test.risk.trend_window",
    )

    assert bundle.assessment.risk_level is not None
    assert bundle.assessment.risk_level.value == "danger"
    assert bundle.assessment.trend_direction.value == "stable"
    assert any(
        "trend_window=" in item
        for item in bundle.assessment.rationale["trend_window_salinity_dsm"]
    )
