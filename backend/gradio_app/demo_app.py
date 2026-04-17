"""Gradio demo control center for Mekong-SALT backend scenarios."""

from __future__ import annotations

import io
import json
import logging
from contextlib import redirect_stdout
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys
from typing import Any

for _logger_name in (
    "google_genai",
    "google_genai.models",
    "google.genai",
    "google.genai.models",
):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

try:
    import gradio as gr
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Gradio is not installed. Install with: ./.venv/Scripts/python.exe -m pip install gradio"
    ) from exc


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BACKEND_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_demo_simulation import (  # noqa: E402
    SCENARIO_SENSOR_PROFILES,
    SimulationError,
    _http_json,
    run_named_scenario,
    run_sensor_profile,
)


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2)


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
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


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _as_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _format_seconds(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}s"


def _build_live_monitor(
    base_url: str,
    window_minutes: int,
    max_rows: int,
) -> tuple[str, list[list[str]], str]:
    now_utc = datetime.now(UTC)
    window_minutes = max(5, min(int(window_minutes), 1440))
    max_rows = max(20, min(int(max_rows), 500))
    window_start = now_utc - timedelta(minutes=window_minutes)

    summary = _http_json(base_url=base_url, method="GET", path="/api/v1/dashboard/summary")
    goals = _as_items(
        _http_json(
            base_url=base_url,
            method="GET",
            path="/api/v1/goals?limit=500&is_active=true",
        )
    )
    runs = _as_items(_http_json(base_url=base_url, method="GET", path="/api/v1/agent/runs?limit=120"))
    readings = _as_items(
        _http_json(base_url=base_url, method="GET", path="/api/v1/readings/history?limit=160")
    )
    risk_timeline = _as_items(_http_json(base_url=base_url, method="GET", path="/api/v1/dashboard/timeline"))
    incidents = _as_items(_http_json(base_url=base_url, method="GET", path="/api/v1/incidents?limit=120"))
    plans = _as_items(_http_json(base_url=base_url, method="GET", path="/api/v1/plans?limit=120"))
    execution_batches = _as_items(
        _http_json(base_url=base_url, method="GET", path="/api/v1/execution-batches?limit=120")
    )

    run_success = 0
    run_failed = 0
    run_durations: list[float] = []
    for run in runs:
        status = str(run.get("status") or "")
        if status == "succeeded":
            run_success += 1
        elif status == "failed":
            run_failed += 1

        started = _parse_dt(run.get("started_at"))
        finished = _parse_dt(run.get("finished_at"))
        if started is not None and finished is not None and finished >= started:
            run_durations.append((finished - started).total_seconds())

    run_count = len(runs)
    run_success_rate = (run_success / run_count * 100.0) if run_count else 0.0
    run_avg_duration = (sum(run_durations) / len(run_durations)) if run_durations else None

    active_goals = len(goals)
    dedup_skips = sum(1 for goal in goals if str(goal.get("last_run_status") or "") == "skipped_no_new_reading")

    readings_in_window = 0
    plans_in_window = 0
    risks_in_window = 0
    batches_in_window = 0

    latest_reading_dt: datetime | None = None
    for reading in readings:
        reading_dt = _parse_dt(reading.get("recorded_at"))
        if reading_dt is not None:
            if latest_reading_dt is None or reading_dt > latest_reading_dt:
                latest_reading_dt = reading_dt
            if reading_dt >= window_start:
                readings_in_window += 1

    latest_risk_dt: datetime | None = None
    for item in risk_timeline:
        risk_dt = _parse_dt(item.get("assessed_at"))
        if risk_dt is not None:
            if latest_risk_dt is None or risk_dt > latest_risk_dt:
                latest_risk_dt = risk_dt
            if risk_dt >= window_start:
                risks_in_window += 1

    for plan in plans:
        created_at = _parse_dt(plan.get("created_at"))
        if created_at is not None and created_at >= window_start:
            plans_in_window += 1

    for batch in execution_batches:
        batch_time = (
            _parse_dt(batch.get("completed_at"))
            or _parse_dt(batch.get("started_at"))
            or _parse_dt(batch.get("created_at"))
        )
        if batch_time is not None and batch_time >= window_start:
            batches_in_window += 1

    observe_to_risk_lag = None
    if latest_reading_dt is not None and latest_risk_dt is not None:
        observe_to_risk_lag = (latest_risk_dt - latest_reading_dt).total_seconds()

    kpi_md = (
        "### Live Flow Health\n"
        f"- Refreshed at: {_fmt_dt(now_utc)}\n"
        f"- Window: last {window_minutes} minute(s)\n"
        f"- Open incidents: {summary.get('open_incidents', 0)} | Pending approvals: {summary.get('pending_approvals', 0)}\n"
        f"- Latest risk: {summary.get('latest_risk_level') or '-'} | Station: {summary.get('latest_station_code') or '-'} | Salinity: {summary.get('latest_salinity_dsm') or '-'}\n"
        f"- Active goals: {active_goals} | Dedup skips (`skipped_no_new_reading`): {dedup_skips}\n"
        f"- Agent runs (recent 120): {run_count} | success={run_success}, failed={run_failed}, success_rate={run_success_rate:.1f}% | avg_duration={_format_seconds(run_avg_duration)}\n"
        f"- Throughput in window: readings={readings_in_window}, risk_assessments={risks_in_window}, new_plans={plans_in_window}, execution_batches={batches_in_window}\n"
        f"- Approx observe->risk lag: {_format_seconds(observe_to_risk_lag)}"
    )

    events: list[tuple[datetime, list[str]]] = []

    for reading in readings:
        event_dt = _parse_dt(reading.get("recorded_at"))
        if event_dt is None or event_dt < window_start:
            continue
        station = str(((reading.get("station") or {}).get("code")) or "-")
        detail = (
            f"station={station}, salinity={reading.get('salinity_dsm')}, "
            f"water={reading.get('water_level_m')}, source={reading.get('source') or '-'}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "sensor",
                    "ingested",
                    str(reading.get("id") or "-"),
                    detail,
                ],
            )
        )

    for risk in risk_timeline:
        event_dt = _parse_dt(risk.get("assessed_at"))
        if event_dt is None or event_dt < window_start:
            continue
        detail = (
            f"station={risk.get('station_code') or '-'}, "
            f"risk={risk.get('risk_level') or '-'}, salinity={risk.get('salinity_dsm') or '-'}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "risk_assessment",
                    str(risk.get("risk_level") or "unknown"),
                    "-",
                    detail,
                ],
            )
        )

    for incident in incidents:
        event_dt = _parse_dt(incident.get("opened_at")) or _parse_dt(incident.get("created_at"))
        if event_dt is None or event_dt < window_start:
            continue
        detail = (
            f"severity={incident.get('severity') or '-'}, "
            f"title={incident.get('title') or '-'}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "incident",
                    str(incident.get("status") or "unknown"),
                    str(incident.get("id") or "-"),
                    detail,
                ],
            )
        )

    for plan in plans:
        event_dt = _parse_dt(plan.get("created_at"))
        if event_dt is None or event_dt < window_start:
            continue
        detail = (
            f"risk_assessment_id={plan.get('risk_assessment_id') or '-'}, "
            f"objective={str(plan.get('objective') or '-')[:70]}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "action_plan",
                    str(plan.get("status") or "unknown"),
                    str(plan.get("id") or "-"),
                    detail,
                ],
            )
        )

    for run in runs:
        event_dt = _parse_dt(run.get("started_at")) or _parse_dt(run.get("created_at"))
        if event_dt is None or event_dt < window_start:
            continue
        detail = (
            f"type={run.get('run_type') or '-'}, source={run.get('trigger_source') or '-'}, "
            f"plan_id={run.get('action_plan_id') or '-'}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "agent_run",
                    str(run.get("status") or "unknown"),
                    str(run.get("id") or "-"),
                    detail,
                ],
            )
        )

    for batch in execution_batches:
        event_dt = (
            _parse_dt(batch.get("completed_at"))
            or _parse_dt(batch.get("started_at"))
            or _parse_dt(batch.get("created_at"))
        )
        if event_dt is None or event_dt < window_start:
            continue
        detail = (
            f"plan_id={batch.get('plan_id') or '-'}, "
            f"step_count={batch.get('step_count') or 0}, simulated={batch.get('simulated')}"
        )
        events.append(
            (
                event_dt,
                [
                    _fmt_dt(event_dt),
                    "execution_batch",
                    str(batch.get("status") or "unknown"),
                    str(batch.get("id") or "-"),
                    detail,
                ],
            )
        )

    events.sort(key=lambda item: item[0], reverse=True)
    timeline_rows = [row for _, row in events[:max_rows]]

    snapshot = {
        "refreshed_at_utc": now_utc.isoformat(),
        "window_minutes": window_minutes,
        "kpi": {
            "active_goals": active_goals,
            "dedup_skips": dedup_skips,
            "open_incidents": summary.get("open_incidents", 0),
            "pending_approvals": summary.get("pending_approvals", 0),
            "run_success_rate_percent": round(run_success_rate, 2),
            "run_avg_duration_seconds": run_avg_duration,
            "throughput": {
                "readings": readings_in_window,
                "risk_assessments": risks_in_window,
                "new_plans": plans_in_window,
                "execution_batches": batches_in_window,
            },
            "observe_to_risk_lag_seconds": observe_to_risk_lag,
        },
        "counts": {
            "goals": len(goals),
            "runs": len(runs),
            "readings": len(readings),
            "risk_timeline_items": len(risk_timeline),
            "incidents": len(incidents),
            "plans": len(plans),
            "execution_batches": len(execution_batches),
            "timeline_rows": len(timeline_rows),
        },
    }
    return kpi_md, timeline_rows, _to_json(snapshot)


