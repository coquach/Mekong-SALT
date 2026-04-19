"""LLM provider abstractions for agent planning."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.schemas.agent import GeneratedActionPlan
from app.services.llm import PlannerInterface


logger = logging.getLogger(__name__)


class PlanProvider(ABC):
    """Base interface for planning providers."""

    name: str

    @abstractmethod
    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a structured plan for the given objective and context."""


class MockProvider(PlanProvider):
    """Deterministic planner for local demos and tests."""

    name = "mock"

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a structured plan without calling an external LLM."""
        assessment = context.get("assessment") or {}
        target_gate_code = _resolve_gate_target_code(context)
        risk_level = assessment.get("risk_level", "warning")
        trend_direction = assessment.get("trend_direction")
        if risk_level == "critical":
            mitigation_action = "close_gate"
        elif risk_level == "danger" and trend_direction == "falling":
            mitigation_action = "open_gate"
        elif risk_level == "danger":
            mitigation_action = "close_gate"
        elif trend_direction == "falling":
            mitigation_action = "open_gate"
        else:
            mitigation_action = "send_alert"

        if mitigation_action == "open_gate":
            mitigation_title = (
                f"Mô phỏng thao tác mở cống {target_gate_code}"
                if target_gate_code
                else "Mô phỏng thao tác mở cống"
            )
            mitigation_instructions = (
                f"Gửi lệnh mô phỏng mở cống tới {target_gate_code} và ghi nhận trạng thái trước/sau."
                if target_gate_code
                else "Gửi lệnh mô phỏng mở cống và ghi nhận trạng thái trước/sau."
            )
            mitigation_rationale = (
                "Xu hướng độ mặn đang giảm nên cần mô phỏng mở cổng để phục hồi khả năng lấy nước an toàn."
            )
            follow_up_step = {
                "step_index": 3,
                "action_type": "wait-safe-window",
                "priority": 3,
                "title": "Theo dõi sau khi mở cống",
                "instructions": "Giữ cống ở trạng thái mở mô phỏng và theo dõi thêm một chu kỳ đo để xác nhận độ mặn tiếp tục giảm.",
                "rationale": "Sau khi mở cống cần quan sát thêm để bảo đảm cửa an toàn duy trì ổn định.",
                "simulated": True,
            }
        else:
            mitigation_title = (
                f"Mô phỏng thao tác cống {target_gate_code}"
                if target_gate_code and mitigation_action in {"close_gate", "open_gate"}
                else "Mô phỏng biện pháp thủy lực"
            )
            mitigation_instructions = (
                f"Gửi lệnh mô phỏng tới cống {target_gate_code} và ghi nhận trạng thái trước/sau."
                if target_gate_code and mitigation_action in {"close_gate", "open_gate"}
                else "Chạy luồng thực thi mô phỏng và ghi nhận kết quả."
            )
            mitigation_rationale = (
                "MVP phải giữ ở chế độ mô phỏng cho đến khi vận hành phê duyệt tích hợp thiết bị."
                if not target_gate_code
                else "Lệnh cống cần target_gate_code để driver mô phỏng có thể ánh xạ đúng thiết bị đầu ra."
            )
            follow_up_step = {
                "step_index": 3,
                "action_type": "stop_pump",
                "priority": 3,
                "title": "Xác nhận tạm dừng lấy nước an toàn",
                "instructions": "Mô phỏng dừng bơm tạm thời nếu độ mặn đầu vào vẫn cao.",
                "rationale": "Tạm dừng lấy nước có kiểm soát có thể giảm phơi nhiễm trong các đỉnh độ mặn.",
                "simulated": True,
            }
        return GeneratedActionPlan.model_validate(
            {
                "objective": objective,
                "summary": (
                    "Phối hợp ứng phó độ mặn và chờ phê duyệt của vận hành trước khi thực hiện thao tác mô phỏng. "
                    "Tóm tắt này nêu rõ bối cảnh rủi ro hiện tại, các tín hiệu quan trắc chính và bước giảm thiểu dự kiến để người vận hành nắm nhanh trước khi duyệt."
                ),
                "context_summary": "Ngữ cảnh từ cảm biến, thời tiết và quy tắc đã được tổng hợp cho sự cố.",
                "risk_summary": assessment.get("summary", "Rủi ro độ mặn cần được vận hành xem xét."),
                "confidence_score": 0.76,
                "assumptions": [
                    "Dữ liệu cảm biến còn đủ mới cho việc lập kế hoạch MVP.",
                    "Mọi hành động thiết bị đều được mô phỏng và cần phê duyệt của con người.",
                ],
                "reasoning_summary": "Mức rủi ro và xu hướng gần đây cho thấy cần gửi cảnh báo sớm và mô phỏng biện pháp giảm thiểu.",
                "steps": [
                    {
                        "step_index": 1,
                        "action_type": "send_alert",
                        "priority": 1,
                        "title": "Gửi cảnh báo cho vận hành và nông dân",
                        "instructions": "Thông báo qua dashboard, SMS mô phỏng, Zalo mô phỏng và email mô phỏng.",
                        "rationale": "Các bên liên quan cần nhận cảnh báo ngay trước khi thay đổi hành vi lấy nước.",
                        "simulated": True,
                    },
                    {
                        "step_index": 2,
                        "action_type": mitigation_action,
                        "priority": 2,
                        "title": mitigation_title,
                        "instructions": mitigation_instructions,
                        "rationale": mitigation_rationale,
                        "target_gate_code": target_gate_code,
                        "simulated": True,
                    },
                    follow_up_step,
                ],
            }
        )


def _resolve_gate_target_code(context: dict[str, Any]) -> str | None:
    """Resolve a stable gate code from planning context for gate actions."""
    recommended = context.get("recommended_gate_target")
    if isinstance(recommended, dict):
        code = recommended.get("code")
        if isinstance(code, str) and code:
            return code

    code = context.get("recommended_gate_target_code")
    if isinstance(code, str) and code:
        return code

    gates = context.get("gate_targets")
    if isinstance(gates, list):
        for gate in gates:
            if isinstance(gate, dict):
                code = gate.get("code")
                if isinstance(code, str) and code:
                    return code

    return None

class GeminiProvider(PlanProvider):
    """Compatibility shim delegating Gemini planning to LLM service adapter."""

    name = "gemini"

    def __init__(self, *, planner: PlannerInterface) -> None:
        self._planner = planner
        self._fallback = MockProvider()

    async def generate_plan(
        self,
        *,
        objective: str,
        context: dict[str, Any],
    ) -> GeneratedActionPlan:
        """Generate a plan via centralized LLM adapter boundary."""
        try:
            return await self._planner.generate_plan(objective=objective, context=context)
        except AppException as exc:
            if exc.code not in {
                "gemini_generation_failed",
                "gemini_empty_response",
                "gemini_invalid_plan_payload",
                "vertex_client_init_failed",
                "vertex_project_missing",
            }:
                raise
            logger.warning(
                "Gemini planning unavailable; using deterministic fallback",
                extra={"error_code": exc.code, "error_message": exc.message},
            )
            return await self._fallback.generate_plan(objective=objective, context=context)


def get_plan_provider(
    provider_name: str | None = None,
    *,
    planner: PlannerInterface | None = None,
) -> PlanProvider:
    """Resolve the configured planning provider implementation."""
    _ = provider_name
    settings = get_settings()
    if settings.llm_provider != "gemini":
        raise AppException(
            status_code=500,
            code="invalid_llm_provider_configuration",
            message="Runtime configuration must use Gemini provider.",
        )
    if planner is None:
        raise AppException(
            status_code=500,
            code="planner_interface_missing",
            message="Gemini provider requires an injected planner interface.",
        )
    return GeminiProvider(planner=planner)
