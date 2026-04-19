"""Consistent API response helpers."""

from datetime import datetime, timezone
import re
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse, ResponseMeta, SuccessResponse


_MESSAGE_MAP: dict[str, str] = {
    "Service is healthy.": "Dịch vụ đang hoạt động bình thường.",
    "Service readiness evaluated.": "Trạng thái sẵn sàng đã được đánh giá.",
    "Mekong-SALT backend is running.": "Backend Mekong-SALT đang chạy.",
    "Dashboard summary retrieved successfully.": "Đã lấy tổng quan dashboard thành công.",
    "Dashboard timeline retrieved successfully.": "Đã lấy dòng thời gian dashboard thành công.",
    "Latest Earth Engine context retrieved successfully.": "Đã lấy ngữ cảnh Earth Engine mới nhất thành công.",
    "Sensor reading ingested successfully.": "Đã ghi nhận dữ liệu cảm biến thành công.",
    "Ingest metrics retrieved successfully.": "Đã lấy số liệu ingest thành công.",
    "Agent runs retrieved successfully.": "Đã lấy danh sách lượt chạy tác tử thành công.",
    "Agent run retrieved successfully.": "Đã lấy lượt chạy tác tử thành công.",
    "Action logs retrieved successfully.": "Đã lấy nhật ký hành động thành công.",
    "Feedback lifecycle evaluation persisted successfully.": "Đã lưu đánh giá vòng đời phản hồi thành công.",
    "Latest feedback lifecycle evaluation retrieved successfully.": "Đã lấy đánh giá vòng đời phản hồi mới nhất thành công.",
    "Audit logs retrieved successfully.": "Đã lấy nhật ký kiểm toán thành công.",
    "Notification sent successfully.": "Đã gửi thông báo thành công.",
    "Notifications retrieved successfully.": "Đã lấy danh sách thông báo thành công.",
    "Notification marked as read successfully.": "Đã đánh dấu thông báo là đã đọc thành công.",
    "Latest risk retrieved successfully.": "Đã lấy rủi ro mới nhất thành công.",
    "No risk assessment has been produced for the requested scope.": "Chưa có đánh giá rủi ro cho phạm vi yêu cầu.",
    "Latest readings retrieved successfully.": "Đã lấy danh sách số liệu đọc mới nhất thành công.",
    "Reading history retrieved successfully.": "Đã lấy lịch sử số liệu đọc thành công.",
    "Plans retrieved successfully.": "Đã lấy danh sách kế hoạch thành công.",
    "Plan retrieved successfully.": "Đã lấy kế hoạch thành công.",
    "Execution batches retrieved successfully.": "Đã lấy danh sách lô thực thi thành công.",
    "Execution batch retrieved successfully.": "Đã lấy lô thực thi thành công.",
    "Execution batch completed successfully.": "Đã hoàn tất lô thực thi thành công.",
    "Action outcomes retrieved successfully.": "Đã lấy kết quả hành động thành công.",
    "Plan decision recorded successfully.": "Đã ghi nhận quyết định kế hoạch thành công.",
    "Approval history retrieved successfully.": "Đã lấy lịch sử phê duyệt thành công.",
    "Incident created successfully.": "Đã tạo sự cố thành công.",
    "Incidents retrieved successfully.": "Đã lấy danh sách sự cố thành công.",
    "Incident retrieved successfully.": "Đã lấy sự cố thành công.",
    "Incident updated successfully.": "Đã cập nhật sự cố thành công.",
    "Monitoring goal created successfully.": "Đã tạo mục tiêu giám sát thành công.",
    "Monitoring goals retrieved successfully.": "Đã lấy danh sách mục tiêu giám sát thành công.",
    "Monitoring goal retrieved successfully.": "Đã lấy mục tiêu giám sát thành công.",
    "Monitoring goal updated successfully.": "Đã cập nhật mục tiêu giám sát thành công.",
    "Monitoring goal deleted successfully.": "Đã xoá mục tiêu giám sát thành công.",
    "Station created successfully.": "Đã tạo trạm thành công.",
    "Stations retrieved successfully.": "Đã lấy danh sách trạm thành công.",
    "Station retrieved successfully.": "Đã lấy trạm thành công.",
    "Station updated successfully.": "Đã cập nhật trạm thành công.",
    "Request validation failed.": "Xác thực yêu cầu thất bại.",
    "Internal server error.": "Lỗi máy chủ nội bộ.",
    "Application error.": "Đã xảy ra lỗi ứng dụng.",
    "Only approved plans can be executed in simulated mode.": "Chỉ các kế hoạch đã được phê duyệt mới có thể thực thi ở chế độ mô phỏng.",
    "Action plan is missing its linked risk assessment.": "Kế hoạch hành động chưa có đánh giá rủi ro liên kết.",
    "Action plan payload is not structurally valid for execution.": "Dữ liệu kế hoạch hành động không hợp lệ về cấu trúc để thực thi.",
    "Action plan failed execution policy validation.": "Kế hoạch hành động không đạt kiểm tra chính sách thực thi.",
    "Runtime configuration must use Gemini provider.": "Cấu hình chạy phải dùng nhà cung cấp Gemini.",
    "Gemini provider requires an injected planner interface.": "Nhà cung cấp Gemini cần được truyền vào planner interface.",
    "station and region filters do not refer to the same region.": "Bộ lọc trạm và vùng không cùng thuộc một khu vực.",
}


