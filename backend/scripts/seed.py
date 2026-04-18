"""Seed the database with minimal realistic sample data."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from sqlalchemy import delete, or_, select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import AsyncSessionFactory, close_database_engine
from app.models import (
    ActionExecution,
    Approval,
    AuditLog,
    ActionPlan,
    AlertEvent,
    AgentRun,
    DecisionLog,
    EmbeddedChunk,
    Incident,
    KnowledgeDocument,
    MemoryCase,
    Notification,
    Region,
    RiskAssessment,
    SensorReading,
    SensorStation,
    ObservationSnapshot,
    WeatherSnapshot,
    Gate,
)
from app.models.enums import (
    ApprovalDecision,
    AlertStatus,
    AuditEventType,
    ActionPlanStatus,
    ActionType,
    DecisionActorType,
    ExecutionStatus,
    IncidentStatus,
    NotificationChannel,
    NotificationStatus,
    RiskLevel,
    StationStatus,
    TrendDirection,
    GateStatus,
)
from app.repositories.region import RegionRepository
from app.repositories.gate import GateRepository
from app.repositories.sensor import SensorStationRepository

logger = logging.getLogger(__name__)


async def _reset_demo_region_data(
    session,
    *,
    region_repo: RegionRepository,
) -> bool:
    """Delete existing demo rows so each seed starts from a clean slate."""
    existing_region = await region_repo.get_by_code("TIEN-GIANG-GO-CONG")
    if existing_region is None:
        return False

    region_id = existing_region.id
    incident_ids = select(Incident.id).where(Incident.region_id == region_id)
    execution_ids = select(ActionExecution.id).where(ActionExecution.region_id == region_id)

    await session.execute(
        delete(Notification).where(
            or_(
                Notification.incident_id.in_(incident_ids),
                Notification.execution_id.in_(execution_ids),
            )
        )
    )
    await session.execute(delete(DecisionLog).where(DecisionLog.region_id == region_id))
    await session.execute(delete(AuditLog).where(AuditLog.region_id == region_id))
    await session.execute(delete(MemoryCase).where(MemoryCase.region_id == region_id))
    await session.execute(delete(AgentRun).where(AgentRun.region_id == region_id))
    await session.execute(delete(ObservationSnapshot).where(ObservationSnapshot.region_id == region_id))
    await session.execute(
        delete(KnowledgeDocument).where(
            KnowledgeDocument.source_uri.like("mekong-salt://knowledge/%")
        )
    )
    await session.execute(delete(Region).where(Region.id == region_id))
    await session.flush()
    return True


def _build_station_metadata(
    *,
    display_name: str,
    operational_role: str,
    owner: str,
    operator: str,
    connectivity: str,
    coverage_radius_km: int,
    sensor_package: list[str],
    reference_water_body: str,
    sampling_interval_minutes: int,
    calibration_cycle_days: int,
    marker_icon: str,
    marker_color: str,
    marker_label: str,
    notes: str,
    map_anchor: dict[str, object] | None = None,
) -> dict[str, object]:
    metadata = {
        "display_name": display_name,
        "operational_role": operational_role,
        "owner": owner,
        "operator": operator,
        "connectivity": connectivity,
        "coverage_radius_km": coverage_radius_km,
        "sensor_package": sensor_package,
        "reference_water_body": reference_water_body,
        "sampling_interval_minutes": sampling_interval_minutes,
        "calibration_cycle_days": calibration_cycle_days,
        "marker": {
            "icon": marker_icon,
            "color": marker_color,
            "label": marker_label,
        },
        "notes": notes,
    }
    if map_anchor is not None:
        metadata["map_anchor"] = map_anchor
    return metadata


def _build_gate_metadata(
    *,
    display_name: str,
    operational_role: str,
    controller: str,
    control_channel: str,
    marker_label: str,
    notes: str,
    map_anchor: dict[str, object] | None = None,
) -> dict[str, object]:
    metadata = {
        "display_name": display_name,
        "operational_role": operational_role,
        "controller": controller,
        "control_channel": control_channel,
        "marker": {
            "icon": "lock",
            "color": "navy",
            "label": marker_label,
        },
        "notes": notes,
    }
    if map_anchor is not None:
        metadata["map_anchor"] = map_anchor
    return metadata


async def _upsert_region_profile(
    session,
    *,
    region_repo: RegionRepository,
) -> tuple[Region, bool]:
    existing_region = await region_repo.get_by_code("TIEN-GIANG-GO-CONG")
    region_payload = {
        "code": "TIEN-GIANG-GO-CONG",
        "name": "Vùng ven biển Gò Công",
        "province": "Tiền Giang",
        "description": (
            "Hành lang thủy lợi ven biển và nội đồng quanh Gò Công, "
            "dùng để theo dõi xâm nhập mặn, biến động mực nước và rủi ro lấy nước."
        ),
        "crop_profile": {
            "dominant_crops": ["rice", "dragon fruit"],
            "irrigation_priority": "high",
            "salinity_tolerance_dsm": 1.5,
            "monitoring_focus": ["salinity", "water level", "tide influence"],
        },
    }

    if existing_region is None:
        region = await region_repo.add(
            Region(
                code=region_payload["code"],
                name=region_payload["name"],
                province=region_payload["province"],
                description=region_payload["description"],
                crop_profile=region_payload["crop_profile"],
            )
        )
        return region, False

    existing_region.name = region_payload["name"]
    existing_region.province = region_payload["province"]
    existing_region.description = region_payload["description"]
    existing_region.crop_profile = region_payload["crop_profile"]
    await session.flush()
    return existing_region, True


async def _upsert_station_profile(
    session,
    *,
    station_repo: SensorStationRepository,
    region: Region,
    code: str,
    name: str,
    station_type: str,
    status: StationStatus,
    latitude: Decimal,
    longitude: Decimal,
    location_description: str,
    installed_at: datetime | None,
    station_metadata: dict[str, object] | None,
) -> SensorStation:
    station = await station_repo.get_by_code(code)
    if station is None:
        return await station_repo.add(
            SensorStation(
                region_id=region.id,
                code=code,
                name=name,
                station_type=station_type,
                status=status,
                latitude=latitude,
                longitude=longitude,
                location_description=location_description,
                installed_at=installed_at,
                station_metadata=station_metadata,
            )
        )

    station.region_id = region.id
    station.name = name
    station.station_type = station_type
    station.status = status
    station.latitude = latitude
    station.longitude = longitude
    station.location_description = location_description
    station.installed_at = installed_at
    station.station_metadata = station_metadata
    await session.flush()
    return station


async def _upsert_gate_profile(
    session,
    *,
    gate_repo: GateRepository,
    region: Region,
    code: str,
    name: str,
    gate_type: str,
    status: GateStatus,
    latitude: Decimal,
    longitude: Decimal,
    location_description: str,
    station_id=None,
    gate_metadata: dict[str, object] | None = None,
) -> Gate:
    gate = await gate_repo.get_by_code(code)
    if gate is None:
        return await gate_repo.add(
            Gate(
                region_id=region.id,
                station_id=station_id,
                code=code,
                name=name,
                gate_type=gate_type,
                status=status,
                latitude=latitude,
                longitude=longitude,
                location_description=location_description,
                gate_metadata=gate_metadata,
            )
        )

    gate.region_id = region.id
    gate.station_id = station_id
    gate.name = name
    gate.gate_type = gate_type
    gate.status = status
    gate.latitude = latitude
    gate.longitude = longitude
    gate.location_description = location_description
    gate.gate_metadata = gate_metadata
    await session.flush()
    return gate


async def run_seed() -> None:
    """Insert a connected demo dataset for local development."""
    settings = get_settings()
    configure_logging(settings.log_level)
    now = datetime.now(UTC)

    async with AsyncSessionFactory() as session:
        region_repo = RegionRepository(session)
        station_repo = SensorStationRepository(session)
        reset_done = await _reset_demo_region_data(session, region_repo=region_repo)
        if reset_done:
            logger.info("Đã reset dữ liệu demo cũ cho region TIEN-GIANG-GO-CONG")
        region, _ = await _upsert_region_profile(session, region_repo=region_repo)

        station_a = await _upsert_station_profile(
            session,
            station_repo=station_repo,
            region=region,
            code="GOCONG-01",
            name="Trạm lấy nước Gò Công Đông",
            station_type="salinity-water-level",
            status=StationStatus.ACTIVE,
            latitude=Decimal("10.323421"),
            longitude=Decimal("106.452189"),
            location_description=(
                "Cửa lấy nước chính ở rìa phía đông của hành lang thủy lợi Gò Công. "
                "Đây là điểm tham chiếu ven biển để đo salinity trước khi nước đi vào mạng kênh."
            ),
            installed_at=now - timedelta(days=180),
            station_metadata=_build_station_metadata(
                display_name="Trạm lấy nước Gò Công Đông",
                operational_role="primary_intake",
                owner="Sở NN&PTNT Tiền Giang",
                operator="Ban quản lý thủy nông Gò Công",
                connectivity="MQTT/4G gateway",
                coverage_radius_km=6,
                sensor_package=["salinity", "water_level", "tide_level", "battery"],
                reference_water_body="Kênh lấy nước ven biển Gò Công",
                sampling_interval_minutes=15,
                calibration_cycle_days=30,
                marker_icon="droplets",
                marker_color="teal",
                marker_label="Cửa lấy nước chính",
                notes=(
                    "Trạm đầu vào chính cho bài toán salinity monitoring và response planning. "
                    "Spot của trạm phải bám theo tọa độ latitude/longitude để hiển thị đúng trên map."
                ),
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "station_pin",
                    "display_strategy": "leaflet_marker",
                    "spot_role": "coastal_intake",
                },
            ),
        )
        station_b = await _upsert_station_profile(
            session,
            station_repo=station_repo,
            region=region,
            code="GOCONG-02",
            name="Trạm quan trắc nội đồng Gò Công",
            station_type="salinity-water-level",
            status=StationStatus.ACTIVE,
            latitude=Decimal("10.312114"),
            longitude=Decimal("106.435403"),
            location_description=(
                "Điểm so sánh nội đồng nằm trong mạng tưới tiêu. "
                "Trạm này dùng để đo độ mặn lan truyền sau cống lấy nước và kiểm tra hiệu ứng của quyết định vận hành."
            ),
            installed_at=now - timedelta(days=150),
            station_metadata=_build_station_metadata(
                display_name="Trạm quan trắc nội đồng Gò Công",
                operational_role="secondary_monitoring",
                owner="Sở NN&PTNT Tiền Giang",
                operator="Tổ quan trắc nội đồng",
                connectivity="MQTT/4G gateway",
                coverage_radius_km=4,
                sensor_package=["salinity", "water_level", "temperature", "battery"],
                reference_water_body="Kênh nội đồng Gò Công",
                sampling_interval_minutes=15,
                calibration_cycle_days=30,
                marker_icon="waves",
                marker_color="amber",
                marker_label="Trạm đối chứng nội đồng",
                notes=(
                    "Điểm tham chiếu nội đồng để so sánh gradient giữa cống lấy nước và mạng kênh bên trong."
                ),
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "station_pin",
                    "display_strategy": "leaflet_marker",
                    "spot_role": "inner_canal_reference",
                },
            ),
        )

        gate_repo = GateRepository(session)
        await _upsert_gate_profile(
            session,
            gate_repo=gate_repo,
            region=region,
            code="GATE-HOA-DINH",
            name="Cống Hòa Định",
            gate_type="sluice",
            status=GateStatus.CLOSED,
            latitude=Decimal("10.324850"),
            longitude=Decimal("106.449120"),
            location_description=(
                "Cống chính gần trạm lấy nước Gò Công Đông. Đây là điểm điều khiển đầu vào cho luồng response."
            ),
            station_id=station_a.id,
            gate_metadata=_build_gate_metadata(
                display_name="Cống Hòa Định",
                operational_role="primary_intake_gate",
                controller="Ban quản lý cống Gò Công",
                control_channel="MQTT/PLC gateway",
                marker_label="Cống chính",
                notes="Điểm đóng/mở chính để giảm xâm nhập mặn khi cần phản ứng nhanh.",
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "gate_pin",
                    "display_strategy": "leaflet_marker",
                    "linked_station_code": "GOCONG-01",
                },
            ),
        )
        await _upsert_gate_profile(
            session,
            gate_repo=gate_repo,
            region=region,
            code="GATE-XUAN-HOA",
            name="Cống Xuân Hòa",
            gate_type="sluice",
            status=GateStatus.CLOSED,
            latitude=Decimal("10.307680"),
            longitude=Decimal("106.440880"),
            location_description="Cống phụ nằm trên tuyến nội đồng, hỗ trợ kiểm soát gradient salinity.",
            station_id=station_b.id,
            gate_metadata=_build_gate_metadata(
                display_name="Cống Xuân Hòa",
                operational_role="secondary_gate",
                controller="Tổ vận hành địa phương",
                control_channel="MQTT/PLC gateway",
                marker_label="Cống phụ",
                notes="Hỗ trợ quan sát nội đồng và cân bằng luồng nước sau cống chính.",
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "gate_pin",
                    "display_strategy": "leaflet_marker",
                    "linked_station_code": "GOCONG-02",
                },
            ),
        )
        await _upsert_gate_profile(
            session,
            gate_repo=gate_repo,
            region=region,
            code="GATE-THOI-TAN",
            name="Cống Thới Tân",
            gate_type="sluice",
            status=GateStatus.OPEN,
            latitude=Decimal("10.338420"),
            longitude=Decimal("106.427890"),
            location_description="Cống vận hành ở phía tây bắc để làm mốc cố định trên bản đồ demo.",
            station_id=station_a.id,
            gate_metadata=_build_gate_metadata(
                display_name="Cống Thới Tân",
                operational_role="sluice_gate",
                controller="Ban vận hành khu vực",
                control_channel="Manual/SCADA",
                marker_label="Cống hiện mở",
                notes="Dùng làm điểm tham chiếu cố định cho lớp control map.",
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "gate_pin",
                    "display_strategy": "leaflet_marker",
                    "linked_station_code": "GOCONG-01",
                },
            ),
        )
        await _upsert_gate_profile(
            session,
            gate_repo=gate_repo,
            region=region,
            code="GATE-PHU-DONG",
            name="Cống Phú Đông",
            gate_type="sluice",
            status=GateStatus.CLOSED,
            latitude=Decimal("10.296120"),
            longitude=Decimal("106.437840"),
            location_description="Cống biên phía nam dùng để khóa ranh giới của hành lang demo.",
            station_id=station_b.id,
            gate_metadata=_build_gate_metadata(
                display_name="Cống Phú Đông",
                operational_role="boundary_gate",
                controller="Trạm giám sát khu vực",
                control_channel="SCADA",
                marker_label="Cống biên",
                notes="Điểm kiểm soát cuối của hành lang demo, dùng để nhìn biên vận hành.",
                map_anchor={
                    "source": "latitude_longitude",
                    "kind": "gate_pin",
                    "display_strategy": "leaflet_marker",
                    "linked_station_code": "GOCONG-02",
                },
            ),
        )

        reading_a = SensorReading(
            station_id=station_a.id,
            recorded_at=now - timedelta(minutes=30),
            salinity_dsm=Decimal("4.80"),
            water_level_m=Decimal("1.62"),
            temperature_c=Decimal("29.40"),
            battery_level_pct=Decimal("88.00"),
            source="simulator",
            context_payload={
                "source": "simulated-sensor",
                "quality": "good",
                "station_code": "GOCONG-01",
                "station_label": "Trạm lấy nước Gò Công Đông",
                "operational_role": "primary_intake",
            },
        )
        reading_b = SensorReading(
            station_id=station_b.id,
            recorded_at=now - timedelta(minutes=20),
            salinity_dsm=Decimal("3.10"),
            water_level_m=Decimal("1.25"),
            temperature_c=Decimal("29.10"),
            battery_level_pct=Decimal("91.50"),
            source="simulator",
            context_payload={
                "source": "simulated-sensor",
                "quality": "good",
                "station_code": "GOCONG-02",
                "station_label": "Trạm quan trắc nội đồng Gò Công",
                "operational_role": "secondary_monitoring",
            },
        )
        session.add_all([reading_a, reading_b])
        await session.flush()

        reading_b_history_1 = SensorReading(
            station_id=station_b.id,
            recorded_at=now - timedelta(minutes=75),
            salinity_dsm=Decimal("1.95"),
            water_level_m=Decimal("1.28"),
            temperature_c=Decimal("28.70"),
            battery_level_pct=Decimal("92.10"),
            source="simulator",
            context_payload={
                "source": "historical-sensor",
                "quality": "good",
                "station_code": "GOCONG-02",
                "station_label": "Trạm quan trắc nội đồng Gò Công",
                "operational_role": "secondary_monitoring",
                "phase": "advisory_window",
            },
        )
        reading_b_history_2 = SensorReading(
            station_id=station_b.id,
            recorded_at=now - timedelta(minutes=65),
            salinity_dsm=Decimal("2.42"),
            water_level_m=Decimal("1.24"),
            temperature_c=Decimal("28.90"),
            battery_level_pct=Decimal("91.80"),
            source="simulator",
            context_payload={
                "source": "historical-sensor",
                "quality": "good",
                "station_code": "GOCONG-02",
                "station_label": "Trạm quan trắc nội đồng Gò Công",
                "operational_role": "secondary_monitoring",
                "phase": "warning_rise",
            },
        )
        session.add_all([reading_b_history_1, reading_b_history_2])
        await session.flush()

        recovery_weather = WeatherSnapshot(
            region_id=region.id,
            observed_at=now - timedelta(minutes=68),
            wind_speed_mps=Decimal("5.10"),
            wind_direction_deg=135,
            tide_level_m=Decimal("1.58"),
            rainfall_mm=Decimal("0.00"),
            condition_summary="Triều đang lên nhưng chưa đạt đỉnh; gió biển vẫn đẩy mặn vào nội đồng.",
            source_payload={"provider": "simulated-weather-feed", "phase": "warning_observation"},
        )
        session.add(recovery_weather)
        await session.flush()

        recovery_risk = RiskAssessment(
            region_id=region.id,
            station_id=station_b.id,
            based_on_reading_id=reading_b_history_2.id,
            based_on_weather_id=recovery_weather.id,
            assessed_at=now - timedelta(minutes=60),
            risk_level=RiskLevel.WARNING,
            salinity_dsm=Decimal("2.42"),
            trend_direction=TrendDirection.RISING,
            trend_delta_dsm=Decimal("0.47"),
            rule_version="v1",
            summary="Độ mặn tăng trong cửa sổ cảnh giác nhưng chưa vượt ngưỡng nguy cấp.",
            rationale={
                "salinity_threshold_dsm": 2.5,
                "wind_factor": "onshore_moderate",
                "tide_factor": "rising_but_not_peak",
                "sensor_confidence": "medium",
            },
        )
        session.add(recovery_risk)
        await session.flush()

        recovery_alert = AlertEvent(
            region_id=region.id,
            risk_assessment_id=recovery_risk.id,
            triggered_at=now - timedelta(minutes=59),
            severity=RiskLevel.WARNING,
            title="Cảnh báo quan trắc mức cảnh giác",
            message="Độ mặn tăng nhưng chưa tới ngưỡng nguy cấp; ưu tiên quan sát và tái đánh giá.",
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_by="seed",
            acknowledged_at=now - timedelta(minutes=58),
        )
        session.add(recovery_alert)
        await session.flush()

        recovery_incident = Incident(
            region_id=region.id,
            station_id=station_b.id,
            risk_assessment_id=recovery_risk.id,
            title="Tăng độ mặn mức cảnh giác tại trạm nội đồng Gò Công",
            description="Cần quan sát thêm trước khi quyết định đóng/mở mô phỏng.",
            severity=RiskLevel.WARNING,
            status=IncidentStatus.INVESTIGATING,
            source="seed",
            evidence={"risk_assessment_id": str(recovery_risk.id), "alert_id": str(recovery_alert.id)},
            opened_at=now - timedelta(minutes=59),
            acknowledged_at=now - timedelta(minutes=58),
            created_by="seed",
        )
        session.add(recovery_incident)
        await session.flush()

        recovery_plan = ActionPlan(
            region_id=region.id,
            risk_assessment_id=recovery_risk.id,
            incident_id=recovery_incident.id,
            status=ActionPlanStatus.REJECTED,
            objective="Giữ quan sát và chờ cửa sổ an toàn trước khi thao tác mô phỏng.",
            generated_by="phase-2-seed",
            model_provider="mock",
            summary="Đề xuất theo dõi và chờ safe window thay vì đóng mở sớm khi dữ liệu chưa ổn định.",
            assumptions={
                "items": [
                    "Tín hiệu triều và gió vẫn còn gây áp lực mặn.",
                    "Operator ưu tiên quan sát thay vì thi hành action ngay.",
                ]
            },
            plan_steps=[
                {
                    "step_index": 1,
                    "action_type": ActionType.NOTIFY_FARMERS.value,
                    "priority": 1,
                    "title": "Gửi cảnh báo mức cảnh giác",
                    "instructions": "Thông báo cho operator và khu vực liên quan rằng hệ thống đang ở trạng thái quan sát.",
                    "rationale": "Giữ mọi bên trong cùng một nhịp đánh giá trước khi thực thi.",
                    "simulated": True,
                },
                {
                    "step_index": 2,
                    "action_type": ActionType.WAIT_SAFE_WINDOW.value,
                    "priority": 2,
                    "title": "Chờ safe window",
                    "instructions": "Không đóng/mở cống cho đến khi có ít nhất một nhịp ổn định.",
                    "rationale": "Dữ liệu hiện tại chưa đủ chắc để đảo trạng thái vận hành.",
                    "simulated": True,
                },
            ],
            validation_result={"is_valid": True, "policy": "warning_hold_then_reassess"},
        )
        session.add(recovery_plan)
        await session.flush()

        recovery_approval = Approval(
            plan_id=recovery_plan.id,
            decided_by_name="supervisor",
            decision=ApprovalDecision.REJECTED,
            comment="Chưa đủ bằng chứng ổn định để chuyển sang đóng/mở mô phỏng.",
            decided_at=now - timedelta(minutes=57),
        )
        session.add(recovery_approval)
        await session.flush()

        recovery_decision_log = DecisionLog(
            region_id=region.id,
            risk_assessment_id=recovery_risk.id,
            action_plan_id=recovery_plan.id,
            logged_at=now - timedelta(minutes=56),
            actor_type=DecisionActorType.OPERATOR,
            actor_name="operator-demo",
            summary="Operator giữ trạng thái quan sát thay vì thi hành plan sớm.",
            outcome="rejected-hold-position",
            details={
                "alert_id": str(recovery_alert.id),
                "reason": "evidence-not-stable-enough",
                "next_action": "reassess-after-20-minutes",
            },
            store_as_memory=False,
        )
        session.add(recovery_decision_log)
        await session.flush()

        recovery_memory_case = MemoryCase(
            region_id=region.id,
            station_id=station_b.id,
            risk_assessment_id=recovery_risk.id,
            incident_id=recovery_incident.id,
            action_plan_id=recovery_plan.id,
            decision_log_id=recovery_decision_log.id,
            objective="Giữ quan sát, chờ safe window",
            severity="warning",
            outcome_class="advisory_hold",
            outcome_status_legacy="rejected",
            summary="Khi ngưỡng chưa ổn định, ưu tiên theo dõi thay vì mô phỏng đóng/mở vội.",
            context_payload={
                "tide_context": "rising",
                "wind_context": "onshore_moderate",
                "scenario": "warning-observe-recover",
            },
            action_payload={
                "recommended_actions": ["notify_farmers", "wait_safe_window"],
                "approval": "rejected",
            },
            outcome_payload={
                "next_action": "reassess after 20 minutes",
                "operator_posture": "observe",
            },
            keywords=["salinity", "warning", "hold", "safe-window", "recovery"],
            occurred_at=now - timedelta(minutes=55),
        )
        session.add(recovery_memory_case)
        await session.flush()

        recovery_audit_log = AuditLog(
            event_type=AuditEventType.APPROVAL,
            actor_name="operator-demo",
            actor_role="operator",
            region_id=region.id,
            incident_id=recovery_incident.id,
            action_plan_id=recovery_plan.id,
            action_execution_id=None,
            occurred_at=now - timedelta(minutes=56),
            summary="Operator giữ trạng thái quan sát và từ chối plan mô phỏng sớm.",
            payload={"approval_id": str(recovery_approval.id), "memory_case_id": str(recovery_memory_case.id)},
        )
        session.add(recovery_audit_log)
        await session.flush()

        weather = WeatherSnapshot(
            region_id=region.id,
            observed_at=now - timedelta(minutes=25),
            wind_speed_mps=Decimal("6.40"),
            wind_direction_deg=135,
            tide_level_m=Decimal("1.72"),
            rainfall_mm=Decimal("0.00"),
            condition_summary="Gió từ biển thổi vào, triều đang lên.",
            source_payload={"provider": "simulated-weather-feed"},
        )
        session.add(weather)
        await session.flush()

        risk = RiskAssessment(
            region_id=region.id,
            station_id=station_a.id,
            based_on_reading_id=reading_a.id,
            based_on_weather_id=weather.id,
            assessed_at=now - timedelta(minutes=15),
            risk_level=RiskLevel.DANGER,
            salinity_dsm=Decimal("4.80"),
            trend_direction=TrendDirection.RISING,
            trend_delta_dsm=Decimal("0.90"),
            rule_version="v1",
            summary="Độ mặn đang vượt ngưỡng tưới và còn tiếp tục tăng.",
            rationale={
                "salinity_threshold_dsm": 4.0,
                "wind_factor": "đẩy mặn vào sâu hơn",
                "tide_factor": "cửa triều đang cao",
            },
        )
        session.add(risk)
        await session.flush()

        alert = AlertEvent(
            region_id=region.id,
            risk_assessment_id=risk.id,
            triggered_at=now - timedelta(minutes=14),
            severity=RiskLevel.DANGER,
            title="Cảnh báo xâm nhập mặn nguy cấp",
            message="Độ mặn quan sát được vượt ngưỡng cho phép gần cống lấy nước chính.",
        )
        session.add(alert)
        await session.flush()

        incident = Incident(
            region_id=region.id,
            station_id=station_a.id,
            risk_assessment_id=risk.id,
            title="Sự cố xâm nhập mặn tại cống lấy nước Gò Công Đông",
            description="Độ mặn vượt ngưỡng tưới và cần luồng phản ứng có giám sát.",
            severity=RiskLevel.DANGER,
            status=IncidentStatus.APPROVED,
            source="seed",
            evidence={"risk_assessment_id": str(risk.id), "alert_id": str(alert.id)},
            opened_at=now - timedelta(minutes=14),
            acknowledged_at=now - timedelta(minutes=12),
            created_by="seed",
        )
        session.add(incident)
        await session.flush()

        plan = ActionPlan(
            region_id=region.id,
            risk_assessment_id=risk.id,
            incident_id=incident.id,
            status=ActionPlanStatus.APPROVED,
            objective="Giảm lượng nước mặn đi vào hệ thống trong cửa sổ rủi ro đang hoạt động.",
            generated_by="phase-2-seed",
            model_provider="mock",
            summary="Thông báo các bên liên quan, tạm ngưng lấy nước và mô phỏng đóng cống cho đến khi điều kiện an toàn hơn.",
            assumptions={
                "items": [
                    "Operator có mặt để duyệt plan.",
                    "Tất cả hành động đều là mock/simulated cho bản demo.",
                ]
            },
            plan_steps=[
                {
                    "step_index": 1,
                    "action_type": ActionType.SEND_ALERT.value,
                    "priority": 1,
                    "title": "Gửi cảnh báo tới các bên",
                    "instructions": "Thông báo cho operator và nông dân qua các kênh mô phỏng.",
                    "rationale": "Các bên liên quan cần biết ngay trước khi thay đổi vận hành.",
                    "simulated": True,
                },
                {
                    "step_index": 2,
                    "action_type": ActionType.CLOSE_GATE.value,
                    "priority": 2,
                    "title": "Mô phỏng đóng cống lấy nước",
                    "instructions": "Chạy execution mô phỏng đóng cống cho điểm lấy nước chính.",
                    "rationale": "Giảm lấy nước trong giai đoạn salinity cao sẽ giảm phơi nhiễm.",
                    "simulated": True,
                },
            ],
            validation_result={"is_valid": True, "policy": "simulated-actions-only"},
        )
        session.add(plan)
        await session.flush()

        approval = Approval(
            plan_id=plan.id,
            decided_by_name="supervisor",
            decision=ApprovalDecision.APPROVED,
            comment="Phê duyệt seed cho luồng demo cục bộ.",
            decided_at=now - timedelta(minutes=11),
        )
        session.add(approval)
        await session.flush()

        execution = ActionExecution(
            plan_id=plan.id,
            region_id=region.id,
            action_type=ActionType.CLOSE_GATE,
            status=ExecutionStatus.SUCCEEDED,
            simulated=True,
            step_index=2,
            started_at=now - timedelta(minutes=10),
            completed_at=now - timedelta(minutes=8),
            result_summary="Đã mô phỏng đóng cống thành công.",
            result_payload={"estimated_effect": "giảm nước mặn đi vào", "confidence": "medium"},
            idempotency_key="seed-close-gate-001",
            requested_by="supervisor",
        )
        session.add(execution)
        await session.flush()

        notification = Notification(
            incident_id=incident.id,
            execution_id=execution.id,
            channel=NotificationChannel.DASHBOARD,
            status=NotificationStatus.SENT,
            recipient="dashboard",
            subject="Phản ứng mặn đã được seed",
            message="Thông báo dashboard mô phỏng cho plan response đã được seed.",
            payload={"mock": True},
            sent_at=now - timedelta(minutes=8),
        )
        session.add(notification)
        await session.flush()

        document = KnowledgeDocument(
            title="Hướng dẫn phản ứng xâm nhập mặn Mekong",
            source_uri="mekong-salt://knowledge/guideline-001",
            document_type="guideline",
            summary="Các bước phản ứng chung cho tình huống xâm nhập mặn cao.",
            content_text=(
                "Khi độ mặn tăng cao, cần tạm dừng lấy nước, thông báo operator, theo dõi triều, "
                "và chỉ mở lại khi readings đã trở xuống dưới ngưỡng cho phép."
            ),
            tags=["salinity", "response", "irrigation"],
            metadata_payload={"language": "vi", "source": "internal-seed"},
        )
        session.add(document)
        await session.flush()

        chunk = EmbeddedChunk(
            document_id=document.id,
            chunk_index=0,
            content_text=document.content_text,
            token_count=29,
            embedding=[0.001] * 768,
            metadata_payload={"section": "overview"},
        )
        session.add(chunk)
        await session.flush()

        reference_documents = [
            {
                "title": "Bộ tiêu chí ngưỡng salinity Mekong-SALT",
                "source_uri": "mekong-salt://knowledge/threshold-matrix-002",
                "document_type": "threshold",
                "summary": "Tóm tắt ngưỡng band, fast-rise, và ngưỡng approval để dùng trong planning context.",
                "content_text": (
                    "Canonical storage and comparison unit is dS/m. Warning band starts at 1.0 dS/m, danger band starts at 2.5 dS/m, "
                    "critical band starts at 4.0 dS/m, and a fast-rise modifier begins around 0.3 dS/m over the assessment window. "
                    "For hackathon operations, the recommendation is to recheck every 20 minutes, keep HITL mandatory for danger or critical outcomes, "
                    "and treat weather or tide as modifiers rather than overrides."
                ),
                "tags": ["salinity", "threshold", "policy", "planning"],
                "metadata_payload": {"language": "vi", "source": "internal-seed", "reference_kind": "policy-summary"},
            },
            {
                "title": "Ghi chú vận hành gió - triều cho quyết định mặn",
                "source_uri": "mekong-salt://knowledge/guideline-002",
                "document_type": "guideline",
                "summary": "Quy tắc diễn giải gió và triều để hỗ trợ quan sát mặn.",
                "content_text": (
                    "Onshore wind and rising tide generally increase saline intrusion pressure near intake points. When tide is falling and salinity trend is stable or declining, "
                    "the system may enter a candidate recovery window, but a one-cycle dip should not be treated as confirmed recovery. Every advisory should include a next review timestamp, "
                    "and any outbound message must state whether the action is simulation-only. Local station anomalies always need sensor confidence checks."
                ),
                "tags": ["weather", "tide", "salinity", "operations"],
                "metadata_payload": {"language": "vi", "source": "internal-seed", "reference_kind": "operational-guidance"},
            },
            {
                "title": "Checklist đóng mở và phục hồi an toàn",
                "source_uri": "mekong-salt://knowledge/sop-002",
                "document_type": "sop",
                "summary": "Checklist rút gọn cho đóng/mở mô phỏng và recovery window.",
                "content_text": (
                    "Before reopening intake, require three consecutive below-warning readings, no fast-rise signal in the latest window, and no adverse tide or wind trigger. "
                    "Reopening should be staged: partial then full. After closure or reopening, continue stakeholder notifications until the trend stabilizes and capture a memory case for later retrieval. "
                    "If provenance confidence is insufficient, reject execution and hold position for another reassessment cycle."
                ),
                "tags": ["sop", "closure", "recovery", "approval"],
                "metadata_payload": {"language": "vi", "source": "internal-seed", "reference_kind": "closure-checklist"},
            },
        ]

        for index, item in enumerate(reference_documents, start=1):
            reference_document = KnowledgeDocument(
                title=item["title"],
                source_uri=item["source_uri"],
                document_type=item["document_type"],
                summary=item["summary"],
                content_text=item["content_text"],
                tags=item["tags"],
                metadata_payload=item["metadata_payload"],
            )
            session.add(reference_document)
            await session.flush()

            reference_chunk = EmbeddedChunk(
                document_id=reference_document.id,
                chunk_index=0,
                content_text=reference_document.content_text,
                token_count=len(reference_document.content_text.split()),
                embedding=[0.002 + (index * 0.001)] * 768,
                metadata_payload={"section": "reference", "seed_source": "internal-seed"},
            )
            session.add(reference_chunk)
            await session.flush()

        decision_log = DecisionLog(
            region_id=region.id,
            risk_assessment_id=risk.id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            logged_at=now - timedelta(minutes=7),
            actor_type=DecisionActorType.SYSTEM,
            actor_name="phase-2-seed",
            summary="Seed gắn kết assessment, plan và execution mô phỏng.",
            outcome="simulated-success",
            details={
                "alert_id": str(alert.id),
                "document_id": str(document.id),
                "notes": "Dùng cho môi trường local development và validation persistence.",
            },
            store_as_memory=False,
        )
        session.add(decision_log)

        audit_log = AuditLog(
            event_type=AuditEventType.EXECUTION,
            actor_name="supervisor",
            actor_role="supervisor",
            region_id=region.id,
            incident_id=incident.id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            occurred_at=now - timedelta(minutes=7),
            summary="Seed plan đã được phê duyệt và execution mô phỏng.",
            payload={"notification_id": str(notification.id), "approval_id": str(approval.id)},
        )
        session.add(audit_log)

        await session.commit()

    logger.info("Đã hoàn tất seed demo với bộ dữ liệu trạm/cống thực tế hơn.")
    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(run_seed())
