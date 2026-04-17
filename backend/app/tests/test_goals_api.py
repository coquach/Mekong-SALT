"""Tests for Monitoring Goals CRUD."""

import pytest


@pytest.mark.asyncio
async def test_monitoring_goal_create_update_list_and_delete(
    client,
    seeded_sensor_data,
):
    create_payload = {
        "name": "TienGiang-Salinity-Goal-01",
        "description": "Keep irrigation salinity below warning",
        "region_id": str(seeded_sensor_data["region"].id),
        "station_id": str(seeded_sensor_data["station_a"].id),
        "objective": "Keep salinity below 2.5 dS/m",
        "provider": "mock",
        "thresholds": {
            "warning_threshold_dsm": "2.50",
            "critical_threshold_dsm": "4.00",
        },
        "evaluation_interval_minutes": 15,
        "is_active": True,
    }
    create_response = await client.post("/api/v1/goals", json=create_payload)

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    goal_id = created["id"]
    assert created["thresholds"]["warning_threshold_dsm"] == "2.50"
    assert created["evaluation_interval_minutes"] == 15
    assert created["is_active"] is True

    update_payload = {
        "objective": "Keep salinity below 2.3 dS/m",
        "thresholds": {
            "warning_threshold_dsm": "2.30",
            "critical_threshold_dsm": "3.80",
        },
        "evaluation_interval_minutes": 20,
    }
    update_response = await client.patch(f"/api/v1/goals/{goal_id}", json=update_payload)

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["objective"] == "Keep salinity below 2.3 dS/m"
    assert updated["thresholds"]["warning_threshold_dsm"] == "2.30"
    assert updated["thresholds"]["critical_threshold_dsm"] == "3.80"
    assert updated["evaluation_interval_minutes"] == 20

    list_response = await client.get("/api/v1/goals")
    assert list_response.status_code == 200
    listed = list_response.json()["data"]
    assert listed["count"] >= 1
    assert any(item["id"] == goal_id for item in listed["items"])

    run_once_response = await client.post(f"/api/v1/goals/{goal_id}/run-once", json={})
    assert run_once_response.status_code == 404

    delete_response = await client.delete(f"/api/v1/goals/{goal_id}")
    assert delete_response.status_code == 200

    get_response = await client.get(f"/api/v1/goals/{goal_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_monitoring_goal_rejects_invalid_thresholds(client, seeded_sensor_data):
    invalid_payload = {
        "name": "Invalid-Goal-Thresholds",
        "region_id": str(seeded_sensor_data["region"].id),
        "station_id": str(seeded_sensor_data["station_a"].id),
        "objective": "Protect irrigation",
        "thresholds": {
            "warning_threshold_dsm": "3.50",
            "critical_threshold_dsm": "3.00",
        },
        "evaluation_interval_minutes": 10,
        "is_active": True,
    }

    response = await client.post("/api/v1/goals", json=invalid_payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
