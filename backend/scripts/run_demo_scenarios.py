"""Demo scenario catalog for Mekong-SALT backend.

This script prints curated end-to-end demo scenarios so operators can run a
consistent storyline after data/setup is ready.
"""

from __future__ import annotations

import argparse
import json
import sys


SCENARIOS = {
    "critical-timeout-replan": {
        "title": "Critical Risk -> Pending Approval -> Timeout Auto-Reject -> Replan",
        "objective": (
            "Send sensor frames that drive the engine from elevated salinity into critical risk, "
            "then show timeout recovery and replan."
        ),
        "preconditions": [
            "Backend API is running.",
            "ACTIVE_MONITORING_MODE=active.",
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_MINUTES=1.",
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_ACTION=auto_reject.",
            "Seed/setup data is available.",
        ],
        "before_commands": [
            {
                "step": "Chuẩn bị demo sạch trước khi bắn scenario.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-migrations",
                "expect": "Seed, RAG corpus, và timeout demo settings đã sẵn sàng.",
            },
        ],
        "steps": [
            {
                "step": "Publish scenario sensor stream via MQTT device path (danger -> critical) with an extra window frame.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan",
                "expect": "Backend ingests device frames and active monitoring worker x? l? lifecycle theo policy hi?n c?.",
            },
            {
                "step": "Optional fallback: publish same stream through HTTP for local debug.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --transport http",
                "expect": "HTTP path should publish the same sensor payload if broker is unavailable.",
            },
            {
                "step": "Optional: re-run the same stream through MQTT edge transport.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883",
                "expect": "MQTT consumer ingests the same frames and backend worker x? l? ti?p.",
            },
            {
                "step": "Inspect plan lifecycle after timeout.",
                "command": "curl http://localhost:8000/api/v1/plans?limit=10",
                "expect": "Old plan is rejected and a fresh pending_approval plan appears.",
            },
        ],
        "after_commands": [
            {
                "step": "Kiểm tra plan sau khi timeout tự xử lý.",
                "command": "curl http://localhost:8000/api/v1/plans?limit=10",
                "expect": "Danh sách plan phải có trạng thái rejected và pending_approval mới.",
            },
        ],
        "highlights": [
            "Sensor scenario is the trigger point (not manual plan API).",
            "Risk is sensor-first: salinity is the base band, while trend and fresh context can only nudge it upward.",
            "MQTT is the primary device path; HTTP is a fallback for demo/debug only.",
            "Approval-timeout policy recovers automatically.",
            "Same scenario can run with HTTP or MQTT transport for parity checks.",
        ],
    },
    "fast-approve-execute": {
        "title": "Fast Approve -> Simulated Execution -> Feedback + Memory",
        "objective": (
            "Send a high-risk sensor stream that produces a reviewable plan, approve it, and execute "
            "the simulated batch end-to-end with dual-unit salinity traces."
        ),
        "preconditions": [
            "Backend API is running.",
            "Seed/setup data is available.",
        ],
        "before_commands": [
            {
                "step": "Chuẩn bị state sạch trước khi chạy execution demo.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-migrations",
                "expect": "Region demo, stations, gates, và RAG corpus đã sẵn sàng.",
            },
        ],
        "steps": [
            {
                "step": "Publish full sensor-driven fast execution scenario with an extra trend frame.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute",
                "expect": "Backend receives the stream and the follow-up feedback probe without script-side GET polling.",
            },
        ],
        "after_commands": [
            {
                "step": "Xem execution batches và action outcomes sau khi chạy xong.",
                "command": "curl http://localhost:8000/api/v1/execution-batches?limit=10 && curl http://localhost:8000/api/v1/action-outcomes?limit=10",
                "expect": "Có batch simulated, action logs, và feedback lifecycle đi kèm.",
            },
        ],
        "highlights": [
            "Sensor feed triggers agentic planning first.",
            "The current risk engine is sensor-first: salinity anchors the band, while trend and fresh weather/tide context only modify it.",
            "Execution and approval happen in backend/UI flow, not from the simulator script.",
            "Salinity values are shown as dS/m and equivalent g/L.",
            "Use --no-post-execute-reading if you want to disable the feedback-probe publish.",
        ],
    },
    "rag-provenance-drilldown": {
        "title": "RAG Provenance Drilldown",
        "objective": "Trigger a fresh plan from sensor frames and inspect retrieval trace/citations.",
        "preconditions": [
            "RAG sample corpus has been ingested.",
            "Backend API is running.",
        ],
        "before_commands": [
            {
                "step": "Nạp lại bộ RAG mẫu nếu vừa chỉnh nội dung tài liệu.",
                "command": "./.venv/Scripts/python.exe scripts/ingest_rag_samples.py",
                "expect": "Corpus demo được sync lại trước khi tạo plan mới.",
            },
        ],
        "steps": [
            {
                "step": "Publish scenario frames for provenance drilldown with a fuller trend window.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown --json",
                "expect": "Script returns a publish summary; provenance trace is inspected from backend state or UI.",
            },
        ],
        "after_commands": [
            {
                "step": "Xem chi tiết agent run và trace truy hồi.",
                "command": "curl http://localhost:8000/api/v1/agent/runs?limit=10",
                "expect": "Run mới xuất hiện với retrieval trace và knowledge context gắn theo scenario.",
            },
        ],
        "highlights": [
            "Retrieval evidence is tied to a specific sensor-triggered planning run.",
            "Top citations/source mix can be explained to stakeholders.",
            "The plan trace should reflect the current risk engine outputs, not a fixed salinity-only story.",
        ],
    },
    "warning-observe-recover": {
        "title": "Warning Observe -> Recovery Window",
        "objective": "Publish a warning-level stream that stays conservative under the current engine, then stabilize into a recovery window.",
        "preconditions": [
            "Backend API is running.",
            "Seed/setup data is available.",
        ],
        "before_commands": [
            {
                "step": "Chuẩn bị state sạch trước khi chạy recovery demo.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-migrations",
                "expect": "Seed, RAG corpus, và active monitoring worker đều sẵn sàng.",
            },
        ],
        "steps": [
            {
                "step": "Publish warning-to-recovery sensor stream via MQTT device path with an extra warning frame.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883",
                "expect": "Backend ingests the warning stream and transitions into a cautious recovery posture.",
            },
            {
                "step": "Optional fallback: publish the same stream through HTTP for local debug.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --transport http",
                "expect": "HTTP path should mirror the same sensor frames when broker is unavailable.",
            },
        ],
        "after_commands": [
            {
                "step": "Kiểm tra risk và plan sau chuỗi warning-recovery.",
                "command": "curl http://localhost:8000/api/v1/risk/latest && curl http://localhost:8000/api/v1/plans?limit=10",
                "expect": "Risk latest phản ánh nhịp recovery đã quay về dưới warning; plan list thể hiện nhánh quan sát nếu worker tạo plan.",
            },
        ],
        "highlights": [
            "This scenario shows a conservative operational posture rather than only critical escalation.",
            "Trend and freshness matter, but the engine still keeps salinity as the anchor band.",
            "The demo now includes both escalation and recovery patterns.",
            "MQTT remains the primary path; HTTP is a fallback for parity checks.",
        ],
    },
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List or print Mekong-SALT demo scenarios.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenario keys only.",
    )
    parser.add_argument(
        "--scenario",
        default="all",
        help="Scenario key to print. Use 'all' to print every scenario.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print output as JSON for automation.",
    )
    return parser