def _refresh_live_monitor(base_url: str, window_minutes: int, max_rows: int) -> tuple[str, list[list[str]], str]:
    try:
        return _build_live_monitor(base_url=base_url, window_minutes=window_minutes, max_rows=max_rows)
    except Exception as exc:
        return (
            "### Live Flow Health\n"
            f"- State: failed\n"
            f"- Error: {exc}\n"
            f"- Time: {_ts()}",
            [],
            _to_json({"error": str(exc)}),
        )


def _tick_live_monitor(
    base_url: str,
    auto_refresh: bool,
    window_minutes: int,
    max_rows: int,
) -> tuple[Any, Any, Any]:
    if not auto_refresh:
        return gr.update(), gr.update(), gr.update()
    return _refresh_live_monitor(base_url=base_url, window_minutes=window_minutes, max_rows=max_rows)


def _update_timer_settings(auto_refresh: bool, refresh_seconds: float) -> Any:
    seconds = max(2.0, min(float(refresh_seconds), 30.0))
    return gr.update(active=bool(auto_refresh), value=seconds)


def _fetch_overview(base_url: str) -> tuple[str, str, str, str]:
    try:
        health = _http_json(base_url=base_url, method="GET", path="/api/v1/health", timeout=10)
        summary = _http_json(base_url=base_url, method="GET", path="/api/v1/dashboard/summary")
        plans = _http_json(base_url=base_url, method="GET", path="/api/v1/plans?limit=10")
        runs = _http_json(base_url=base_url, method="GET", path="/api/v1/agent/runs?limit=10")
    except SimulationError as exc:
        return (
            f"### Server Status\n- State: unreachable\n- Error: {exc}",
            "{}",
            "[]",
            "{}",
        )

    status_md = (
        "### Server Status\n"
        f"- State: reachable\n"
        f"- Time: {_ts()}\n"
        f"- Base URL: {base_url}"
    )
    return status_md, _to_json(summary), _to_json(plans), _to_json(runs)


