from datetime import UTC, datetime, timedelta
from decimal import Decimal
import pytest

from app.models.memory_case import MemoryCase


@pytest.mark.asyncio
async def test_memory_cases_list_endpoint(client, db_session, seeded_sensor_data):
    region = seeded_sensor_data["region"]
    station = seeded_sensor_data["station_a"]
    now = datetime.now(UTC)

    older_case = MemoryCase(
        region_id=region.id,
        station_id=station.id,
        risk_assessment_id=None,
        incident_id=None,
        action_plan_id=None,
        action_execution_id=None,
        decision_log_id=None,
        objective="Older warning case",
        severity="warning",
        outcome_class="success",
        outcome_status_legacy="improved",
        summary="Older memory case summary.",
        context_payload={"source": "test"},
        action_payload={"steps": ["notify"]},
        outcome_payload={"result": "stable"},
        keywords=["warning"],
        occurred_at=now - timedelta(hours=2),
    )
    newer_case = MemoryCase(
        region_id=region.id,
        station_id=station.id,
        risk_assessment_id=None,
        incident_id=None,
        action_plan_id=None,
        action_execution_id=None,
        decision_log_id=None,
        objective="Newer critical case",
        severity="critical",
        outcome_class="success",
        outcome_status_legacy="improved",
        summary="Newer memory case summary.",
        context_payload={"source": "test"},
        action_payload={"steps": ["close_gate"]},
        outcome_payload={"result": "stable"},
        keywords=["critical"],
        occurred_at=now - timedelta(minutes=20),
    )
    db_session.add_all([older_case, newer_case])
    await db_session.commit()

    response = await client.get("/api/v1/memory-cases", params={"limit": 10})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["count"] == 2
    assert payload["items"][0]["id"] == str(newer_case.id)
    assert payload["items"][0]["summary"] == "Newer memory case summary."
    assert payload["items"][1]["id"] == str(older_case.id)
