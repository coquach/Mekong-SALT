"""MQTT-only demo sensor publisher for Mekong-SALT."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import time
from pathlib import Path
import sys
from typing import Any, Callable
from urllib import error, request

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

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
    """Scenario settings used to drive a publish-only MQTT demo stream."""

    key: str
    description: str
    objective: str
    warning_threshold_dsm: str
    critical_threshold_dsm: str
    frames: tuple[SensorFrame, ...]
    post_planning_frame: SensorFrame | None = None


@dataclass(slots=True)
class SimulationRuntimeConfig:
    """Transport configuration for sensor emission."""

    ingest_mode: str = "auto"
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
        description="Push salinity through danger into critical while keeping a fresh stream window.",
        objective="Escalate salinity to a critical band with a longer trend window.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.90", "1.48", "29.20", "84.00", note="initial high risk"),
            SensorFrame("4.15", "1.54", "29.28", "83.85", note="crossing danger"),
            SensorFrame("4.45", "1.60", "29.40", "83.70", note="critical threshold exceeded"),
            SensorFrame("5.15", "1.72", "29.70", "83.20", note="critical state sustained"),
        ),
        post_planning_frame=SensorFrame(
            "1.80",
            "1.60",
            "29.60",
            "82.90",
            note="sharp salinity drop after simulated gate closure, entering warning band",
            pause_seconds=60.0,
        ),
    ),
    "fast-approve-execute": SensorScenarioProfile(
        key="fast-approve-execute",
        description="Start from normal salinity, move through warning, then stop at critical review point.",
        objective="Create a reviewable plan candidate from a rising salinity stream.",
        warning_threshold_dsm="1.80",
        critical_threshold_dsm="3.20",
        frames=(
            SensorFrame("0.84", "1.20", "28.82", "89.20", note="normal baseline"),
            SensorFrame("1.26", "1.24", "28.92", "89.00", note="approaching warning"),
            SensorFrame("2.04", "1.31", "29.02", "88.70", note="warning band trend"),
            SensorFrame("3.38", "1.44", "29.16", "88.30", note="critical review point"),
        ),
        post_planning_frame=SensorFrame(
            "2.68",
            "1.36",
            "29.08",
            "88.05",
            note="post-plan follow-up pulse",
            pause_seconds=60.0,
        ),
    ),
    "rag-provenance-drilldown": SensorScenarioProfile(
        key="rag-provenance-drilldown",
        description="Use richer context to exercise retrieval and trace visibility.",
        objective="Trigger a plan candidate that should surface citations and evidence.",
        warning_threshold_dsm="2.30",
        critical_threshold_dsm="3.90",
        frames=(
            SensorFrame("2.60", "1.12", "28.60", "91.00", note="warning onset"),
            SensorFrame("2.95", "1.18", "28.72", "90.80", note="extra trend window"),
            SensorFrame("3.20", "1.24", "28.80", "90.50", note="rising trend"),
            SensorFrame("3.85", "1.36", "29.00", "90.10", note="near critical"),
        ),
        post_planning_frame=SensorFrame(
            "3.92",
            "1.38",
            "29.04",
            "89.85",
            note="trace-preserving follow-up",
            pause_seconds=60.0,
        ),
    ),
    "warning-observe-recover": SensorScenarioProfile(
        key="warning-observe-recover",
        description="Hold a warning band stream, then drift back into a recovery window.",
        objective="Show a cautious warning posture that later recovers below threshold.",
        warning_threshold_dsm="1.80",
        critical_threshold_dsm="3.20",
        frames=(
            SensorFrame("1.92", "1.16", "28.70", "92.20", wind_speed_mps="5.20", wind_direction_deg=135, note="initial warning"),
            SensorFrame("2.10", "1.17", "28.78", "92.00", wind_speed_mps="5.60", wind_direction_deg=132, note="holding warning"),
            SensorFrame("2.18", "1.18", "28.82", "91.90", wind_speed_mps="5.80", wind_direction_deg=130, note="trend still rising"),
            SensorFrame("2.05", "1.15", "28.76", "91.70", wind_speed_mps="5.10", wind_direction_deg=145, note="still in warning"),
        ),
        post_planning_frame=SensorFrame(
            "0.92",
            "1.12",
            "28.60",
            "91.50",
            wind_speed_mps="4.30",
            wind_direction_deg=160,
            note="recovery window",
            pause_seconds=60.0,
        ),
    ),
    "salinity-falling-open-gate": SensorScenarioProfile(
        key="salinity-falling-open-gate",
        description="Start in the danger band, then trend downward while staying planable for a gate-open recovery.",
        objective="Show a falling salinity window that should lead to an open-gate recovery plan.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.72", "1.28", "28.90", "90.10", wind_speed_mps="3.40", wind_direction_deg=148, note="danger baseline"),
            SensorFrame("3.36", "1.26", "28.84", "89.90", wind_speed_mps="3.20", wind_direction_deg=150, note="falling but still danger"),
            SensorFrame("3.02", "1.23", "28.78", "89.70", wind_speed_mps="3.00", wind_direction_deg=152, note="recovery trend continues"),
            SensorFrame("2.70", "1.20", "28.72", "89.50", wind_speed_mps="2.80", wind_direction_deg=155, note="near reopening window"),
        ),
        post_planning_frame=SensorFrame(
            "2.58",
            "1.18",
            "28.68",
            "89.30",
            wind_speed_mps="2.60",
            wind_direction_deg=160,
            note="follow-up recovery pulse",
            pause_seconds=60.0,
        ),
    ),
}

RUNTIME_CONFIG = SimulationRuntimeConfig()

DEFAULT_FRAME_PAUSE_SECONDS = 10.0
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_STATION_CODE = "GOCONG-01"


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
    """Small JSON helper kept for Gradio live-monitor reads."""

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


def _open_mqtt_client() -> tuple[Any, Any]:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:  # pragma: no cover - environment dependency
        raise SimulationError("Missing dependency 'paho-mqtt'. Install backend dependencies first.") from exc

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=RUNTIME_CONFIG.mqtt_client_id,
        protocol=mqtt.MQTTv311,
    )
    if RUNTIME_CONFIG.mqtt_username:
        client.username_pw_set(RUNTIME_CONFIG.mqtt_username, RUNTIME_CONFIG.mqtt_password)

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


def _publish_sensor_reading_via_http(
    *,
    base_url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Persist one sensor reading through the canonical HTTP ingest endpoint."""
    return _http_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/sensors/ingest",
        payload=payload,
        timeout=30,
    )


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
            "objective": profile.objective,
        },
    }
    if frame.wind_speed_mps is not None:
        payload["wind_speed_mps"] = frame.wind_speed_mps
    if frame.wind_direction_deg is not None:
        payload["wind_direction_deg"] = frame.wind_direction_deg
    if frame.flow_rate_m3s is not None:
        payload["flow_rate_m3s"] = frame.flow_rate_m3s
    return payload


