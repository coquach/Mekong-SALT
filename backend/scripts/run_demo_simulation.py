"""Scenario-driven sensor simulation for triggering Mekong-SALT agentic flow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import time
from typing import Any, Callable
from urllib import error, parse, request

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


SCENARIO_SENSOR_PROFILES: dict[str, SensorScenarioProfile] = {
    "critical-timeout-replan": SensorScenarioProfile(
        key="critical-timeout-replan",
        description="Escalating salinity to critical, leave pending plan untouched for timeout auto-reject.",
        objective="Handle critical salinity escalation with mandatory HITL review.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.90", "1.48", "29.20", "84.00", note="danger baseline"),
            SensorFrame("4.45", "1.60", "29.40", "83.70", pause_seconds=0.8, note="cross critical"),
            SensorFrame("5.15", "1.72", "29.70", "83.20", pause_seconds=0.8, note="sustain critical"),
        ),
    ),
    "fast-approve-execute": SensorScenarioProfile(
        key="fast-approve-execute",
        description="High-risk readings to create pending plan, then approve and simulate execution.",
        objective="Generate an actionable high-risk plan for quick operator approval and simulation.",
        warning_threshold_dsm="2.50",
        critical_threshold_dsm="4.00",
        frames=(
            SensorFrame("3.35", "1.30", "28.90", "88.50", note="elevated warning"),
            SensorFrame("4.05", "1.42", "29.10", "88.00", pause_seconds=0.8, note="danger threshold"),
            SensorFrame("4.60", "1.55", "29.30", "87.60", pause_seconds=0.8, note="pending approval trigger"),
        ),
    ),
    "rag-provenance-drilldown": SensorScenarioProfile(
        key="rag-provenance-drilldown",
        description="Context-rich readings to trigger a fresh planning run for retrieval trace inspection.",
        objective="Create a plan that requires evidence-grounded rationale for operator briefing.",
        warning_threshold_dsm="2.30",
        critical_threshold_dsm="3.90",
        frames=(
            SensorFrame("2.60", "1.12", "28.60", "91.00", note="warning onset"),
            SensorFrame("3.20", "1.24", "28.80", "90.50", pause_seconds=0.8, note="rising trend"),
            SensorFrame("3.85", "1.36", "29.00", "90.10", pause_seconds=0.8, note="near critical"),
        ),
    ),
}

def _to_query(params: dict[str, Any]) -> str:
    encoded = parse.urlencode(
        {key: value for key, value in params.items() if value is not None},
        doseq=True,
    )
    return f"?{encoded}" if encoded else ""


def _parse_iso_datetime(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _to_decimal(raw: Any, *, fallback: str) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(fallback)


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


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
            "Backend API is not reachable. Start server first with: "
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
        raise SimulationError("No station reading found. Run seed/setup first.")

    target = items[0]
    station = target.get("station") or {}
    code = str(station.get("code") or "")
    station_id = str(station.get("id") or "")
    region_id = str(station.get("region_id") or "")
    if not code or not station_id or not region_id:
        raise SimulationError("Station payload is missing code/id/region_id.")

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


def _ingest_sensor_profile(
    base_url: str,
    *,
    profile: SensorScenarioProfile,
    station_code: str,
    frame_pause_seconds: float,
) -> list[dict[str, Any]]:
    base_time = datetime.now(UTC)
    emitted: list[dict[str, Any]] = []
    for index, frame in enumerate(profile.frames, start=1):
        recorded_at = base_time + timedelta(seconds=index)
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
                "frame_index": index,
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

        _http_json(base_url=base_url, method="POST", path="/api/v1/sensors/ingest", payload=payload)
        emitted.append(payload)
        print(
            f"[OK] Emitted frame {index}/{len(profile.frames)} "
            f"salinity={frame.salinity_dsm} dS/m note={frame.note or '-'}"
        )

        pause = max(frame_pause_seconds, frame.pause_seconds)
        if index < len(profile.frames) and pause > 0:
            time.sleep(pause)

    return emitted


def _inject_post_execute_reading_and_evaluate_feedback(
    base_url: str,
    *,
    station_code: str,
    execution_batch_id: str,
    scenario_key: str,
) -> dict[str, Any]:
    payload = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/readings/latest{_to_query({'station_code': station_code, 'limit': 1})}",
    )
    items = list((payload or {}).get("items") or [])
    if not items:
        raise SimulationError(
            f"Cannot inject post-execute reading: no latest reading for station '{station_code}'."
        )

    latest = items[0]
    latest_recorded_at = _parse_iso_datetime(latest.get("recorded_at"))
    next_recorded_at = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=2)
    if latest_recorded_at is not None and next_recorded_at <= latest_recorded_at:
        next_recorded_at = latest_recorded_at + timedelta(seconds=2)

    latest_salinity = _to_decimal(latest.get("salinity_dsm"), fallback="3.00")
    target_salinity = max(Decimal("0.20"), latest_salinity - Decimal("0.45"))

    latest_water_level = _to_decimal(latest.get("water_level_m"), fallback="1.20")
    target_water_level = max(Decimal("0.10"), latest_water_level - Decimal("0.03"))

    latest_temperature = _to_decimal(latest.get("temperature_c"), fallback="29.00")
    target_temperature = latest_temperature - Decimal("0.10")

    latest_battery = _to_decimal(latest.get("battery_level_pct"), fallback="82.00")
    target_battery = max(Decimal("1.00"), latest_battery - Decimal("0.20"))

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
            "phase": "post_execute_feedback_probe",
            "note": "Injected after simulated execution to make feedback evaluate comparable latest reading.",
        },
    }

    if latest.get("wind_speed_mps") is not None:
        ingest_payload["wind_speed_mps"] = latest.get("wind_speed_mps")
    if latest.get("wind_direction_deg") is not None:
        ingest_payload["wind_direction_deg"] = latest.get("wind_direction_deg")
    if latest.get("flow_rate_m3s") is not None:
        ingest_payload["flow_rate_m3s"] = latest.get("flow_rate_m3s")

    ingested = _http_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/sensors/ingest",
        payload=ingest_payload,
    )
    print(
        "[OK] Injected post-execute reading "
        f"station={station_code} salinity={ingest_payload['salinity_dsm']} dS/m"
    )

    evaluated = _http_json(
        base_url=base_url,
        method="POST",
        path=f"/api/v1/feedback/execution-batches/{execution_batch_id}/evaluate",
    )
    feedback = evaluated.get("feedback") or {}
    print(
        "[OK] Evaluated feedback "
        f"batch={execution_batch_id} outcome={feedback.get('outcome_class')} "
        f"status={feedback.get('status')}"
    )

    latest_feedback = _http_json(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/feedback/execution-batches/{execution_batch_id}/latest",
    )

    return {
        "state": "evaluated",
        "execution_batch_id": execution_batch_id,
        "ingested_reading_id": ingested.get("id"),
        "ingested_recorded_at": ingested.get("recorded_at"),
        "ingested_salinity_dsm": ingested.get("salinity_dsm"),
        "feedback_outcome_class": feedback.get("outcome_class"),
        "feedback_status": feedback.get("status"),
        "feedback_summary": feedback.get("summary"),
        "replan_recommended": feedback.get("replan_recommended"),
        "evaluation_id": (evaluated.get("evaluation") or {}).get("id"),
        "latest_evaluation_id": (latest_feedback.get("evaluation") or {}).get("id"),
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
                raise SimulationError(f"Plan generation run failed for goal '{goal_name}'.")
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
    station_scope = _resolve_station_scope(base_url, station_code=station_code)
    goal = _ensure_monitoring_goal(base_url, profile=profile, station_scope=station_scope)
    goal_name = str(goal.get("name") or _goal_name(profile.key, station_scope["station_code"]))

    closed_incident_ids: list[str] = []
    if close_open_incidents:
        closed_incident_ids = _close_open_incidents(
            base_url,
            region_id=station_scope["region_id"],
        )

    baseline_plan_ids = {
        str(item.get("id"))
        for item in _list_plans(base_url, limit=120)
        if item.get("id")
    }
    baseline_run_ids = {
        str(item.get("id"))
        for item in _list_agent_runs(base_url, limit=120)
        if item.get("id")
    }

    emitted_frames = _ingest_sensor_profile(
        base_url,
        profile=profile,
        station_code=station_scope["station_code"],
        frame_pause_seconds=frame_pause_seconds,
    )

    run = _wait_plan_generation_run_for_goal(
        base_url,
        goal_name=goal_name,
        baseline_run_ids=baseline_run_ids,
        timeout_seconds=timeout_seconds,
    )

    action_plan_id = str(run.get("action_plan_id") or "")
    if action_plan_id:
        plan = _http_json(base_url=base_url, method="GET", path=f"/api/v1/plans/{action_plan_id}")
    else:
        plan = _wait_new_pending_plan(
            base_url,
            baseline_plan_ids=baseline_plan_ids,
            timeout_seconds=timeout_seconds,
        )
        action_plan_id = str(plan.get("id") or "")

    if not action_plan_id:
        raise SimulationError("Plan generation run completed but did not expose an action plan id.")

    return {
        "profile_key": profile.key,
        "goal_id": goal.get("id"),
        "goal_name": goal_name,
        "station_code": station_scope["station_code"],
        "station_id": station_scope["station_id"],
        "region_id": station_scope["region_id"],
        "closed_incident_ids": closed_incident_ids,
        "emitted_frames": emitted_frames,
        "trigger_run": run,
        "plan": plan,
        "plan_id": action_plan_id,
        "baseline_plan_ids": baseline_plan_ids,
    }


def run_sensor_profile(
    *,
    base_url: str,
    scenario_key: str,
    timeout_seconds: int,
    station_code: str | None = None,
    frame_pause_seconds: float = 1.2,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    """Emit scenario-specific sensor stream and wait until plan generation is triggered."""
    profile = SCENARIO_SENSOR_PROFILES.get(scenario_key)
    if profile is None:
        raise SimulationError(f"Unknown scenario profile '{scenario_key}'.")
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
        "goal_id": prepared["goal_id"],
        "goal_name": prepared["goal_name"],
        "plan_id": prepared["plan_id"],
        "plan_status": str((prepared["plan"] or {}).get("status") or ""),
        "trigger_run_id": prepared["trigger_run"].get("id"),
        "trigger_run_status": prepared["trigger_run"].get("status"),
        "emitted_frame_count": len(prepared["emitted_frames"]),
        "closed_incident_count": len(prepared["closed_incident_ids"]),
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "Sensor-profile mode does not execute plans, so no post-execute reading is injected."
                if inject_post_execute_reading
                else "Post-execute reading injection is disabled."
            ),
        },
    }


def scenario_critical_timeout_replan(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = 1.2,
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
    pending_id = str(prepared["plan_id"])

    _wait_plan_status(
        base_url,
        plan_id=pending_id,
        target_statuses={"pending_approval", "rejected"},
        timeout_seconds=max(timeout_seconds, 90),
    )
    rejected = _wait_plan_status(
        base_url,
        plan_id=pending_id,
        target_statuses={"rejected"},
        timeout_seconds=max(timeout_seconds, 120),
    )
    newer_pending = _wait_new_pending_plan(
        base_url,
        baseline_plan_ids=prepared["baseline_plan_ids"] | {pending_id},
        timeout_seconds=timeout_seconds,
    )

    return {
        "scenario": "critical-timeout-replan",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "pending_plan_id": pending_id,
        "rejected_plan_status": rejected.get("status"),
        "replacement_plan_id": newer_pending.get("id"),
        "replacement_plan_status": newer_pending.get("status"),
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "This scenario keeps plans pending/rejected for timeout-replan behavior and does not execute."
                if inject_post_execute_reading
                else "Post-execute reading injection is disabled."
            ),
        },
    }


def scenario_fast_approve_execute(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = 1.2,
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

    plan_id = str(prepared["plan_id"])
    pending_plan = _wait_plan_status(
        base_url,
        plan_id=plan_id,
        target_statuses={"pending_approval"},
        timeout_seconds=timeout_seconds,
    )

    _http_json(
        base_url=base_url,
        method="POST",
        path=f"/api/v1/approvals/plans/{plan_id}/decision?actor_name=demo-operator",
        payload={"decision": "approved", "comment": "demo fast approval after sensor stream"},
    )
    print(f"[OK] Approved plan {plan_id}")

    simulated = _http_json(
        base_url=base_url,
        method="POST",
        path=f"/api/v1/execution-batches/plans/{plan_id}/simulate",
        payload={"idempotency_key": f"demo-fast-approve-execute:{plan_id}"},
    )
    batch = simulated.get("batch") or {}
    batch_id = batch.get("id")
    print(f"[OK] Simulated execution batch created for plan {plan_id}")

    post_execute = _wait_plan_status(
        base_url,
        plan_id=plan_id,
        target_statuses={"simulated", "closed"},
        timeout_seconds=timeout_seconds,
    )

    def _has_action_logs() -> tuple[bool, Any]:
        logs = _http_json(
            base_url=base_url,
            method="GET",
            path=f"/api/v1/actions/logs{_to_query({'plan_id': plan_id, 'limit': 20})}",
        )
        count = int((logs or {}).get("count") or 0)
        return count > 0, logs

    logs = _poll(
        description=f"execution logs for plan {plan_id}",
        timeout_seconds=timeout_seconds,
        interval_seconds=4.0,
        condition=_has_action_logs,
    )

    post_execute_feedback: dict[str, Any]
    if inject_post_execute_reading:
        if batch_id is None:
            post_execute_feedback = {
                "state": "skipped",
                "reason": "Execution completed without batch_id; feedback probe not triggered.",
            }
        else:
            post_execute_feedback = _inject_post_execute_reading_and_evaluate_feedback(
                base_url,
                station_code=prepared["station_code"],
                execution_batch_id=str(batch_id),
                scenario_key="fast-approve-execute",
            )
    else:
        post_execute_feedback = {
            "state": "skipped",
            "reason": "Post-execute reading injection is disabled.",
        }

    return {
        "scenario": "fast-approve-execute",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "pending_plan_id": pending_plan.get("id"),
        "approved_plan_id": plan_id,
        "execution_batch_id": batch_id,
        "post_execute_status": post_execute.get("status"),
        "action_log_count": int((logs or {}).get("count") or 0),
        "post_execute_feedback": post_execute_feedback,
    }


def scenario_rag_provenance_drilldown(
    base_url: str,
    timeout_seconds: int,
    *,
    station_code: str | None = None,
    frame_pause_seconds: float = 1.2,
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

    run_id = str(prepared["trigger_run"].get("id") or "")
    if not run_id:
        raise SimulationError("Unable to resolve trigger run id for RAG drilldown.")

    run_detail = _http_json(base_url=base_url, method="GET", path=f"/api/v1/agent/runs/{run_id}")
    trace = run_detail.get("trace") or {}
    retrieval_trace = trace.get("retrieval_trace") or {}
    snapshot = run_detail.get("observation_snapshot") or {}
    snapshot_payload = snapshot.get("payload") or {}
    preview = list(snapshot_payload.get("knowledge_context_preview") or [])
    top_citations = list(retrieval_trace.get("top_citations") or [])
    source_counts = retrieval_trace.get("source_counts") or {}
    total_evidence = retrieval_trace.get("total_evidence")
    if total_evidence is None:
        total_evidence = len(preview)

    return {
        "scenario": "rag-provenance-drilldown",
        "station_code": prepared["station_code"],
        "goal_name": prepared["goal_name"],
        "run_id": run_id,
        "plan_id": prepared["plan_id"],
        "total_evidence": int(total_evidence),
        "source_counts": source_counts,
        "top_citations": top_citations,
        "knowledge_context_preview": preview,
        "post_execute_feedback": {
            "state": "skipped",
            "reason": (
                "This scenario focuses on planning provenance and does not execute the plan."
                if inject_post_execute_reading
                else "Post-execute reading injection is disabled."
            ),
        },
    }


ScenarioRunner = Callable[..., dict[str, Any]]

SCENARIO_EXECUTORS: dict[str, ScenarioRunner] = {
    "critical-timeout-replan": scenario_critical_timeout_replan,
    "fast-approve-execute": scenario_fast_approve_execute,
    "rag-provenance-drilldown": scenario_rag_provenance_drilldown,
}


def run_named_scenario(
    *,
    base_url: str,
    scenario_key: str,
    timeout_seconds: int,
    station_code: str | None = None,
    frame_pause_seconds: float = 1.2,
    close_open_incidents: bool = True,
    inject_post_execute_reading: bool = True,
) -> dict[str, Any]:
    """Dispatch one scenario with runtime options."""
    runner = SCENARIO_EXECUTORS.get(scenario_key)
    if runner is None:
        raise SimulationError(f"Unknown scenario '{scenario_key}'. Use --list.")
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
            frame_pause_seconds=1.2,
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
        default=220,
        help="Polling timeout per major wait step.",
    )
    parser.add_argument(
        "--station-code",
        default=None,
        help="Optional station_code target for sensor stream (default: auto-select latest station).",
    )
    parser.add_argument(
        "--frame-pause-seconds",
        type=float,
        default=1.2,
        help="Default pause between sensor frames in one scenario.",
    )
    parser.add_argument(
        "--keep-open-incidents",
        action="store_true",
        help="Do not auto-close open incidents before sending scenario frames.",
    )
    parser.add_argument(
        "--no-post-execute-reading",
        action="store_true",
        help=(
            "Disable automatic post-execution reading injection + feedback evaluation "
            "for scenarios that execute plans."
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
        raise SystemExit(f"Unknown scenario '{args.scenario}'. Use --list.")

    _ensure_server_ready(args.base_url)
    print(f"[OK] Backend API reachable at {args.base_url}")

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
