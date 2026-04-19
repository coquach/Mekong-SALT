from decimal import Decimal
from uuid import uuid4

import pytest
from app.models.gate import Gate
from app.models.region import Region
from app.models.sensor import SensorStation
from app.models.enums import GateStatus, StationStatus


@pytest.mark.asyncio
async def test_gate_crud_endpoints(client, db_session):
    region = Region(
        code=f"TEST-GATE-REGION-{uuid4().hex[:8]}",
        name="Test Gate Region",
        province="Tien Giang",
        crop_profile={"dominant_crops": ["rice"]},
    )
    station = SensorStation(
        region=region,
        code=f"TEST-GATE-STATION-{uuid4().hex[:6]}",
        name="Linked Station",
        station_type="salinity-water-level",
        status=StationStatus.ACTIVE,
        latitude=Decimal("10.100001"),
        longitude=Decimal("106.100001"),
    )
    gate = Gate(
        region=region,
        station=station,
        code=f"TEST-GATE-{uuid4().hex[:6]}",
        name="Test Gate",
        gate_type="sluice",
        status=GateStatus.CLOSED,
        latitude=Decimal("10.200001"),
        longitude=Decimal("106.200001"),
        gate_metadata={"source": "test"},
    )
    db_session.add_all([region, station, gate])
    await db_session.commit()

    response = await client.get("/api/v1/gates")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert any(item["code"] == gate.code for item in payload["items"])
    gate_item = next(item for item in payload["items"] if item["code"] == gate.code)
    assert gate_item["station"]["code"] == station.code

    detail = await client.get(f"/api/v1/gates/{gate.id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["code"] == gate.code

    update = await client.patch(
        f"/api/v1/gates/{gate.id}",
        json={"status": "open", "name": "Updated Gate"},
    )
    assert update.status_code == 200
    updated = update.json()["data"]
    assert updated["status"] == "open"
    assert updated["name"] == "Updated Gate"
    assert updated["last_operated_at"] is not None
    assert updated["gate_metadata"]["last_command"]["action_type"] == "open_gate"
    assert updated["gate_metadata"]["last_command"]["status_before"] == "closed"
    assert updated["gate_metadata"]["last_command"]["status_after"] == "open"
