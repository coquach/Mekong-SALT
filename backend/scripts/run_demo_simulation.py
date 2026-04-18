"""Scenario-driven sensor publish stream for Mekong-SALT demo flows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import time
from typing import Any, Callable
from urllib import error, parse, request

from app.core.salinity_units import dsm_to_gl

UTC = timezone.utc


class SimulationError(RuntimeError):
    """Raised when one scenario cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class SensorFrame:
    """One synthetic reading in a sensor scenario timeline."""

    salinity_dsm: str
    water_level_m: str
    temperature_c: str
    battery_level_pct: str
    wind_speed_mps: str | None = None
    wind_direction_deg: int | None = None
    flow_rate_m3s: str | None = None
    pause_seconds: float = 0.0
    note: str = ""


@dataclass(frozen=True, slots=True)
class SensorScenarioProfile:
    """Scenario settings used to trigger monitoring -> planning -> lifecycle flows."""

    key: str
    description: str
    objective: str
    warning_threshold_dsm: str
    critical_threshold_dsm: str
    frames: tuple[SensorFrame, ...]
    post_planning_frame: SensorFrame | None = None


@dataclass(slots=True)
class SimulationRuntimeConfig:
    """Transport configuration for scenario sensor emission."""

    transport: str = "http"
    mqtt_broker_url: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_sensor_readings: str = "mekong/sensors/readings"
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_client_id: str = "mekong-salt-demo-simulation"
    mqtt_qos: int = 1


SCENARIO_SENSOR_PROFILES: dict[str, SensorScenarioProfile] = {
    "critical-timeout-replan": SensorScenarioProfile(
        key="critical-timeout-replan",
        description="Tăng dần độ mặn lên mức nguy cấp, rồi giữ thêm một nhịp hậu planning để chờ auto-reject.",
        objective="Xử lý leo thang độ mặn nguy cấp với luồng HITL bắt buộc và timeout tự từ chối.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.90", "1.48", "29.20", "84.00", note="mốc nguy cơ ban đầu"),
            SensorFrame("4.45", "1.60", "29.40", "83.70", note="vượt ngưỡng nguy cấp"),
            SensorFrame("5.15", "1.72", "29.70", "83.20", note="duy trì trạng thái nguy cấp"),
        ),
        post_planning_frame=SensorFrame(
            "5.30",
            "1.76",
            "29.82",
            "82.90",
            note="nhịp hậu planning để mô phỏng cảnh báo kéo dài",
        ),
    ),
    "fast-approve-execute": SensorScenarioProfile(
        key="fast-approve-execute",
        description="Bắn dữ liệu rủi ro cao, tạo plan pending, sau đó duyệt và mô phỏng thực thi.",
        objective="Sinh ra plan hành động có thể duyệt nhanh cho operator và kiểm tra luồng feedback.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.35", "1.30", "28.90", "88.50", note="cảnh báo tăng"),
            SensorFrame("4.05", "1.42", "29.10", "88.00", note="chạm ngưỡng nguy cấp"),
            SensorFrame("4.60", "1.55", "29.30", "87.60", note="kích hoạt pending plan"),
        ),
        post_planning_frame=SensorFrame(
            "4.18",
            "1.46",
            "29.18",
            "87.40",
            note="nhịp hậu planning trước khi duyệt plan",
        ),
    ),
    "rag-provenance-drilldown": SensorScenarioProfile(
        key="rag-provenance-drilldown",
        description="Đẩy dữ liệu giàu ngữ cảnh để kích hoạt planning mới và soi trace truy hồi.",
        objective="Tạo plan cần lập luận có bằng chứng để briefing operator rõ hơn.",
        warning_threshold_dsm="2.30",
        critical_threshold_dsm="3.90",
        frames=(
            SensorFrame("2.60", "1.12", "28.60", "91.00", note="mở đầu cảnh báo"),
            SensorFrame("3.20", "1.24", "28.80", "90.50", note="xu hướng tăng"),
            SensorFrame("3.85", "1.36", "29.00", "90.10", note="tiệm cận nguy cấp"),
        ),
        post_planning_frame=SensorFrame(
            "3.92",
            "1.38",
            "29.04",
            "89.85",
            note="nhịp hậu planning để giữ trace truy hồi sống",
        ),
    ),
    "warning-observe-recover": SensorScenarioProfile(
        key="warning-observe-recover",
        description="Gây cảnh báo mức vừa rồi để backend đi qua cửa sổ quan sát và hồi phục tự nhiên.",
        objective="Quan sát nhịp warning, giữ posture thận trọng, rồi kiểm tra recovery window.",
        warning_threshold_dsm="1.80",
        critical_threshold_dsm="3.20",
        frames=(
            SensorFrame("1.92", "1.16", "28.70", "92.20", wind_speed_mps="5.20", wind_direction_deg=135, note="cảnh giác ban đầu"),
            SensorFrame("2.18", "1.18", "28.82", "91.90", wind_speed_mps="5.80", wind_direction_deg=130, note="xu hướng tăng nhưng chưa tới critical"),
            SensorFrame("2.05", "1.15", "28.76", "91.70", wind_speed_mps="5.10", wind_direction_deg=145, note="giữ ở warning"),
        ),
        post_planning_frame=SensorFrame(
            "1.68",
            "1.12",
            "28.60",
            "91.50",
            wind_speed_mps="4.30",
            wind_direction_deg=160,
            note="recovery window bắt đầu mở ra",
        ),
    ),
}

