"""One-shot demo setup runbook for Mekong-SALT backend.

This script prepares local demo data by running:
1) alembic upgrade head
2) seed script
3) RAG sample ingestion

It also validates the active-monitoring approval-timeout settings so the
pending-approval auto-recovery path is visible during demo.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_ROOT / ".env"


class SetupError(RuntimeError):
    """Raised when one setup step fails."""


def _run_step(step_name: str, command: list[str]) -> None:
    print(f"\n[STEP] {step_name}")
    print("[CMD]", " ".join(command))
    completed = subprocess.run(command, cwd=str(BACKEND_ROOT), check=False)
    if completed.returncode != 0:
        raise SetupError(f"Step failed: {step_name} (exit_code={completed.returncode})")


def _read_env_lines() -> list[str]:
    if not ENV_FILE.exists():
        return []
    return ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()


def _read_env_value(lines: Iterable[str], key: str) -> str | None:
    prefix = f"{key}="
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _check_demo_timeout_settings(strict: bool) -> None:
    lines = _read_env_lines()
    timeout_minutes = _read_env_value(lines, "ACTIVE_MONITORING_APPROVAL_TIMEOUT_MINUTES")
    timeout_action = _read_env_value(lines, "ACTIVE_MONITORING_APPROVAL_TIMEOUT_ACTION")

    warnings: list[str] = []
    if timeout_minutes != "1":
        warnings.append(
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_MINUTES should be 1 for quick demo cycles."
        )
    if (timeout_action or "").lower() != "auto_reject":
        warnings.append(
            "ACTIVE_MONITORING_APPROVAL_TIMEOUT_ACTION should be auto_reject to unblock stale approvals."
        )

    if warnings:
        print("\n[WARN] Approval-timeout demo settings are not ideal:")
        for warning in warnings:
            print(f"- {warning}")
        if strict:
            raise SetupError("Strict mode enabled and timeout settings are not demo-ready.")
    else:
        print("\n[OK] Approval-timeout demo settings look good.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare Mekong-SALT backend for end-to-end feature demo.",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running Alembic migrations.",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip running scripts/seed.py.",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip running scripts/ingest_rag_samples.py.",
    )
    parser.add_argument(
        "--strict-timeout-config",
        action="store_true",
        help="Fail setup if approval-timeout demo settings are not configured as expected.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not ENV_FILE.exists():
        raise SetupError("Missing .env file. Create backend/.env before running demo setup.")

    python_exe = sys.executable
    os.environ.setdefault("PYTHONUTF8", "1")

    print("[INFO] Backend root:", BACKEND_ROOT)
    print("[INFO] Python:", python_exe)

    _check_demo_timeout_settings(strict=args.strict_timeout_config)

    if not args.skip_migrations:
        _run_step("Apply migrations", [python_exe, "-m", "alembic", "upgrade", "head"])

    if not args.skip_seed:
        _run_step("Seed baseline data", [python_exe, "scripts/seed.py"])

    if not args.skip_ingest:
        _run_step("Ingest RAG sample corpus", [python_exe, "scripts/ingest_rag_samples.py"])

    print("\n[DONE] Demo setup completed.")
    print("[NEXT] Khởi động API: ./.venv/Scripts/python.exe -m uvicorn main:app --reload")
    print("[NEXT] Liệt kê scenario: ./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --list")
    print("[NEXT] In toàn bộ scenario: ./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --scenario all")
    print(
        "[NEXT] Chạy mô phỏng thật: ./.venv/Scripts/python.exe scripts/run_demo_simulation.py "
        "--scenario all --timeout-seconds 300 --frame-pause-seconds 10"
    )
    print(
        "[NEXT] Nhắm một trạm: ./.venv/Scripts/python.exe scripts/run_demo_simulation.py "
        "--scenario fast-approve-execute --station-code GOCONG-01 --frame-pause-seconds 10"
    )
    print("        Kịch bản này dừng ở pending approval, không tự duyệt plan.")
    print(
        "[NEXT] Mô phỏng MQTT: ./.venv/Scripts/python.exe scripts/run_demo_simulation.py "
        "--scenario fast-approve-execute --mqtt-broker-url localhost "
        "--mqtt-broker-port 1883 --frame-pause-seconds 10"
    )
    print("        Chỉ publish sensor frames; approval vẫn do người dùng thực hiện.")
    print("[NEXT] Mở demo Gradio: ./.venv/Scripts/python.exe gradio_app/demo_app.py")
    print("[NEXT] Theo dõi trạng thái: GET /api/v1/dashboard/summary và GET /api/v1/plans")
    print("[NEXT] Ghi chú policy: backend/document/proposal_unit_alignment.md")


if __name__ == "__main__":
    try:
        main()
    except SetupError as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1) from exc