def _extract_plan_id_from_choice(choice: str | None) -> str:
    if not choice:
        return ""
    return str(choice).split("|", 1)[0].strip()


def _build_plan_choice(plan: dict[str, Any]) -> str:
    objective = str(plan.get("objective") or "").strip()
    objective_short = objective[:56] + "..." if len(objective) > 56 else objective
    return (
        f"{plan.get('id')} | status={plan.get('status')} | "
        f"risk_assessment={plan.get('risk_assessment_id')} | {objective_short}"
    )


def _list_pending_plans(base_url: str, *, limit: int = 120) -> list[dict[str, Any]]:
    plans = _http_json(base_url=base_url, method="GET", path=f"/api/v1/plans?limit={limit}")
    if not isinstance(plans, list):
        return []
    return [plan for plan in plans if str(plan.get("status") or "") == "pending_approval"]


def _refresh_pending_controls(base_url: str) -> tuple[str, Any, str, str]:
    try:
        pending = _list_pending_plans(base_url)
        choices = [_build_plan_choice(plan) for plan in pending]
        selected = choices[0] if choices else None
        selected_plan_id = _extract_plan_id_from_choice(selected)
        status_md = (
            "### Manual Control\n"
            f"- Pending plans: {len(choices)}\n"
            f"- Refreshed at: {_ts()}"
        )
        payload = {
            "count": len(choices),
            "plan_ids": [str(plan.get("id")) for plan in pending],
            "items": pending,
        }
        return status_md, gr.update(choices=choices, value=selected), selected_plan_id, _to_json(payload)
    except Exception as exc:
        status_md = (
            "### Manual Control\n"
            "- State: failed\n"
            f"- Error: {exc}"
        )
        return status_md, gr.update(choices=[], value=None), "", _to_json({"error": str(exc)})


