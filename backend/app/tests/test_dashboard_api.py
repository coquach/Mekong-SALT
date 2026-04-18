"""Dashboard API integration tests."""

from datetime import UTC, datetime

import pytest

from app.models.enums import NotificationChannel
from app.models.agent_run import AgentRun, ObservationSnapshot
from app.schemas.notification import NotificationCreate
from app.services.notification_service import create_notification


@pytest.mark.asyncio
async def test_dashboard_earth_engine_latest_returns_context(
    client,
    db_session,
    seeded_sensor_data,
):
    station = seeded_sensor_data["station_a"]
    region = seeded_sensor_data["region"]
    now = datetime.now(UTC)

    run = AgentRun(
        run_type="plan_generation",
        trigger_source="monitoring.worker.auto_plan",
        status="succeeded",
        payload={"goal_name": "test-goal"},
        trace={},
        started_at=now,
        finished_at=now,
        region_id=region.id,
        station_id=station.id,
    )
    db_session.add(run)
    await db_session.flush()

    snapshot = ObservationSnapshot(
        agent_run_id=run.id,
        captured_at=now,
        source="plan.pre_decision",
        region_id=region.id,
        station_id=station.id,
        reading_id=seeded_sensor_data["reading_a_latest"].id,
        weather_snapshot_id=None,
        payload={
            "earth_engine_context": {
                "source": "earth-engine-fallback",
                "fallback_used": True,
                "dataset": "COPERNICUS/S2_SR_HARMONIZED",
                "summary": "Fallback hydro-context used.",
            }
        },
    )
    db_session.add(snapshot)
    await db_session.commit()

    response = await client.get(
        "/api/v1/dashboard/earth-engine/latest",
        params={"station_code": station.code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["run_id"] == str(run.id)
    assert body["data"]["station_code"] == station.code
    assert body["data"]["region_code"] == region.code
    assert body["data"]["source"] == "earth-engine-fallback"
    assert body["data"]["earth_engine_context"]["fallback_used"] is True


@pytest.mark.asyncio
async def test_dashboard_earth_engine_latest_returns_empty_payload_without_snapshot(
    client,
    seeded_sensor_data,
):
    station = seeded_sensor_data["station_a"]

    response = await client.get(
        "/api/v1/dashboard/earth-engine/latest",
        params={"station_code": station.code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["run_id"] is None
    assert body["data"]["earth_engine_context"] is None


@pytest.mark.asyncio
async def test_dashboard_summary_counts_email_delivery_records(
    client,
    db_session,
):
    baseline_response = await client.get("/api/v1/dashboard/summary")
    assert baseline_response.status_code == 200
    baseline_body = baseline_response.json()
    assert baseline_body["success"] is True
    baseline_count = baseline_body["data"]["active_notifications"]

    await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.DASHBOARD,
            recipient="dashboard",
            subject="Thông báo nội bộ",
            message="Thông báo hiển thị trên dashboard.",
            payload={"event": "incident_created"},
        ),
    )
    await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.EMAIL_MOCK,
            recipient="ops@example.test",
            subject="Thông báo email",
            message="Thông báo gửi qua email.",
            payload={"event": "incident_created"},
        ),
    )
    await db_session.commit()

    response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["active_notifications"] == baseline_count + 2