def _print_command_block(title: str, commands: list[dict[str, str]] | None) -> None:
    if not commands:
        return
    print(f"{title}:")
    for idx, command in enumerate(commands, start=1):
        print(f"{idx}. {command['step']}")
        print(f"   cmd: {command['command']}")
        print(f"   expect: {command['expect']}")


def _print_scenario(key: str, data: dict[str, object]) -> None:
    print(f"\n=== {key} ===")
    print("Title:", data["title"])
    print("Objective:", data["objective"])
    print("Preconditions:")
    for line in data["preconditions"]:
        print(f"- {line}")
    _print_command_block("Trước demo", data.get("before_commands"))
    print("Steps:")
    for idx, step in enumerate(data["steps"], start=1):
        print(f"{idx}. {step['step']}")
        print(f"   cmd: {step['command']}")
        print(f"   expect: {step['expect']}")
    _print_command_block("Sau demo", data.get("after_commands"))
    print("Highlights:")
    for line in data["highlights"]:
        print(f"- {line}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")

    args = _build_parser().parse_args()

    if args.list:
        for key in SCENARIOS:
            print(key)
        return

    if args.scenario != "all" and args.scenario not in SCENARIOS:
        raise SystemExit(
            f"Unknown scenario '{args.scenario}'. Use --list to see available keys."
        )

    selected = (
        {args.scenario: SCENARIOS[args.scenario]}
        if args.scenario != "all"
        else SCENARIOS
    )

    if args.json:
        print(json.dumps(selected, ensure_ascii=True, indent=2))
        return

    for key, data in selected.items():
        _print_scenario(key, data)


if __name__ == "__main__":
    main()
