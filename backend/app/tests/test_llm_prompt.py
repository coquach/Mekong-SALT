"""Tests for planning prompt and local fallback language behavior."""

from __future__ import annotations

import pytest

from app.agents.providers import MockProvider
from app.services.llm.vertex_planner import build_plan_prompt


def test_build_plan_prompt_requests_vietnamese_human_readable_fields() -> None:
    prompt = build_plan_prompt(
        objective="Bảo vệ chất lượng nước tưới",
        context={"region": {"code": "TG-01"}},
    )

    assert "Return all human-readable fields in Vietnamese" in prompt
    assert "Keep JSON keys and action_type values in English." in prompt


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