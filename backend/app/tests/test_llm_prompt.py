"""Tests for planning prompt and local fallback language behavior."""

from __future__ import annotations

import pytest

from app.agents.providers import MockProvider
from app.models.enums import ActionType
from app.services.llm.vertex_planner import build_plan_prompt


def test_build_plan_prompt_requests_vietnamese_human_readable_fields() -> None:
    prompt = build_plan_prompt(
        objective="Bảo vệ chất lượng nước tưới",
        context={"region": {"code": "TG-01"}},
    )

    assert "Use only information present in the Context." in prompt
    assert "Return all human-readable fields in Vietnamese" in prompt
    assert "Prefer a direct mitigation step when risk is danger or critical." in prompt
    assert "prefer open_gate for a danger-level plan" in prompt
    assert "Keep JSON keys and action_type values in English." in prompt
    assert "Make summary 2 to 4 Vietnamese sentences" in prompt
    assert "Avoid one-line boilerplate." in prompt


@pytest.mark.asyncio
async def test_mock_provider_returns_vietnamese_plan_text() -> None:
    provider = MockProvider()

    plan = await provider.generate_plan(
        objective="Bảo vệ chất lượng nước tưới",
        context={"assessment": {"risk_level": "critical", "summary": "Rủi ro cao"}},
    )

    assert plan.summary.startswith("Phối hợp ứng phó độ mặn")
    assert plan.context_summary.startswith("Ngữ cảnh từ cảm biến")
    assert plan.steps[0].title == "Gửi cảnh báo cho vận hành và nông dân"
    assert plan.steps[1].instructions == "Chạy luồng thực thi mô phỏng và ghi nhận kết quả."


@pytest.mark.asyncio
async def test_mock_provider_prefers_open_gate_when_salinity_is_falling() -> None:
    provider = MockProvider()

    plan = await provider.generate_plan(
        objective="Phục hồi lấy nước khi độ mặn giảm",
        context={
            "assessment": {
                "risk_level": "danger",
                "trend_direction": "falling",
                "summary": "Độ mặn đang giảm nhưng vẫn trong band cần giám sát.",
            },
            "recommended_gate_target_code": "GATE-RECOVERY-01",
        },
    )

    assert plan.steps[1].action_type == ActionType.OPEN_GATE
    assert plan.steps[1].target_gate_code == "GATE-RECOVERY-01"
    assert plan.steps[2].action_type == ActionType.WAIT_SAFE_WINDOW