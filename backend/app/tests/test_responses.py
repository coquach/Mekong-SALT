"""Tests for API response localization helpers."""

import pytest

from app.core.responses import translate_api_message


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Service is healthy.", "Dịch vụ đang hoạt động bình thường."),
        ("Dashboard summary retrieved successfully.", "Đã lấy tổng quan dashboard thành công."),
        (
            "Sensor station 'station-01' was not found.",
            "Không tìm thấy trạm cảm biến 'station-01'.",
        ),
        (
            "Action plan 'plan-123' was not found.",
            "Không tìm thấy kế hoạch hành động 'plan-123'.",
        ),
        (
            "Monitoring goal 'goal-456' was not found.",
            "Không tìm thấy mục tiêu giám sát 'goal-456'.",
        ),
        ("Widget was not found.", "Không tìm thấy Widget."),
    ],
)
def test_translate_api_message(message: str, expected: str) -> None:
    assert translate_api_message(message) == expected