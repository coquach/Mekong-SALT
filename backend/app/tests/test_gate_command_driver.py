from decimal import Decimal
from uuid import uuid4

import pytest

from app.agents.providers import MockProvider
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, ActionType, GateStatus, StationStatus
from app.models.gate import Gate
from app.models.region import Region
from app.models.sensor import SensorStation
from app.schemas.agent import PlanStep
from app.services.gate_command_driver import SimulatedGateCommandDriver


@pytest.mark.asyncio
async def test_mock_planner_includes_gate_target_code():
    provider = MockProvider()
    plan = await provider.generate_plan(
        objective="Giảm rủi ro xâm nhập mặn",
        context={
            "assessment": {
                "risk_level": "critical",
                "summary": "Rủi ro cần đóng cống",
            },
            "recommended_gate_target_code": "GATE-HOA-DINH",
            "gate_targets": [
                {
                    "code": "GATE-HOA-DINH",
                    "name": "Cống Hòa Định",
                }
            ],
        },
    )

    assert plan.steps[1].action_type == ActionType.CLOSE_GATE
    assert plan.steps[1].target_gate_code == "GATE-HOA-DINH"


@pytest.mark.asyncio
async def test_mock_planner_prefers_open_gate_when_salinity_is_falling():
    provider = MockProvider()
    plan = await provider.generate_plan(
        objective="Mở cống khi độ mặn giảm",
        context={
            "assessment": {
                "risk_level": "danger",
                "trend_direction": "falling",
                "summary": "Salinity is decreasing but still in a planable band.",
            },
            "recommended_gate_target_code": "GATE-RECOVERY-01",
        },
    )

    assert plan.steps[1].action_type == ActionType.OPEN_GATE
    assert plan.steps[1].target_gate_code == "GATE-RECOVERY-01"
    assert plan.steps[2].action_type == ActionType.WAIT_SAFE_WINDOW


@pytest.mark.asyncio
async def test_simulated_gate_driver_updates_gate_status(db_session):
    region = Region(
        code=f"TEST-GATE-DRIVER-{uuid4().hex[:8]}",
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

    plan = ActionPlan(
        region_id=region.id,
        risk_assessment_id=uuid4(),
        objective="Test gate closure",
        summary="Test gate closure summary",
        plan_steps=[],
        status=ActionPlanStatus.APPROVED,
    )
    step = PlanStep(
        step_index=1,
        action_type=ActionType.OPEN_GATE,
        priority=1,
        title="Mở cống thử nghiệm",
        instructions="Mở cống được chỉ định.",
        rationale="Kiểm tra driver mô phỏng.",
        target_gate_code=gate.code,
        simulated=True,
    )

    driver = SimulatedGateCommandDriver()
    result = await driver.execute(db_session, plan=plan, step=step, actor_name="operator")

    await db_session.refresh(gate)

    assert result.gate.code == gate.code
    assert result.before_status == GateStatus.CLOSED
    assert result.after_status == GateStatus.OPEN
    assert gate.status == GateStatus.OPEN
    assert gate.last_operated_at is not None
    assert result.payload["gate"]["code"] == gate.code
    assert result.payload["target_resolution"] == "step.target_gate_code"