RUNTIME_CONFIG = SimulationRuntimeConfig()

DEFAULT_FRAME_PAUSE_SECONDS = 10.0
DEFAULT_TIMEOUT_SECONDS = 300

def _to_query(params: dict[str, Any]) -> str:
    encoded = parse.urlencode(
        {key: value for key, value in params.items() if value is not None},
        doseq=True,
    )
    return f"?{encoded}" if encoded else ""


def _to_decimal(raw: Any, *, fallback: str) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(fallback)


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _format_salinity_dual(value_dsm: str | Decimal | None) -> str:
    if value_dsm is None:
        return "- dS/m / - g/L"
    value_decimal = _to_decimal(value_dsm, fallback="0.00")
    value_gl = dsm_to_gl(value_decimal)
    return f"{_format_decimal(value_decimal)} dS/m (~{value_gl} g/L)"


def _http_json(
    *,
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    data: bytes | None = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, method=method.upper(), headers=headers, data=data)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise SimulationError(f"HTTP {exc.code} {method} {path}: {detail}") from exc
    except error.URLError as exc:
        raise SimulationError(f"Network error {method} {path}: {exc}") from exc

    if not body.strip():
        return {}

    parsed = json.loads(body)
    if isinstance(parsed, dict) and "data" in parsed:
        return parsed["data"]
    if isinstance(parsed, dict):
        return parsed
    raise SimulationError(f"Unexpected response format from {method} {path}: {type(parsed)}")


def _ensure_server_ready(base_url: str) -> None:
    try:
        _http_json(base_url=base_url, method="GET", path="/api/v1/health", timeout=10)
    except SimulationError as exc:
        raise SimulationError(
            "Backend API chưa sẵn sàng. Hãy khởi động server trước với: "
            "./.venv/Scripts/python.exe -m uvicorn main:app --reload"
        ) from exc


def _poll(
    *,
    description: str,
    timeout_seconds: int,
    interval_seconds: float,
    condition: Callable[[], tuple[bool, Any]],
) -> Any:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        ok, value = condition()
        if ok:
            print(f"[OK] {description}")
            return value
        time.sleep(interval_seconds)
    raise SimulationError(f"Timeout while waiting for: {description}")


def _list_plans(base_url: str, *, limit: int = 50) -> list[dict[str, Any]]:
    payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/plans{_to_query({'limit': limit})}",
    )
    return payload if isinstance(payload, list) else []


def _list_agent_runs(base_url: str, *, limit: int = 80) -> list[dict[str, Any]]:
    payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/agent/runs{_to_query({'limit': limit})}",
    )
    items = list((payload or {}).get("items") or [])
    return items


def _resolve_station_scope(base_url: str, *, station_code: str | None = None) -> dict[str, str]:
    payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/readings/latest{_to_query({'limit': 200, 'station_code': station_code})}",
    )
    items = list((payload or {}).get("items") or [])
    if not items:
        raise SimulationError("Không tìm thấy reading của trạm nào. Hãy chạy seed/setup trước.")

    target = items[0]
    station = target.get("station") or {}
    code = str(station.get("code") or "")
    station_id = str(station.get("id") or "")
    region_id = str(station.get("region_id") or "")
    if not code or not station_id or not region_id:
        raise SimulationError("Payload trạm thiếu code/id/region_id.")

    return {
        "station_code": code,
        "station_id": station_id,
        "region_id": region_id,
    }


