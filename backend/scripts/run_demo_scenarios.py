"""Demo scenario catalog for Mekong-SALT backend.

This script prints curated end-to-end demo scenarios so operators can run a
consistent storyline after data/setup is ready.
"""

from __future__ import annotations

import argparse
import json


SCENARIOS = {
    "critical-timeout-replan": {
        "title": "Critical Risk -> Pending Approval -> Timeout Auto-Reject -> Replan",
        "objective": (
            "Send escalating sensor frames to trigger critical plan and timeout recovery "
            "(canonical dS/m, display g/L)."
        ),
        "preconditions": [
            "Backend API is running.",
            "ACTIVE_MONITORING_MODE=active.",
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_MINUTES=1.",
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_ACTION=auto_reject.",
            "Seed/setup data is available.",
        ],
        "steps": [
            {
                "step": "Emit scenario sensor stream (danger -> critical).",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan",
                "expect": "Worker creates pending_approval plan from scenario-triggered readings.",
            },
            {
                "step": "Inspect plan lifecycle after timeout.",
                "command": "curl http://localhost:8000/api/v1/plans?limit=10",
                "expect": "Old plan is rejected and a fresh pending_approval plan appears.",
            },
        ],
        "highlights": [
            "Sensor scenario is the trigger point (not manual plan API).",
            "Approval-timeout policy recovers automatically.",
        ],
    },
    "fast-approve-execute": {
        "title": "Fast Approve -> Simulated Execution -> Feedback + Memory",
        "objective": (
            "Send high-risk sensor stream, approve, and execute simulated batch end-to-end "
            "with dual-unit salinity traces."
        ),
        "preconditions": [
            "Backend API is running.",
            "Seed/setup data is available.",
        ],
        "steps": [
            {
                "step": "Run full sensor-driven fast execution scenario.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute",
                "expect": (
                    "Plan is approved/simulated, then one fresh post-execution reading is injected "
                    "and feedback is re-evaluated."
                ),
            },
        ],
        "highlights": [
            "Sensor feed triggers agentic planning first.",
            "Execution remains simulated but fully traceable with logs/batch.",
            "Salinity values are shown as dS/m and equivalent g/L.",
            "Use --no-post-execute-reading if you want to disable feedback-probe injection.",
        ],
    },
    "rag-provenance-drilldown": {
        "title": "RAG Provenance Drilldown",
        "objective": "Trigger a fresh plan from sensor frames and inspect retrieval trace/citations.",
        "preconditions": [
            "RAG sample corpus has been ingested.",
            "Backend API is running.",
        ],
        "steps": [
            {
                "step": "Run scenario and collect run evidence.",
                "command": "./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown --json",
                "expect": "Result includes run_id, source_counts, top_citations, and knowledge_context_preview.",
            },
        ],
        "highlights": [
            "Retrieval evidence is tied to a specific sensor-triggered planning run.",
            "Top citations/source mix can be explained to stakeholders.",
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


def _print_scenario(key: str, data: dict[str, object]) -> None:
    print(f"\n=== {key} ===")
    print("Title:", data["title"])
    print("Objective:", data["objective"])
    print("Preconditions:")
    for line in data["preconditions"]:
        print(f"- {line}")
    print("Steps:")
    for idx, step in enumerate(data["steps"], start=1):
        print(f"{idx}. {step['step']}")
        print(f"   cmd: {step['command']}")
        print(f"   expect: {step['expect']}")
    print("Highlights:")
    for line in data["highlights"]:
        print(f"- {line}")


def main() -> None:
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
