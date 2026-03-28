"""Integration tests for sensor ingestion and query APIs."""

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_ingest_sensor_reading_persists_and_returns_envelope(
    client, seeded_sensor_data
):
    station = seeded_sensor_data["station_a"]
    recorded_at = datetime.now(UTC).replace(microsecond=0)

    response = await client.post(
        "/api/v1/sensors/ingest",
        json={
            "station_code": station.code,
            "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
            "salinity_dsm": "4.25",
            "water_level_m": "1.55",
            "temperature_c": "30.10",
            "battery_level_pct": "79.00",
            "context_payload": {"source": "api-test"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["station"]["code"] == station.code
    assert body["data"]["salinity_dsm"] == "4.25"
    assert body["data"]["context_payload"]["source"] == "api-test"


@pytest.mark.asyncio
async def test_latest_returns_one_latest_reading_per_station_for_region(
    client, seeded_sensor_data
):
    region = seeded_sensor_data["region"]

    response = await client.get(
        "/api/v1/sensors/latest",
        params={"region_code": region.code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["count"] == 2

    items = body["data"]["items"]
    station_codes = {item["station"]["code"] for item in items}
    assert station_codes == {
        seeded_sensor_data["station_a"].code,
        seeded_sensor_data["station_b"].code,
    }

    station_a_item = next(
        item
        for item in items
        if item["station"]["code"] == seeded_sensor_data["station_a"].code
    )
    assert station_a_item["salinity_dsm"] == str(
        seeded_sensor_data["reading_a_latest"].salinity_dsm
    )


@pytest.mark.asyncio
async def test_history_filters_by_station_and_time_range(client, seeded_sensor_data):
    station = seeded_sensor_data["station_a"]
    start_at = seeded_sensor_data["now"] - timedelta(hours=3)
    end_at = seeded_sensor_data["now"] - timedelta(minutes=30)

    response = await client.get(
        "/api/v1/sensors/history",
        params={
            "station_code": station.code,
            "start_at": start_at.isoformat().replace("+00:00", "Z"),
            "end_at": end_at.isoformat().replace("+00:00", "Z"),
            "limit": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["count"] == 1
    item = body["data"]["items"][0]
    assert item["station"]["code"] == station.code
    assert item["salinity_dsm"] == str(seeded_sensor_data["reading_a_old"].salinity_dsm)


@pytest.mark.asyncio
async def test_history_rejects_invalid_time_range(client, seeded_sensor_data):
    station = seeded_sensor_data["station_a"]
    start_at = datetime.now(UTC)
    end_at = start_at - timedelta(hours=1)

    response = await client.get(
        "/api/v1/sensors/history",
        params={
            "station_code": station.code,
            "start_at": start_at.isoformat().replace("+00:00", "Z"),
            "end_at": end_at.isoformat().replace("+00:00", "Z"),
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "invalid_time_range"