def _goal_name(profile_key: str, station_code: str) -> str:
    return f"demo-sensor-{profile_key}-{station_code}".lower()


def _ensure_monitoring_goal(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    station_scope: dict[str, str],
) -> dict[str, Any]:
    name = _goal_name(profile.key, station_scope["station_code"])
    goals_payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/goals{_to_query({'limit': 500, 'is_active': True})}",
    )
    goals = list((goals_payload or {}).get("items") or [])
    existing = next((item for item in goals if str(item.get("name")) == name), None)

    body = {
        "name": name,
        "description": f"Scenario-driven sensor goal for {profile.key}",
        "region_id": station_scope["region_id"],
        "station_id": station_scope["station_id"],
        "objective": profile.objective,
        "provider": "gemini",
        "thresholds": {
            "warning_threshold_dsm": profile.warning_threshold_dsm,
            "critical_threshold_dsm": profile.critical_threshold_dsm,
        },
        "evaluation_interval_minutes": 1,
        "auto_plan_enabled": True,
        "is_active": True,
    }

    if existing is None:
        created = _http_json(base_url=base_url, method="POST", path="/api/v1/goals", payload=body)
        print(f"[OK] Created monitoring goal {name}")
        return created

    goal_id = str(existing.get("id") or "")
    if not goal_id:
        raise SimulationError(f"Goal '{name}' is missing id.")

    patch_body = {
        "objective": body["objective"],
        "station_id": body["station_id"],
        "region_id": body["region_id"],
        "thresholds": body["thresholds"],
        "evaluation_interval_minutes": body["evaluation_interval_minutes"],
        "auto_plan_enabled": True,
        "is_active": True,
        "provider": "gemini",
    }
    updated = _http_json(
        base_url=base_url,
        method="PATCH",
        path=f"/api/v1/goals/{goal_id}",
        payload=patch_body,
    )
    print(f"[OK] Reused monitoring goal {name}")
    return updated


def _close_open_incidents(base_url: str, *, region_id: str) -> list[str]:
    payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/incidents{_to_query({'region_id': region_id, 'limit': 200})}",
    )
    incidents = list((payload or {}).get("items") or [])
    closed_ids: list[str] = []
    for incident in incidents:
        incident_id = str(incident.get("id") or "")
        status = str(incident.get("status") or "")
        if not incident_id or status in {"resolved", "closed"}:
            continue
        _http_json(
            base_url=base_url,
            method="PATCH",
            path=f"/api/v1/incidents/{incident_id}",
            payload={
                "status": "closed",
                "note": "Closed by demo simulation reset to allow a fresh scenario trigger.",
            },
        )
        closed_ids.append(incident_id)
    if closed_ids:
        print(f"[OK] Closed {len(closed_ids)} open incidents for scenario reset")
    return closed_ids


def _build_sensor_frame_payload(
    *,
    profile: SensorScenarioProfile,
    frame: SensorFrame,
    frame_index: int,
    station_code: str,
    recorded_at: datetime,
    phase: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "station_code": station_code,
        "recorded_at": recorded_at.replace(microsecond=0).isoformat(),
        "salinity_dsm": frame.salinity_dsm,
        "water_level_m": frame.water_level_m,
        "temperature_c": frame.temperature_c,
        "battery_level_pct": frame.battery_level_pct,
        "source": "demo-simulation",
        "context_payload": {
            "scenario": profile.key,
            "frame_index": frame_index,
            "phase": phase,
            "frame_note": frame.note,
            "description": profile.description,
        },
    }
    if frame.wind_speed_mps is not None:
        payload["wind_speed_mps"] = frame.wind_speed_mps
    if frame.wind_direction_deg is not None:
        payload["wind_direction_deg"] = frame.wind_direction_deg
    if frame.flow_rate_m3s is not None:
        payload["flow_rate_m3s"] = frame.flow_rate_m3s
    return payload


def _open_mqtt_client() -> tuple[Any, Any]:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:  # pragma: no cover - environment dependency
        raise SimulationError(
            "Missing dependency 'paho-mqtt'. Install backend dependencies first."
        ) from exc

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=RUNTIME_CONFIG.mqtt_client_id,
        protocol=mqtt.MQTTv311,
    )
    if RUNTIME_CONFIG.mqtt_username:
        client.username_pw_set(
            RUNTIME_CONFIG.mqtt_username,
            RUNTIME_CONFIG.mqtt_password,
        )

    try:
        client.connect(
            host=RUNTIME_CONFIG.mqtt_broker_url,
            port=RUNTIME_CONFIG.mqtt_broker_port,
            keepalive=30,
        )
    except OSError as exc:
        raise SimulationError(
            f"Cannot connect MQTT broker {RUNTIME_CONFIG.mqtt_broker_url}:{RUNTIME_CONFIG.mqtt_broker_port}: {exc}"
        ) from exc

    client.loop_start()
    return client, mqtt


