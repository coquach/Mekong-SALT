"""Gate command driver boundaries for simulated and future real device control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.action import ActionPlan
from app.models.enums import ActionType, GateStatus
from app.models.gate import Gate
from app.repositories.gate import GateRepository
from app.schemas.agent import PlanStep


GATE_ACTION_TYPES = {
    ActionType.CLOSE_GATE,
    ActionType.OPEN_GATE,
    ActionType.CLOSE_GATE_SIMULATED,
}


@dataclass(slots=True)
class GateCommandResult:
    """Resolved outcome for one gate command."""

    gate: Gate | None
    action_type: ActionType
    before_status: GateStatus | None
    after_status: GateStatus | None
    target_resolution: str
    summary: str
    payload: dict[str, Any]


class GateCommandDriver(Protocol):
    """Boundary for gate command execution."""

    async def execute(
        self,
        session: AsyncSession,
        *,
        plan: ActionPlan,
        step: PlanStep,
        actor_name: str,
    ) -> GateCommandResult:
        """Execute a gate command."""


class SimulatedGateCommandDriver:
    """Deterministic PLC-like driver that mutates gate state in the database."""

    async def execute(
        self,
        session: AsyncSession,
        *,
        plan: ActionPlan,
        step: PlanStep,
        actor_name: str,
    ) -> GateCommandResult:
        """Apply a simulated gate state transition for one execution step."""
        if step.action_type not in GATE_ACTION_TYPES:
            raise AppException(
                status_code=HTTPStatus.BAD_REQUEST,
                code="unsupported_gate_action",
                message=f"Action '{step.action_type.value}' is not supported by the gate command driver.",
            )

        gate_repo = GateRepository(session)
        gate, target_resolution = await self._resolve_gate_target(
            gate_repo,
            plan=plan,
            step=step,
        )
        now = datetime.now(UTC)
        if gate is not None:
            before_status = gate.status
            after_status = self._resolve_target_status(step.action_type)

            gate.status = after_status
            gate.last_operated_at = now
            metadata = dict(gate.gate_metadata or {})
            metadata["last_command"] = {
                "action_type": step.action_type.value,
                "step_index": step.step_index,
                "actor_name": actor_name,
                "issued_at": now.isoformat(),
                "target_resolution": target_resolution,
            }
            gate.gate_metadata = metadata
            await session.flush()
        else:
            before_status = None
            after_status = None

        summary = self._build_summary(
            step.action_type,
            gate=gate,
            after_status=after_status,
            target_gate_code=step.target_gate_code,
        )
        payload = {
            "simulated": True,
            "target_resolution": target_resolution,
            "gate": (
                {
                    "id": str(gate.id),
                    "code": gate.code,
                    "name": gate.name,
                    "status_before": before_status.value if before_status is not None else None,
                    "status_after": after_status.value if after_status is not None else None,
                    "station_id": str(gate.station_id) if gate.station_id is not None else None,
                    "station_code": gate.station.code if gate.station is not None else None,
                    "last_operated_at": now.isoformat(),
                }
                if gate is not None
                else None
            ),
            "virtual_gate": None if gate is not None else {
                "target_gate_code": step.target_gate_code,
                "action_type": step.action_type.value,
                "note": "Không tìm thấy gate vật lý; mô phỏng trên thiết bị ảo.",
            },
        }
        return GateCommandResult(
            gate=gate,
            action_type=step.action_type,
            before_status=before_status,
            after_status=after_status,
            target_resolution=target_resolution,
            summary=summary,
            payload=payload,
        )

    async def _resolve_gate_target(
        self,
        gate_repo: GateRepository,
        *,
        plan: ActionPlan,
        step: PlanStep,
    ) -> tuple[Gate | None, str]:
        if step.target_gate_code:
            gate = await gate_repo.get_by_code(step.target_gate_code)
            if gate is not None:
                return gate, "step.target_gate_code"

        station_id = plan.risk_assessment.station_id if plan.risk_assessment is not None else None
        if station_id is not None:
            gate = await gate_repo.get_preferred_for_station(station_id)
            if gate is not None:
                return gate, "plan.risk_assessment.station_id"

        gates = await gate_repo.list_by_region(plan.region_id, limit=1)
        if gates:
            return gates[0], "region_fallback"

        return None, "simulation_only"

    @staticmethod
    def _resolve_target_status(action_type: ActionType) -> GateStatus:
        if action_type is ActionType.OPEN_GATE:
            return GateStatus.OPEN
        if action_type in {ActionType.CLOSE_GATE, ActionType.CLOSE_GATE_SIMULATED}:
            return GateStatus.CLOSED
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="unsupported_gate_action",
            message=f"Action '{action_type.value}' cannot be mapped to a gate state.",
        )

    @staticmethod
    def _build_summary(
        action_type: ActionType,
        *,
        gate: Gate | None,
        after_status: GateStatus | None,
        target_gate_code: str | None,
    ) -> str:
        gate_label = gate.code if gate is not None else (target_gate_code or "thiết bị ảo")
        if action_type is ActionType.OPEN_GATE:
            return (
                f"Mô phỏng mở cống {gate_label} thành công; trạng thái hiện tại: {after_status.value}."
                if after_status is not None
                else f"Mô phỏng mở cống {gate_label} hoàn tất trên thiết bị ảo."
            )
        if action_type in {ActionType.CLOSE_GATE, ActionType.CLOSE_GATE_SIMULATED}:
            return (
                f"Mô phỏng đóng cống {gate_label} thành công; trạng thái hiện tại: {after_status.value}."
                if after_status is not None
                else f"Mô phỏng đóng cống {gate_label} hoàn tất trên thiết bị ảo."
            )
        return f"Mô phỏng thao tác cống {gate_label} hoàn tất."