_NOT_FOUND_PATTERN = re.compile(r"^(?P<entity>.+) was not found\.$")
_QUOTED_ENTITY_NOT_FOUND_PATTERN = re.compile(
    r"^(?P<label>.+) '(?P<identifier>.+)' was not found\.$"
)
_QUOTED_ENTITY_LABELS: dict[str, str] = {
    "Sensor station": "trạm cảm biến",
    "Region": "khu vực",
    "Action plan": "kế hoạch hành động",
    "Execution batch": "lô thực thi",
    "Agent run": "lượt chạy tác tử",
    "Monitoring goal": "mục tiêu giám sát",
    "Incident": "sự cố",
    "Notification": "thông báo",
    "Knowledge source": "nguồn tri thức",
}


def translate_api_message(message: str) -> str:
    """Translate common API messages to Vietnamese for FE responses."""
    translated = _MESSAGE_MAP.get(message)
    if translated is not None:
        return translated

    match = _QUOTED_ENTITY_NOT_FOUND_PATTERN.match(message)
    if match:
        label = match.group("label")
        translated_label = _QUOTED_ENTITY_LABELS.get(label, label)
        return f"Không tìm thấy {translated_label} '{match.group('identifier')}'."

    match = _NOT_FOUND_PATTERN.match(message)
    if match:
        entity = match.group("entity")
        return f"Không tìm thấy {entity}."

    if message.endswith("retrieved successfully."):
        entity = message.removesuffix(" retrieved successfully.")
        return f"Đã lấy {entity.lower()} thành công."

    if message.endswith("created successfully."):
        entity = message.removesuffix(" created successfully.")
        return f"Đã tạo {entity.lower()} thành công."

    if message.endswith("updated successfully."):
        entity = message.removesuffix(" updated successfully.")
        return f"Đã cập nhật {entity.lower()} thành công."

    if message.endswith("deleted successfully."):
        entity = message.removesuffix(" deleted successfully.")
        return f"Đã xoá {entity.lower()} thành công."

    return message


def _build_meta(request: Request | None) -> ResponseMeta:
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)

    return ResponseMeta(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc),
    )


def success_response(
    *,
    request: Request | None,
    message: str,
    data: Any = None,
    status_code: int = 200,
) -> JSONResponse:
    """Build a successful API response envelope."""
    payload = SuccessResponse[Any](
        message=translate_api_message(message),
        data=data,
        meta=_build_meta(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def error_response(
    *,
    request: Request | None,
    status_code: int,
    message: str,
    code: str,
    details: Any | None = None,
) -> JSONResponse:
    """Build a failed API response envelope."""
    # RequestValidationError may include raw Exception objects in context.
    safe_details = jsonable_encoder(
        details,
        custom_encoder={Exception: lambda exc: str(exc)},
    )

    payload = ErrorResponse(
        message=translate_api_message(message),
        error=ErrorDetail(code=code, details=safe_details),
        meta=_build_meta(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))