def _publish_sensor_reading_via_mqtt(
    *,
    mqtt_client: Any,
    mqtt_lib: Any,
    payload: dict[str, Any],
) -> None:
    publish_info = mqtt_client.publish(
        topic=RUNTIME_CONFIG.mqtt_topic_sensor_readings,
        payload=json.dumps(payload, ensure_ascii=True),
        qos=RUNTIME_CONFIG.mqtt_qos,
        retain=False,
    )
    publish_info.wait_for_publish()
    if publish_info.rc != mqtt_lib.MQTT_ERR_SUCCESS:
        raise SimulationError(
            f"MQTT publish failed rc={publish_info.rc} topic={RUNTIME_CONFIG.mqtt_topic_sensor_readings}"
        )


def _emit_sensor_frame(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    frame: SensorFrame,
    frame_index: int,
    station_code: str,
    recorded_at: datetime,
    phase: str,
    mqtt_client: Any | None = None,
    mqtt_lib: Any | None = None,
) -> dict[str, Any]:
    payload = _build_sensor_frame_payload(
        profile=profile,
        frame=frame,
        frame_index=frame_index,
        station_code=station_code,
        recorded_at=recorded_at,
        phase=phase,
    )

    if RUNTIME_CONFIG.transport == "mqtt":
        if mqtt_client is None or mqtt_lib is None:
            raise SimulationError("Đang bật MQTT nhưng publisher chưa sẵn sàng.")
        _publish_sensor_reading_via_mqtt(
            mqtt_client=mqtt_client,
            mqtt_lib=mqtt_lib,
            payload=payload,
        )
    else:
        _http_json(
            base_url=base_url,
            method="POST",
            path="/api/v1/sensors/ingest",
            payload=payload,
        )

    return payload


def _ingest_sensor_profile(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    station_code: str,
    frame_pause_seconds: float,
    phase: str,
) -> list[dict[str, Any]]:
    base_time = datetime.now(UTC)
    emitted: list[dict[str, Any]] = []
    mqtt_client: Any | None = None
    mqtt_lib: Any | None = None
    if RUNTIME_CONFIG.transport == "mqtt":
        mqtt_client, mqtt_lib = _open_mqtt_client()

    try:
        elapsed_seconds = 0.0
        for index, frame in enumerate(profile.frames, start=1):
            recorded_at = base_time + timedelta(seconds=elapsed_seconds)
            payload = _emit_sensor_frame(
                base_url,
                profile=profile,
                frame=frame,
                frame_index=index,
                station_code=station_code,
                recorded_at=recorded_at,
                phase=phase,
                mqtt_client=mqtt_client,
                mqtt_lib=mqtt_lib,
            )
            emitted.append(payload)
            print(
                f"[OK] Emitted frame {index}/{len(profile.frames)} via {RUNTIME_CONFIG.transport.upper()} "
                f"salinity={_format_salinity_dual(frame.salinity_dsm)} note={frame.note or '-'}"
            )

            pause = max(frame_pause_seconds, frame.pause_seconds, DEFAULT_FRAME_PAUSE_SECONDS)
            if index < len(profile.frames) and pause > 0:
                time.sleep(pause)
                elapsed_seconds += pause
    finally:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

    return emitted


def _ingest_follow_up_frame(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    frame: SensorFrame,
    station_code: str,
    frame_index: int,
    frame_pause_seconds: float,
    phase: str,
) -> dict[str, Any]:
    base_time = datetime.now(UTC)
    recorded_at = base_time.replace(microsecond=0)
    mqtt_client: Any | None = None
    mqtt_lib: Any | None = None
    if RUNTIME_CONFIG.transport == "mqtt":
        mqtt_client, mqtt_lib = _open_mqtt_client()

    try:
        payload = _emit_sensor_frame(
            base_url,
            profile=profile,
            frame=frame,
            frame_index=frame_index,
            station_code=station_code,
            recorded_at=recorded_at,
            phase=phase,
            mqtt_client=mqtt_client,
            mqtt_lib=mqtt_lib,
        )
        print(
            f"[OK] Emitted {phase} frame {frame_index} via {RUNTIME_CONFIG.transport.upper()} "
            f"salinity={_format_salinity_dual(frame.salinity_dsm)} note={frame.note or '-'}"
        )
        return payload
    finally:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


