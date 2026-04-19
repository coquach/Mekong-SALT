"""Seed the database with minimal realistic safe baseline data."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.db.base import Base
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import AsyncSessionFactory, close_database_engine
from app.models import (
    EmbeddedChunk,
    Gate,
    KnowledgeDocument,
    MonitoringGoal,
    RiskAssessment,
    Region,
    SensorReading,
    SensorStation,
    WeatherSnapshot,
)
from app.models.enums import GateStatus, RiskLevel, StationStatus, TrendDirection
from app.repositories.gate import GateRepository
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository

logger = logging.getLogger(__name__)


async def _reset_all_demo_data(session) -> None:
    """Truncate existing application rows so each seed starts from a clean slate."""
    table_names = ", ".join(_format_table_name(table) for table in Base.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    await session.flush()


def _format_table_name(table) -> str:
    """Return a safely quoted table identifier for the current database dialect."""
    if table.schema:
        return f'"{table.schema}"."{table.name}"'
    return f'"{table.name}"'


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


def _discover_sample_documents(*, backend_root: Path) -> list[dict[str, object]]:
    """Discover bundled RAG sample files that should be seeded as knowledge documents."""
    samples_root = backend_root / "document" / "rag_samples"
    if not samples_root.exists():
        return []

    supported_extensions = {".txt", ".md", ".rst", ".json", ".yaml", ".yml", ".log", ".csv"}
    manifest: list[dict[str, object]] = []

    for file_path in sorted(samples_root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name.lower() == "readme.md":
            continue
        if file_path.suffix.lower() not in supported_extensions:
            continue

        relative_path = file_path.relative_to(backend_root).as_posix()
        content_text = file_path.read_text(encoding="utf-8").strip()
        category = _resolve_sample_category(file_path, samples_root)

        manifest.append(
            {
                "relative_path": relative_path,
                "title": _build_sample_title(file_path.stem),
                "source_uri": _build_sample_source_uri(relative_path),
                "document_type": category,
                "summary": _build_sample_summary(
                    file_path=file_path,
                    content_text=content_text,
                    category=category,
                ),
                "content_text": content_text,
                "tags": _build_sample_tags(
                    category=category,
                    file_path=file_path,
                    content_text=content_text,
                ),
                "metadata": {
                    "language": "en",
                    "source": "rag_samples",
                    "sample_pack": "backend/document/rag_samples",
                    "relative_path": relative_path,
                    "category": category,
                    "file_extension": file_path.suffix.lower().lstrip("."),
                },
            }
        )

    return manifest


def _resolve_sample_category(file_path: Path, samples_root: Path) -> str:
    try:
        category = file_path.relative_to(samples_root).parts[0].strip().lower()
    except ValueError:
        category = "guideline"
    if category in {"sop", "threshold", "casebook", "guideline"}:
        return category
    return "guideline"


def _build_sample_title(stem: str) -> str:
    title = stem.replace("_", " ").replace("-", " ").strip()
    title = " ".join(part for part in title.split() if part)
    if not title:
        return "Sample Document"
    return title.title()


def _build_sample_source_uri(relative_path: str) -> str:
    safe = relative_path.lower().replace(" ", "-")
    safe = "".join(character for character in safe if character.isalnum() or character in {"-", "_", "/", "."})
    safe = safe.replace(".", "-")
    return f"mekong-salt://samples/{safe}"


def _build_sample_tags(*, category: str, file_path: Path, content_text: str) -> list[str]:
    tags = [category, "sample"]
    extension = file_path.suffix.lower().lstrip(".")
    if extension and extension not in tags:
        tags.append(extension)

    stem = file_path.stem.lower()
    for token in (
        "salinity",
        "water",
        "quality",
        "irrigation",
        "policy",
        "report",
        "weather",
        "tide",
        "sensor",
        "calibration",
        "closure",
        "recovery",
    ):
        if token in stem and token not in tags:
            tags.append(token)

    content_lower = content_text.lower()
    for token in ("policy", "sensor", "weather", "salinity", "recovery"):
        if token in content_lower and token not in tags:
            tags.append(token)

    return tags


def _build_sample_summary(*, file_path: Path, content_text: str, category: str) -> str:
    lines = [line.strip() for line in content_text.splitlines() if line.strip()]
    if not lines:
        return f"{category.title()} sample document from rag_samples."

    if file_path.suffix.lower() == ".csv":
        row_count = max(len(lines) - 1, 0)
        header = lines[0].split(",")[:4]
        header_preview = ", ".join(part.strip() for part in header if part.strip())
        if header_preview:
            return f"{category.title()} sample table with {row_count} records and columns {header_preview}."
        return f"{category.title()} sample table with {row_count} records."

    for line in lines:
        if line.startswith("#"):
            continue
        if len(line) >= 40:
            return line[:255]

    return lines[0][:255]


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
    """Insert a connected safe baseline dataset for local development."""
    settings = get_settings()
    configure_logging(settings.log_level)
    now = datetime.now(UTC)
    backend_root = Path(__file__).resolve().parents[1]

    async with AsyncSessionFactory() as session:
        region_repo = RegionRepository(session)
        station_repo = SensorStationRepository(session)

        await _reset_all_demo_data(session)
        logger.info("Đã xóa toàn bộ dữ liệu demo cũ trước khi seed mới")

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
            status=GateStatus.OPEN,
            latitude=Decimal("10.317250"),
            longitude=Decimal("106.463346"),
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
            status=GateStatus.OPEN,
            latitude=Decimal("10.336566"),
            longitude=Decimal("106.411532"),
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
            latitude=Decimal("10.336632"),
            longitude=Decimal("106.427931"),
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
            latitude=Decimal("10.244237"),
            longitude=Decimal("106.700512"),
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

        readings = [
            SensorReading(
                station_id=station_a.id,
                recorded_at=now - timedelta(minutes=70),
                salinity_dsm=Decimal("0.74"),
                water_level_m=Decimal("1.58"),
                temperature_c=Decimal("29.00"),
                battery_level_pct=Decimal("88.40"),
                source="simulator",
                context_payload={
                    "source": "historical-sensor",
                    "quality": "good",
                    "station_code": "GOCONG-01",
                    "station_label": "Trạm lấy nước Gò Công Đông",
                    "operational_role": "primary_intake",
                    "phase": "baseline_safe",
                },
            ),
            SensorReading(
                station_id=station_a.id,
                recorded_at=now - timedelta(minutes=50),
                salinity_dsm=Decimal("0.79"),
                water_level_m=Decimal("1.60"),
                temperature_c=Decimal("29.20"),
                battery_level_pct=Decimal("88.20"),
                source="simulator",
                context_payload={
                    "source": "historical-sensor",
                    "quality": "good",
                    "station_code": "GOCONG-01",
                    "station_label": "Trạm lấy nước Gò Công Đông",
                    "operational_role": "primary_intake",
                    "phase": "baseline_safe",
                },
            ),
            SensorReading(
                station_id=station_a.id,
                recorded_at=now - timedelta(minutes=30),
                salinity_dsm=Decimal("0.82"),
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
                    "phase": "baseline_safe",
                },
            ),
            SensorReading(
                station_id=station_b.id,
                recorded_at=now - timedelta(minutes=75),
                salinity_dsm=Decimal("0.70"),
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
                    "phase": "baseline_safe",
                },
            ),
            SensorReading(
                station_id=station_b.id,
                recorded_at=now - timedelta(minutes=65),
                salinity_dsm=Decimal("0.74"),
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
                    "phase": "baseline_safe",
                },
            ),
            SensorReading(
                station_id=station_b.id,
                recorded_at=now - timedelta(minutes=20),
                salinity_dsm=Decimal("0.78"),
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
                    "phase": "baseline_safe",
                },
            ),
        ]
        session.add_all(readings)
        await session.flush()

        weather_snapshots = [
            WeatherSnapshot(
                region_id=region.id,
                observed_at=now - timedelta(minutes=40),
                wind_speed_mps=Decimal("3.20"),
                wind_direction_deg=135,
                tide_level_m=Decimal("1.10"),
                rainfall_mm=Decimal("0.00"),
                condition_summary="Điều kiện nền ổn định, chưa có áp lực mặn đáng kể.",
                source_payload={
                    "provider": "simulated-weather-feed",
                    "phase": "baseline_safe",
                },
            ),
            WeatherSnapshot(
                region_id=region.id,
                observed_at=now - timedelta(minutes=10),
                wind_speed_mps=Decimal("3.60"),
                wind_direction_deg=140,
                tide_level_m=Decimal("1.18"),
                rainfall_mm=Decimal("0.00"),
                condition_summary="Thời tiết và thủy triều ổn định, phù hợp trạng thái quan trắc an toàn ban đầu.",
                source_payload={
                    "provider": "simulated-weather-feed",
                    "phase": "baseline_safe_latest",
                },
            ),
        ]
        session.add_all(weather_snapshots)
        await session.flush()

        monitoring_goal = MonitoringGoal(
            name="GO-CONG-PRIMARY-INTAKE-PLAN",
            description=(
                "Active monitoring goal for the main intake station so the worker can trigger "
                "plan generation from fresh sensor frames."
            ),
            region_id=region.id,
            station_id=station_a.id,
            objective=(
                "Bảo vệ chất lượng nước tưới tại cửa lấy nước Gò Công Đông và phản ứng khi độ mặn tăng."
            ),
            provider="mock",
            warning_threshold_dsm=Decimal("2.50"),
            critical_threshold_dsm=Decimal("4.00"),
            evaluation_interval_minutes=1,
            is_active=True,
        )
        monitoring_goal_b = MonitoringGoal(
            name="GO-CONG-INLAND-MONITOR",
            description=(
                "Active monitoring goal for the inland station so the worker can also "
                "evaluate risk from fresh sensor frames at GOCONG-02."
            ),
            region_id=region.id,
            station_id=station_b.id,
            objective=(
                "Theo dõi độ mặn nội đồng tại Gò Công và phát hiện sớm xu hướng lan truyền mặn."
            ),
            provider="mock",
            warning_threshold_dsm=Decimal("2.50"),
            critical_threshold_dsm=Decimal("4.00"),
            evaluation_interval_minutes=1,
            is_active=True,
        )
        session.add_all([monitoring_goal, monitoring_goal_b])
        await session.flush()

        base_document = KnowledgeDocument(
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
        session.add(base_document)
        await session.flush()

        base_chunk = EmbeddedChunk(
            document_id=base_document.id,
            chunk_index=0,
            content_text=base_document.content_text,
            token_count=29,
            embedding=[0.001] * 768,
            metadata_payload={"section": "overview"},
        )
        session.add(base_chunk)
        await session.flush()

        sample_documents = _discover_sample_documents(backend_root=backend_root)

        for index, item in enumerate(sample_documents, start=1):
            reference_document = KnowledgeDocument(
                title=item["title"],
                source_uri=item["source_uri"],
                document_type=item["document_type"],
                summary=item["summary"],
                content_text=item["content_text"],
                tags=item["tags"],
                metadata_payload=item["metadata"],
            )
            session.add(reference_document)
            await session.flush()

            reference_chunk = EmbeddedChunk(
                document_id=reference_document.id,
                chunk_index=0,
                content_text=reference_document.content_text,
                token_count=len(reference_document.content_text.split()),
                embedding=[0.002 + (index * 0.001)] * 768,
                metadata_payload={
                    "section": "reference",
                    "seed_source": "rag_samples",
                    "relative_path": item["relative_path"],
                },
            )
            session.add(reference_chunk)
            await session.flush()

        await session.commit()

    logger.info("Đã hoàn tất seed baseline cho demo worker + simulator + active monitoring goal.")
    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(run_seed())