def _sync_plan_id_from_choice(choice: str) -> str:
    return _extract_plan_id_from_choice(choice)


def _manual_decide_plan(
    base_url: str,
    plan_id: str,
    decision: str,
    comment: str,
    actor_name: str,
) -> tuple[str, str, str, str, Any, str, str]:
    plan_id = plan_id.strip()
    actor_name = actor_name.strip() or "demo-operator"
    if not plan_id:
        return (
            "### Manual Decision\n- State: failed\n- Error: plan_id is required",
            _to_json({"error": "missing_plan_id"}),
            "[]",
            "{}",
            gr.update(),
            "",
            "{}",
        )

    try:
        result = _http_json(
            base_url=base_url,
            method="POST",
            path=f"/api/v1/approvals/plans/{plan_id}/decision?actor_name={actor_name}",
            payload={"decision": decision, "comment": comment or f"manual-{decision} from gradio"},
        )
        status_md = (
            "### Manual Decision\n"
            "- State: success\n"
            f"- Plan: {plan_id}\n"
            f"- Decision: {decision}\n"
            f"- Time: {_ts()}"
        )
        overview = _fetch_overview(base_url)
        pending_status, pending_update, selected_plan_id, pending_json = _refresh_pending_controls(base_url)
        _ = pending_status
        return (
            status_md,
            _to_json(result),
            overview[2],
            overview[3],
            pending_update,
            selected_plan_id,
            pending_json,
        )
    except Exception as exc:
        status_md = (
            "### Manual Decision\n"
            "- State: failed\n"
            f"- Plan: {plan_id}\n"
            f"- Error: {exc}"
        )
        return (
            status_md,
            _to_json({"error": str(exc)}),
            "[]",
            "{}",
            gr.update(),
            plan_id,
            "{}",
        )


def _manual_execute_plan(
    base_url: str,
    plan_id: str,
    idempotency_key: str,
) -> tuple[str, str, str, str, Any, str, str]:
    plan_id = plan_id.strip()
    if not plan_id:
        return (
            "### Manual Execute\n- State: failed\n- Error: plan_id is required",
            _to_json({"error": "missing_plan_id"}),
            "[]",
            "{}",
            gr.update(),
            "",
            "{}",
        )

    payload: dict[str, Any] = {}
    key = idempotency_key.strip()
    if key:
        payload["idempotency_key"] = key

    try:
        result = _http_json(
            base_url=base_url,
            method="POST",
            path=f"/api/v1/execution-batches/plans/{plan_id}/simulate",
            payload=payload,
        )
        status_md = (
            "### Manual Execute\n"
            "- State: success\n"
            f"- Plan: {plan_id}\n"
            f"- Time: {_ts()}"
        )
        overview = _fetch_overview(base_url)
        pending_status, pending_update, selected_plan_id, pending_json = _refresh_pending_controls(base_url)
        _ = pending_status
        return (
            status_md,
            _to_json(result),
            overview[2],
            overview[3],
            pending_update,
            selected_plan_id,
            pending_json,
        )
    except Exception as exc:
        status_md = (
            "### Manual Execute\n"
            "- State: failed\n"
            f"- Plan: {plan_id}\n"
            f"- Error: {exc}"
        )
        return (
            status_md,
            _to_json({"error": str(exc)}),
            "[]",
            "{}",
            gr.update(),
            plan_id,
            "{}",
        )