def _emit_sensor_frame(
    *,
    profile: SensorScenarioProfile,
    frame: SensorFrame,
    frame_index: int,
    station_code: str,
    recorded_at: datetime,
    phase: str,
    base_url: str,
    ingest_mode: str,
    mqtt_client: Any,
    mqtt_lib: Any,
) -> dict[str, Any]:
    payload = _build_sensor_frame_payload(
        profile=profile,
        frame=frame,
        frame_index=frame_index,
        station_code=station_code,
        recorded_at=recorded_at,
        phase=phase,
    )

    http_succeeded = False
    if ingest_mode in {"http", "auto", "both"}:
        try:
            _publish_sensor_reading_via_http(base_url=base_url, payload=payload)
            http_succeeded = True
        except SimulationError as exc:
            if ingest_mode == "http":
                raise
            print(f"[WARN] HTTP ingest fallback failed for frame {frame_index}: {exc}")

    if ingest_mode == "auto" and http_succeeded:
        return payload

    if ingest_mode in {"mqtt", "both"} and mqtt_client is not None and mqtt_lib is not None:
        _publish_sensor_reading_via_mqtt(mqtt_client=mqtt_client, mqtt_lib=mqtt_lib, payload=payload)
    elif ingest_mode == "auto" and not http_succeeded:
        fallback_client, fallback_mqtt_lib = _open_mqtt_client()
        try:
            _publish_sensor_reading_via_mqtt(
                mqtt_client=fallback_client,
                mqtt_lib=fallback_mqtt_lib,
                payload=payload,
            )
        finally:
            fallback_client.loop_stop()
            fallback_client.disconnect()

    return payload