def _publish_post_execute_reading_via_mqtt(
    *,
    station_code: str,
    execution_batch_id: str,
    scenario_key: str,
) -> dict[str, Any]:
    profile = SCENARIO_SENSOR_PROFILES.get(scenario_key)
    if profile is None:
        raise SimulationError(f"Không nhận diện được scenario profile '{scenario_key}'.")

    base_frame = profile.post_planning_frame or profile.frames[-1]
    target_salinity = max(Decimal("0.20"), _to_decimal(base_frame.salinity_dsm, fallback="3.00") - Decimal("0.45"))
    target_water_level = max(Decimal("0.10"), _to_decimal(base_frame.water_level_m, fallback="1.20") - Decimal("0.03"))
    target_temperature = _to_decimal(base_frame.temperature_c, fallback="29.00") - Decimal("0.10")
    target_battery = max(Decimal("1.00"), _to_decimal(base_frame.battery_level_pct, fallback="82.00") - Decimal("0.20"))

    next_recorded_at = datetime.now(UTC).replace(microsecond=0)
    ingest_payload: dict[str, Any] = {
        "station_code": station_code,
        "recorded_at": next_recorded_at.isoformat(),
        "salinity_dsm": _format_decimal(target_salinity),
        "water_level_m": _format_decimal(target_water_level),
        "temperature_c": _format_decimal(target_temperature),
        "battery_level_pct": _format_decimal(target_battery),
        "source": "demo-post-execute-feedback",
        "context_payload": {
            "scenario": scenario_key,
            "execution_batch_id": execution_batch_id,
            "phase": "post_execute_feedback_probe",
            "note": "Published after simulated execution so backend can observe a fresh MQTT reading.",
        },
    }

    follow_up_frame = SensorFrame(
        salinity_dsm=ingest_payload["salinity_dsm"],
        water_level_m=ingest_payload["water_level_m"],
        temperature_c=ingest_payload["temperature_c"],
        battery_level_pct=ingest_payload["battery_level_pct"],
        wind_speed_mps=base_frame.wind_speed_mps,
        wind_direction_deg=base_frame.wind_direction_deg,
        flow_rate_m3s=base_frame.flow_rate_m3s,
        note="post-execute feedback probe",
    )

    payload = _build_sensor_frame_payload(
        profile=profile,
        frame=follow_up_frame,
        frame_index=len(profile.frames) + 2,
        station_code=station_code,
        recorded_at=next_recorded_at,
        phase="post_execute_feedback_probe",
    )
    payload.setdefault("context_payload", {})
    if isinstance(payload["context_payload"], dict):
        payload["context_payload"]["execution_batch_id"] = execution_batch_id
        payload["context_payload"]["transport"] = "mqtt"

    mqtt_client, mqtt_lib = _open_mqtt_client()
    try:
        _publish_sensor_reading_via_mqtt(
            mqtt_client=mqtt_client,
            mqtt_lib=mqtt_lib,
            payload=payload,
        )
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    print(
        "[OK] Đã publish reading hậu execute "
        f"station={station_code} salinity={_format_salinity_dual(payload['salinity_dsm'])}"
    )

    return {
        "state": "published",
        "execution_batch_id": execution_batch_id,
        "published_recorded_at": payload.get("recorded_at"),
        "published_salinity_dsm": payload.get("salinity_dsm"),
        "published_salinity_gl": str(dsm_to_gl(_to_decimal(payload.get("salinity_dsm"), fallback="0.00"))),
        "transport": "mqtt",
        "note": "Backend sẽ tự xử lý theo luồng ingest/MQTT hiện có; script không gọi GET hay feedback endpoint.",
    }