def _run_scenario(
    base_url: str,
    timeout_seconds: int,
    scenario_key: str,
    station_code: str,
    frame_pause_seconds: float,
    close_open_incidents: bool,
    inject_post_execute_reading: bool,
) -> tuple[str, str, str, str, str]:
    if scenario_key not in SCENARIO_SENSOR_PROFILES:
        return (
            f"### Scenario Run\n- State: failed\n- Error: Unknown scenario '{scenario_key}'",
            "",
            "{}",
            "[]",
            "{}",
        )

    logs = io.StringIO()
    try:
        with redirect_stdout(logs):
            result = run_named_scenario(
                base_url=base_url,
                scenario_key=scenario_key,
                timeout_seconds=int(timeout_seconds),
                station_code=(station_code.strip() or None),
                frame_pause_seconds=float(frame_pause_seconds),
                close_open_incidents=bool(close_open_incidents),
                inject_post_execute_reading=bool(inject_post_execute_reading),
            )
        status_md = (
            "### Scenario Run\n"
            f"- State: success\n"
            f"- Scenario: {scenario_key}\n"
            f"- Completed at: {_ts()}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json(result), overview[2], overview[3]
    except Exception as exc:
        status_md = (
            "### Scenario Run\n"
            f"- State: failed\n"
            f"- Scenario: {scenario_key}\n"
            f"- Error: {exc}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json({"error": str(exc)}), overview[2], overview[3]


def _run_all(
    base_url: str,
    timeout_seconds: int,
    station_code: str,
    frame_pause_seconds: float,
    close_open_incidents: bool,
    inject_post_execute_reading: bool,
) -> tuple[str, str, str, str, str]:
    logs = io.StringIO()
    outputs: dict[str, Any] = {}
    try:
        with redirect_stdout(logs):
            for key in SCENARIO_SENSOR_PROFILES:
                outputs[key] = run_named_scenario(
                    base_url=base_url,
                    scenario_key=key,
                    timeout_seconds=int(timeout_seconds),
                    station_code=(station_code.strip() or None),
                    frame_pause_seconds=float(frame_pause_seconds),
                    close_open_incidents=bool(close_open_incidents),
                    inject_post_execute_reading=bool(inject_post_execute_reading),
                )
        status_md = (
            "### Scenario Run\n"
            "- State: success\n"
            "- Scenario: all\n"
            f"- Completed at: {_ts()}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json(outputs), overview[2], overview[3]
    except Exception as exc:
        status_md = (
            "### Scenario Run\n"
            "- State: failed\n"
            "- Scenario: all\n"
            f"- Error: {exc}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json(outputs), overview[2], overview[3]


def _inject_sensor_profile(
    base_url: str,
    timeout_seconds: int,
    scenario_key: str,
    station_code: str,
    frame_pause_seconds: float,
    close_open_incidents: bool,
    inject_post_execute_reading: bool,
) -> tuple[str, str, str, str, str]:
    logs = io.StringIO()
    try:
        with redirect_stdout(logs):
            result = run_sensor_profile(
                base_url=base_url,
                scenario_key=scenario_key,
                timeout_seconds=int(timeout_seconds),
                station_code=(station_code.strip() or None),
                frame_pause_seconds=float(frame_pause_seconds),
                close_open_incidents=bool(close_open_incidents),
                inject_post_execute_reading=bool(inject_post_execute_reading),
            )
        status_md = (
            "### Sensor Stream\n"
            "- State: success\n"
            f"- Scenario: {scenario_key}\n"
            f"- Completed at: {_ts()}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json(result), overview[2], overview[3]
    except Exception as exc:
        status_md = (
            "### Sensor Stream\n"
            "- State: failed\n"
            f"- Scenario: {scenario_key}\n"
            f"- Error: {exc}"
        )
        overview = _fetch_overview(base_url)
        return status_md, logs.getvalue().strip(), _to_json({"error": str(exc)}), overview[2], overview[3]


def build_demo_app() -> gr.Blocks:
    with gr.Blocks(title="Mekong-SALT Demo Control Center") as app:
        gr.Markdown(
            "# Mekong-SALT Demo Control Center\n"
            "Run scenario-driven sensor streams and inspect agentic planning/execution evidence in one place."
        )

        with gr.Row():
            base_url = gr.Textbox(label="Backend Base URL", value="http://localhost:8000")
            timeout_seconds = gr.Slider(
                label="Scenario Timeout (seconds)",
                minimum=30,
                maximum=600,
                step=10,
                value=180,
            )

        with gr.Row():
            station_code = gr.Textbox(
                label="Target Station Code (optional)",
                value="",
                placeholder="Leave blank to auto-select latest station",
            )
            frame_pause_seconds = gr.Slider(
                label="Frame Pause (seconds)",
                minimum=0.0,
                maximum=5.0,
                step=0.2,
                value=1.2,
            )
            close_open_incidents = gr.Checkbox(
                label="Auto-close open incidents before run",
                value=True,
            )
            inject_post_execute_reading = gr.Checkbox(
                label="Inject post-execute reading + evaluate feedback",
                value=True,
            )

        with gr.Row():
            refresh_btn = gr.Button("Refresh Overview", variant="secondary")
            scenario = gr.Dropdown(
                label="Scenario",
                choices=list(SCENARIO_SENSOR_PROFILES.keys()),
                value="critical-timeout-replan",
            )
            inject_profile_btn = gr.Button("Inject Sensor Profile", variant="secondary")
            run_one_btn = gr.Button("Run Full Scenario", variant="primary")
            run_all_btn = gr.Button("Run All Scenarios", variant="primary")

        status_md = gr.Markdown("### Server Status\n- State: unknown")

        with gr.Row():
            summary_json = gr.Code(label="Dashboard Summary", language="json", value="{}")
            runs_json = gr.Code(label="Recent Agent Runs", language="json", value="{}")

        with gr.Row():
            plans_json = gr.Code(label="Recent Plans", language="json", value="[]")
            scenario_result_json = gr.Code(label="Scenario Result", language="json", value="{}")

        scenario_logs = gr.Textbox(label="Scenario Logs", lines=14, max_lines=22)

        gr.Markdown("## Manual Approval & Execute")
        with gr.Row():
            refresh_pending_btn = gr.Button("Refresh Pending Plans", variant="secondary")
            pending_plan_select = gr.Dropdown(
                label="Pending Approval Plans",
                choices=[],
                value=None,
            )

        with gr.Row():
            manual_plan_id = gr.Textbox(
                label="Plan ID",
                value="",
                placeholder="Auto-filled from dropdown or paste plan id here",
            )
            manual_actor_name = gr.Textbox(
                label="Actor Name",
                value="demo-operator",
            )

        with gr.Row():
            manual_decision = gr.Radio(
                label="Decision",
                choices=["approved", "rejected"],
                value="approved",
            )
            manual_comment = gr.Textbox(
                label="Decision Comment",
                value="manual decision from gradio",
            )
            decide_btn = gr.Button("Apply Decision", variant="primary")

        with gr.Row():
            execute_idempotency_key = gr.Textbox(
                label="Execute Idempotency Key (optional)",
                value="",
                placeholder="Optional key for replay-safe execute",
            )
            execute_btn = gr.Button("Execute Simulated", variant="primary")

        manual_status_md = gr.Markdown("### Manual Control\n- Pending plans: unknown")
        manual_result_json = gr.Code(label="Manual Action Result", language="json", value="{}")
        pending_plans_json = gr.Code(label="Pending Plans Snapshot", language="json", value="{}")

        gr.Markdown("## Live Monitor")
        with gr.Row():
            auto_live_refresh = gr.Checkbox(
                label="Auto Refresh Live Monitor",
                value=True,
            )
            live_refresh_seconds = gr.Slider(
                label="Refresh Every (seconds)",
                minimum=2.0,
                maximum=30.0,
                step=1.0,
                value=5.0,
            )
            live_window_minutes = gr.Slider(
                label="Timeline Window (minutes)",
                minimum=5,
                maximum=360,
                step=5,
                value=60,
            )
            live_max_rows = gr.Slider(
                label="Max Timeline Rows",
                minimum=20,
                maximum=300,
                step=10,
                value=120,
            )
            refresh_live_btn = gr.Button("Refresh Live Monitor", variant="secondary")

        live_kpi_md = gr.Markdown("### Live Flow Health\n- State: unknown")
        live_timeline_table = gr.Dataframe(
            headers=["time_utc", "stage", "status", "entity_id", "detail"],
            datatype=["str", "str", "str", "str", "str"],
            value=[],
            row_count=(0, "dynamic"),
            column_count=(5, "fixed"),
            interactive=False,
            label="Realtime Flow Timeline",
        )
        live_snapshot_json = gr.Code(label="Live Monitor Snapshot", language="json", value="{}")
        live_timer = gr.Timer(value=5.0, active=True)

        refresh_btn.click(
            fn=_fetch_overview,
            inputs=[base_url],
            outputs=[status_md, summary_json, plans_json, runs_json],
        )

        run_one_btn.click(
            fn=_run_scenario,
            inputs=[
                base_url,
                timeout_seconds,
                scenario,
                station_code,
                frame_pause_seconds,
                close_open_incidents,
                inject_post_execute_reading,
            ],
            outputs=[status_md, scenario_logs, scenario_result_json, plans_json, runs_json],
        )

        run_all_btn.click(
            fn=_run_all,
            inputs=[
                base_url,
                timeout_seconds,
                station_code,
                frame_pause_seconds,
                close_open_incidents,
                inject_post_execute_reading,
            ],
            outputs=[status_md, scenario_logs, scenario_result_json, plans_json, runs_json],
        )

        inject_profile_btn.click(
            fn=_inject_sensor_profile,
            inputs=[
                base_url,
                timeout_seconds,
                scenario,
                station_code,
                frame_pause_seconds,
                close_open_incidents,
                inject_post_execute_reading,
            ],
            outputs=[status_md, scenario_logs, scenario_result_json, plans_json, runs_json],
        )

        refresh_pending_btn.click(
            fn=_refresh_pending_controls,
            inputs=[base_url],
            outputs=[manual_status_md, pending_plan_select, manual_plan_id, pending_plans_json],
        )

        pending_plan_select.change(
            fn=_sync_plan_id_from_choice,
            inputs=[pending_plan_select],
            outputs=[manual_plan_id],
        )

        decide_btn.click(
            fn=_manual_decide_plan,
            inputs=[base_url, manual_plan_id, manual_decision, manual_comment, manual_actor_name],
            outputs=[
                manual_status_md,
                manual_result_json,
                plans_json,
                runs_json,
                pending_plan_select,
                manual_plan_id,
                pending_plans_json,
            ],
        )

        execute_btn.click(
            fn=_manual_execute_plan,
            inputs=[base_url, manual_plan_id, execute_idempotency_key],
            outputs=[
                manual_status_md,
                manual_result_json,
                plans_json,
                runs_json,
                pending_plan_select,
                manual_plan_id,
                pending_plans_json,
            ],
        )

        refresh_live_btn.click(
            fn=_refresh_live_monitor,
            inputs=[base_url, live_window_minutes, live_max_rows],
            outputs=[live_kpi_md, live_timeline_table, live_snapshot_json],
        )

        auto_live_refresh.change(
            fn=_update_timer_settings,
            inputs=[auto_live_refresh, live_refresh_seconds],
            outputs=[live_timer],
        )

        live_refresh_seconds.change(
            fn=_update_timer_settings,
            inputs=[auto_live_refresh, live_refresh_seconds],
            outputs=[live_timer],
        )

        live_timer.tick(
            fn=_tick_live_monitor,
            inputs=[base_url, auto_live_refresh, live_window_minutes, live_max_rows],
            outputs=[live_kpi_md, live_timeline_table, live_snapshot_json],
        )

        app.load(
            fn=_fetch_overview,
            inputs=[base_url],
            outputs=[status_md, summary_json, plans_json, runs_json],
        )

        app.load(
            fn=_refresh_pending_controls,
            inputs=[base_url],
            outputs=[manual_status_md, pending_plan_select, manual_plan_id, pending_plans_json],
        )

        app.load(
            fn=_refresh_live_monitor,
            inputs=[base_url, live_window_minutes, live_max_rows],
            outputs=[live_kpi_md, live_timeline_table, live_snapshot_json],
        )

    return app


def main() -> None:
    app = build_demo_app()
    app.launch(server_name="127.0.0.1", server_port=7860, show_error=True)


if __name__ == "__main__":
    main()