def _emit_profile_via_mqtt(
    *,
    base_url: str,
    profile: SensorScenarioProfile,
    station_code: str,
    frame_pause_seconds: float,
    inject_post_execute_reading: bool,
    ingest_mode: str,
) -> list[dict[str, Any]]:
    base_time = datetime.now(UTC)
    emitted: list[dict[str, Any]] = []
    mqtt_client: Any | None = None
    mqtt_lib: Any | None = None
    if ingest_mode in {"mqtt", "both"}:
        mqtt_client, mqtt_lib = _open_mqtt_client()

    try:
        elapsed_seconds = 0.0
        for index, frame in enumerate(profile.frames, start=1):
            recorded_at = base_time + timedelta(seconds=elapsed_seconds)
            payload = _emit_sensor_frame(
                profile=profile,
                frame=frame,
                frame_index=index,
                station_code=station_code,
                recorded_at=recorded_at,
                phase="primary",
                base_url=base_url,
                ingest_mode=ingest_mode,
                mqtt_client=mqtt_client,
                mqtt_lib=mqtt_lib,
            )
            emitted.append(payload)
            print(
                f"[OK] Emitted frame {index}/{len(profile.frames)} via MQTT "
                f"salinity={_format_salinity_dual(frame.salinity_dsm)} note={frame.note or '-'}"
            )

            pause = max(float(frame_pause_seconds), float(frame.pause_seconds), 0.0)
            if index < len(profile.frames) and pause > 0:
                time.sleep(pause)
                elapsed_seconds += pause

        if inject_post_execute_reading and profile.post_planning_frame is not None:
            pause = max(float(frame_pause_seconds), float(profile.post_planning_frame.pause_seconds), 0.0)
            if pause > 0:
                time.sleep(pause)
                elapsed_seconds += pause
            recorded_at = base_time + timedelta(seconds=elapsed_seconds)
            payload = _emit_sensor_frame(
                profile=profile,
                frame=profile.post_planning_frame,
                frame_index=len(profile.frames) + 1,
                station_code=station_code,
                recorded_at=recorded_at,
                phase="post_planning",
                base_url=base_url,
                ingest_mode=ingest_mode,
                mqtt_client=mqtt_client,
                mqtt_lib=mqtt_lib,
            )
            emitted.append(payload)
            print(
                f"[OK] Emitted follow-up frame via MQTT "
                f"salinity={_format_salinity_dual(profile.post_planning_frame.salinity_dsm)} "
                f"note={profile.post_planning_frame.note or '-'}"
            )
    finally:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

    return emitted