def _wait_new_pending_plan(
    base_url: str,
    *,
    baseline_plan_ids: set[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    def _condition() -> tuple[bool, Any]:
        plans = _list_plans(base_url, limit=100)
        for plan in plans:
            plan_id = str(plan.get("id") or "")
            status = str(plan.get("status") or "")
            if plan_id and plan_id not in baseline_plan_ids and status == "pending_approval":
                return True, plan
        return False, None

    return _poll(
        description="new pending_approval plan",
        timeout_seconds=timeout_seconds,
        interval_seconds=5.0,
        condition=_condition,
    )


def _wait_plan_status(
    base_url: str,
    *,
    plan_id: str,
    target_statuses: set[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    def _condition() -> tuple[bool, Any]:
        plan = _http_json(base_url=base_url, method="GET", path=f"/api/v1/plans/{plan_id}")
        status = str(plan.get("status") or "")
        return status in target_statuses, plan

    return _poll(
        description=f"plan {plan_id} status in {sorted(target_statuses)}",
        timeout_seconds=timeout_seconds,
        interval_seconds=5.0,
        condition=_condition,
    )


def _wait_plan_generation_run_for_goal(
    base_url: str,
    *,
    goal_name: str,
    baseline_run_ids: set[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    def _condition() -> tuple[bool, Any]:
        for run in _list_agent_runs(base_url, limit=120):
            run_id = str(run.get("id") or "")
            if not run_id or run_id in baseline_run_ids:
                continue
            if str(run.get("run_type") or "") != "plan_generation":
                continue
            payload = run.get("payload") or {}
            trigger_payload = payload.get("trigger_payload") or {}
            if str(trigger_payload.get("goal_name") or "") != goal_name:
                continue
            status = str(run.get("status") or "")
            if status == "failed":
                raise SimulationError(f"Plan generation cho goal '{goal_name}' đã thất bại.")
            if status == "succeeded":
                return True, run
        return False, None

    return _poll(
        description=f"plan_generation run for goal {goal_name}",
        timeout_seconds=timeout_seconds,
        interval_seconds=4.0,
        condition=_condition,
    )


def _prepare_plan_from_sensor_profile(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    timeout_seconds: int,
    station_code: str | None,
    frame_pause_seconds: float,
    close_open_incidents: bool,
) -> dict[str, Any]:
    del timeout_seconds, close_open_incidents
    station = str(station_code or "GOCONG-01")
    emitted_frames = _ingest_sensor_profile(
        base_url,
        profile=profile,
        station_code=station,
        frame_pause_seconds=frame_pause_seconds,
        phase="primary",
    )

    if profile.post_planning_frame is not None:
        follow_up_index = len(emitted_frames) + 1
        follow_up_pause = max(frame_pause_seconds, profile.post_planning_frame.pause_seconds, DEFAULT_FRAME_PAUSE_SECONDS)
        if follow_up_pause > 0:
            time.sleep(follow_up_pause)
        follow_up_payload = _ingest_follow_up_frame(
            base_url,
            profile=profile,
            frame=profile.post_planning_frame,
            station_code=station,
            frame_index=follow_up_index,
            frame_pause_seconds=frame_pause_seconds,
            phase="post_planning",
        )
        emitted_frames.append(follow_up_payload)

    return {
        "profile_key": profile.key,
        "goal_name": _goal_name(profile.key, station),
        "station_code": station,
        "emitted_frames": emitted_frames,
        "closed_incident_ids": [],
        "trigger_run": None,
        "plan": None,
        "plan_id": None,
        "baseline_plan_ids": set(),
    }


def run_sensor_profile(
    *,
    base_url: str,
    scenario_key: str,
    timeout_seconds: int,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    """Emit scenario-specific sensor stream without polling server state."""
    profile = SCENARIO_SENSOR_PROFILES.get(scenario_key)
    if profile is None:
        raise SimulationError(f"Không nhận diện được scenario profile '{scenario_key}'.")
    prepared = _prepare_plan_from_sensor_profile(
        base_url,
        profile=profile,
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
    )
    return {
        "scenario": scenario_key,
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "emitted_frame_count": len(prepared["emitted_frames"]),
        "closed_incident_count": 0,
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "Chế độ publish-only không thực thi plan, nên không tiêm post-execute reading."
                if inject_post_execute_reading
                else "Đã tắt tiêm post-execute reading."
            ),
        },
    }


def scenario_critical_timeout_replan(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    print("\n[SCENARIO] critical-timeout-replan")
    prepared = _prepare_plan_from_sensor_profile(
        base_url,
        profile=SCENARIO_SENSOR_PROFILES["critical-timeout-replan"],
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
    )

    return {
        "scenario": "critical-timeout-replan",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "pending_plan_id": None,
        "rejected_plan_status": None,
        "replacement_plan_id": None,
        "replacement_plan_status": None,
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "Scenario này chỉ publish sensor frames; backend worker tự xử lý timeout-replan."
                if inject_post_execute_reading
                else "Đã tắt tiêm post-execute reading."
            ),
        },
    }


def scenario_fast_approve_execute(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    print("\n[SCENARIO] fast-approve-execute")
    prepared = _prepare_plan_from_sensor_profile(
        base_url,
        profile=SCENARIO_SENSOR_PROFILES["fast-approve-execute"],
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
    )
    post_execute_feedback: dict[str, Any]
    if inject_post_execute_reading:
        feedback_frame = SCENARIO_SENSOR_PROFILES["fast-approve-execute"].post_planning_frame
        if feedback_frame is None:
            feedback_frame = SCENARIO_SENSOR_PROFILES["fast-approve-execute"].frames[-1]
        follow_up_payload = _ingest_follow_up_frame(
            base_url,
            profile=SCENARIO_SENSOR_PROFILES["fast-approve-execute"],
            frame=feedback_frame,
            station_code=prepared["station_code"],
            frame_index=len(prepared["emitted_frames"]) + 1,
            frame_pause_seconds=frame_pause_seconds,
            phase="post_execute_feedback_probe",
        )
        post_execute_feedback = {
            "state": "published",
            "transport": RUNTIME_CONFIG.transport,
            "station_code": prepared["station_code"],
            "scenario": "fast-approve-execute",
            "recorded_at": follow_up_payload.get("recorded_at"),
        }
    else:
        post_execute_feedback = {
            "state": "skipped",
            "reason": "Đã tắt tiêm post-execute reading.",
        }

    return {
        "scenario": "fast-approve-execute",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "pending_plan_id": None,
        "approved_plan_id": None,
        "execution_batch_id": None,
        "post_execute_status": None,
        "action_log_count": 0,
        "post_execute_feedback": post_execute_feedback,
    }


def scenario_rag_provenance_drilldown(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    print("\n[SCENARIO] rag-provenance-drilldown")
    prepared = _prepare_plan_from_sensor_profile(
        base_url,
        profile=SCENARIO_SENSOR_PROFILES["rag-provenance-drilldown"],
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
    )

    return {
        "scenario": "rag-provenance-drilldown",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "run_id": None,
        "plan_id": None,
        "total_evidence": 0,
        "source_counts": {},
        "top_citations": [],
        "knowledge_context_preview": [],
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "This scenario chỉ publish sensor frames; backend tự sinh trace provenance."
                if inject_post_execute_reading
                else "Đã tắt tiêm post-execute reading."
            ),
        },
    }


def scenario_warning_observe_recover(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    print("\n[SCENARIO] warning-observe-recover")
    prepared = _prepare_plan_from_sensor_profile(
        base_url,
        profile=SCENARIO_SENSOR_PROFILES["warning-observe-recover"],
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
    )

    return {
        "scenario": "warning-observe-recover",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "pending_plan_id": None,
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "Scenario này chỉ publish warning->recovery frames; backend worker tự quyết định posture."
                if inject_post_execute_reading
                else "Đã tắt tiêm post-execute reading."
            ),
        },
    }


ScenarioRunner = Callable[..., dict[str, Any]]

SCENARIO_EXECUTORS: dict[str, ScenarioRunner] = {
    "critical-timeout-replan": scenario_critical_timeout_replan,
    "fast-approve-execute": scenario_fast_approve_execute,
    "rag-provenance-drilldown": scenario_rag_provenance_drilldown,
    "warning-observe-recover": scenario_warning_observe_recover,
}


def run_named_scenario(
    *,
    base_url: str,
    scenario_key: str,
    timeout_seconds: int,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    """Dispatch one scenario with runtime options."""
    runner = SCENARIO_EXECUTORS.get(scenario_key)
    if runner is None:
        raise SimulationError(f"Không nhận diện được scenario '{scenario_key}'. Dùng --list để xem danh sách.")
    return runner(
        base_url,
        timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


SCENARIO_RUNNERS: dict[str, Callable[[str, int], dict[str, Any]]] = {
    key: (
        lambda base_url, timeout_seconds, *, _key=key: run_named_scenario(
            base_url=base_url,
            scenario_key=_key,
            timeout_seconds=timeout_seconds,
            station_code=None,
            frame_pause_seconds=DEFAULT_FRAME_PAUSE_SECONDS,
            close_open_incidents=True,
        )
    )
    for key in SCENARIO_EXECUTORS
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real API demo scenarios end-to-end.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL.",
    )
    parser.add_argument(
        "--scenario",
        default="all",
        help="Scenario key or 'all'.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenario keys.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Reserved for compatibility; publish-only mode does not poll server state.",
    )
    parser.add_argument(
        "--station-code",
        default=None,
        help="Optional station_code target for sensor stream (default: GOCONG-01).",
    )
    parser.add_argument(
        "--frame-pause-seconds",
        type=float,
        default=DEFAULT_FRAME_PAUSE_SECONDS,
        help="Default pause between sensor frames in one scenario.",
    )
    parser.add_argument(
        "--transport",
        default="http",
        choices=["http", "mqtt"],
        help="Transport for scenario sensor stream emission.",
    )
    parser.add_argument(
        "--mqtt-broker-url",
        default="localhost",
        help="MQTT broker host for --transport mqtt.",
    )
    parser.add_argument(
        "--mqtt-broker-port",
        type=int,
        default=1883,
        help="MQTT broker port for --transport mqtt.",
    )
    parser.add_argument(
        "--mqtt-topic-readings",
        default="mekong/sensors/readings",
        help="MQTT topic to publish sensor readings.",
    )
    parser.add_argument(
        "--mqtt-username",
        default=None,
        help="Optional MQTT username.",
    )
    parser.add_argument(
        "--mqtt-password",
        default=None,
        help="Optional MQTT password.",
    )
    parser.add_argument(
        "--mqtt-client-id",
        default="mekong-salt-demo-simulation",
        help="MQTT client id for the publisher.",
    )
    parser.add_argument(
        "--mqtt-qos",
        type=int,
        default=1,
        choices=[0, 1, 2],
        help="MQTT publish QoS for scenario frames.",
    )
    parser.add_argument(
        "--keep-open-incidents",
        action="store_true",
        help="Reserved for compatibility; publish-only mode does not auto-close incidents.",
    )
    parser.add_argument(
        "--no-post-execute-reading",
        action="store_true",
        help=(
            "Disable the follow-up feedback probe publish for scenarios that emit it."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print final result as JSON.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.list:
        for key in SCENARIO_EXECUTORS:
            print(key)
        return

    if args.scenario != "all" and args.scenario not in SCENARIO_EXECUTORS:
        raise SystemExit(f"Không nhận diện được scenario '{args.scenario}'. Dùng --list để xem danh sách.")

    RUNTIME_CONFIG.transport = str(args.transport)
    RUNTIME_CONFIG.mqtt_broker_url = str(args.mqtt_broker_url)
    RUNTIME_CONFIG.mqtt_broker_port = int(args.mqtt_broker_port)
    RUNTIME_CONFIG.mqtt_topic_sensor_readings = str(args.mqtt_topic_readings)
    RUNTIME_CONFIG.mqtt_username = args.mqtt_username
    RUNTIME_CONFIG.mqtt_password = args.mqtt_password
    RUNTIME_CONFIG.mqtt_client_id = str(args.mqtt_client_id)
    RUNTIME_CONFIG.mqtt_qos = int(args.mqtt_qos)

    print(f"[OK] Demo simulation configured for {args.base_url}")
    if RUNTIME_CONFIG.transport == "mqtt":
        print(
            "[OK] Sensor stream transport MQTT "
            f"{RUNTIME_CONFIG.mqtt_broker_url}:{RUNTIME_CONFIG.mqtt_broker_port} "
            f"topic={RUNTIME_CONFIG.mqtt_topic_sensor_readings} qos={RUNTIME_CONFIG.mqtt_qos}"
        )
    else:
        print("[OK] Sensor stream transport HTTP /api/v1/sensors/ingest")

    selected_keys = (
        [args.scenario]
        if args.scenario != "all"
        else list(SCENARIO_EXECUTORS.keys())
    )

    outputs: dict[str, Any] = {}
    for key in selected_keys:
        outputs[key] = run_named_scenario(
            base_url=args.base_url,
            scenario_key=key,
            timeout_seconds=int(args.timeout_seconds),
            station_code=args.station_code,
            frame_pause_seconds=float(args.frame_pause_seconds),
            close_open_incidents=not bool(args.keep_open_incidents),
            inject_post_execute_reading=not bool(args.no_post_execute_reading),
        )

    if args.json:
        print(json.dumps(outputs, ensure_ascii=True, indent=2))
        return

    print("\n=== Simulation Result ===")
    for key, value in outputs.items():
        print(f"{key}: {json.dumps(value, ensure_ascii=True)}")


if __name__ == "__main__":
    try:
        main()
    except SimulationError as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        print("[ERROR] Interrupted by user")
        raise SystemExit(130)