def _stream_name(profile_key: str, station_code: str) -> str:
    return f"demo-sensor-{profile_key}-{station_code}".lower()


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
    """Publish a scenario-specific sensor stream through HTTP and/or MQTT."""

    del timeout_seconds, close_open_incidents

    profile = SCENARIO_SENSOR_PROFILES.get(scenario_key)
    if profile is None:
        raise SimulationError(f"Unknown scenario profile '{scenario_key}'.")

    station = str(station_code or DEFAULT_STATION_CODE)
    emitted_frames = _emit_profile_via_mqtt(
        base_url=base_url,
        profile=profile,
        station_code=station,
        frame_pause_seconds=frame_pause_seconds,
        inject_post_execute_reading=inject_post_execute_reading,
        ingest_mode=RUNTIME_CONFIG.ingest_mode,
    )
    stream_name = _stream_name(profile.key, station)

    return {
        "scenario": scenario_key,
        "stream_name": stream_name,
        "goal_name": stream_name,
        "station_code": station,
        "transport": (
            "http"
            if RUNTIME_CONFIG.ingest_mode == "http"
            else "mqtt"
            if RUNTIME_CONFIG.ingest_mode == "mqtt"
            else "hybrid"
        ),
        "ingest_mode": RUNTIME_CONFIG.ingest_mode,
        "mqtt_topic": RUNTIME_CONFIG.mqtt_topic_sensor_readings,
        "emitted_frame_count": len(emitted_frames),
        "emitted_frames": [
            {
                "frame_index": index,
                "recorded_at": frame.get("recorded_at"),
                "salinity_dsm": frame.get("salinity_dsm"),
                "water_level_m": frame.get("water_level_m"),
                "temperature_c": frame.get("temperature_c"),
                "battery_level_pct": frame.get("battery_level_pct"),
                "note": (frame.get("context_payload") or {}).get("frame_note", ""),
            }
            for index, frame in enumerate(emitted_frames, start=1)
        ],
        "closed_incident_count": 0,
        "post_execute_feedback": {
            "state": "skipped",
            "reason": "MQTT-only demo mode does not call backend plan or feedback endpoints.",
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
    return run_sensor_profile(
        base_url=base_url,
        scenario_key="critical-timeout-replan",
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


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
    return run_sensor_profile(
        base_url=base_url,
        scenario_key="fast-approve-execute",
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


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
    return run_sensor_profile(
        base_url=base_url,
        scenario_key="rag-provenance-drilldown",
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


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
    return run_sensor_profile(
        base_url=base_url,
        scenario_key="warning-observe-recover",
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


def scenario_salinity_falling_open_gate(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = DEFAULT_FRAME_PAUSE_SECONDS,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    print("\n[SCENARIO] salinity-falling-open-gate")
    return run_sensor_profile(
        base_url=base_url,
        scenario_key="salinity-falling-open-gate",
        timeout_seconds=timeout_seconds,
        station_code=station_code,
        frame_pause_seconds=frame_pause_seconds,
        close_open_incidents=close_open_incidents,
        inject_post_execute_reading=inject_post_execute_reading,
    )


ScenarioRunner = Callable[..., dict[str, Any]]

SCENARIO_EXECUTORS: dict[str, ScenarioRunner] = {
    "critical-timeout-replan": scenario_critical_timeout_replan,
    "fast-approve-execute": scenario_fast_approve_execute,
    "rag-provenance-drilldown": scenario_rag_provenance_drilldown,
    "warning-observe-recover": scenario_warning_observe_recover,
    "salinity-falling-open-gate": scenario_salinity_falling_open_gate,
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
        raise SimulationError(f"Unknown scenario '{scenario_key}'. Use --list to see available keys.")
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
    parser = argparse.ArgumentParser(description="Publish Mekong-SALT demo sensor streams over MQTT.")
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
        help="Kept for compatibility; MQTT-only mode does not poll server state.",
    )
    parser.add_argument(
        "--station-code",
        default=None,
        help=f"Optional station_code target for the sensor stream (default: {DEFAULT_STATION_CODE}).",
    )
    parser.add_argument(
        "--frame-pause-seconds",
        type=float,
        default=DEFAULT_FRAME_PAUSE_SECONDS,
        help="Default pause between sensor frames in one scenario.",
    )
    parser.add_argument(
        "--mqtt-broker-url",
        default="localhost",
        help="MQTT broker host.",
    )
    parser.add_argument(
        "--mqtt-broker-port",
        type=int,
        default=1883,
        help="MQTT broker port.",
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
        "--ingest-mode",
        default="auto",
        choices=["auto", "mqtt", "http", "both"],
        help="Choose transport for sensor frames: auto tries HTTP first, then MQTT.",
    )
    parser.add_argument(
        "--no-post-execute-reading",
        action="store_true",
        help="Disable the follow-up MQTT frame for scenarios that define one.",
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
        raise SystemExit(f"Unknown scenario '{args.scenario}'. Use --list to see available keys.")

    RUNTIME_CONFIG.mqtt_broker_url = str(args.mqtt_broker_url)
    RUNTIME_CONFIG.mqtt_broker_port = int(args.mqtt_broker_port)
    RUNTIME_CONFIG.mqtt_topic_sensor_readings = str(args.mqtt_topic_readings)
    RUNTIME_CONFIG.mqtt_username = args.mqtt_username
    RUNTIME_CONFIG.mqtt_password = args.mqtt_password
    RUNTIME_CONFIG.mqtt_client_id = str(args.mqtt_client_id)
    RUNTIME_CONFIG.mqtt_qos = int(args.mqtt_qos)
    RUNTIME_CONFIG.ingest_mode = str(args.ingest_mode)

    print(
        "[OK] MQTT demo configured "
        f"broker={RUNTIME_CONFIG.mqtt_broker_url}:{RUNTIME_CONFIG.mqtt_broker_port} "
        f"topic={RUNTIME_CONFIG.mqtt_topic_sensor_readings} qos={RUNTIME_CONFIG.mqtt_qos} "
        f"ingest_mode={RUNTIME_CONFIG.ingest_mode}"
    )

    selected_keys = [args.scenario] if args.scenario != "all" else list(SCENARIO_EXECUTORS.keys())

    outputs: dict[str, Any] = {}
    for key in selected_keys:
        outputs[key] = run_named_scenario(
            base_url="http://localhost:8000",
            scenario_key=key,
            timeout_seconds=int(args.timeout_seconds),
            station_code=args.station_code,
            frame_pause_seconds=float(args.frame_pause_seconds),
            close_open_incidents=True,
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
