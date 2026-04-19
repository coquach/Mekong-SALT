"""Tests for notification delivery behavior."""

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.models.enums import NotificationChannel, NotificationStatus
from app.schemas.notification import NotificationCreate
from app.services.notification_service import create_notification, create_operational_notifications, list_notifications
from app.services.agent_execution_service import _build_execution_summary_notification_message
from app.services.notify.email import build_email_text, send_email_message
from app.services.notify.zalo import ZaloDeliveryResult, build_zalo_template_data, build_zalo_text


@pytest.mark.asyncio
async def test_create_notification_uses_zalo_template_delivery_when_enabled(
    db_session,
    monkeypatch,
):
    sent_messages: list[dict[str, object]] = []

    async def fake_send_zalo_template_message(**kwargs):
        sent_messages.append(kwargs)
        return ZaloDeliveryResult(
            ok=True,
            status_code=200,
            message_id="msg-123",
            response_payload={"data": {"message_id": "msg-123"}},
        )

    fake_settings = SimpleNamespace(
        zalo_notifications_enabled=True,
        zalo_delivery_mode="template",
        zalo_oa_access_token=SecretStr("token-123"),
        zalo_oa_recipient_phone_number="0987654321",
        zalo_oa_template_id="tmpl-123",
        zalo_oa_template_message_endpoint="https://example.test/zalo/template",
        zalo_oa_timeout_seconds=7,
    )

    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: fake_settings)
    monkeypatch.setattr(
        "app.services.notification_service.send_zalo_template_message",
        fake_send_zalo_template_message,
    )

    notification = await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.ZALO_MOCK,
            recipient="zalo-operator-group",
            subject="Cảnh báo mặn tăng",
            message="Độ mặn đã vượt ngưỡng cảnh báo.",
            payload={"event": "risk_alert", "station_code": "TG-01"},
        ),
    )
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.status is NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.payload is not None
    assert notification.payload["delivery"]["mode"] == "template"
    assert notification.payload["delivery"]["provider"] == "zalo"
    assert notification.payload["delivery"]["message_id"] == "msg-123"
    assert sent_messages[0]["recipient_phone_number"] == "0987654321"
    assert sent_messages[0]["template_id"] == "tmpl-123"
    assert sent_messages[0]["endpoint"] == "https://example.test/zalo/template"
    assert sent_messages[0]["payload"]["event"] == "risk_alert"
    assert sent_messages[0]["payload"]["station_code"] == "TG-01"


@pytest.mark.asyncio
async def test_create_notification_falls_back_to_mock_when_zalo_disabled(
    db_session,
    monkeypatch,
):
    called = False

    async def fake_send_zalo_template_message(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("Zalo template sender should not be called when disabled.")

    fake_settings = SimpleNamespace(
        zalo_notifications_enabled=False,
        zalo_oa_access_token=None,
        zalo_oa_recipient_phone_number=None,
        zalo_oa_template_id=None,
        zalo_oa_template_message_endpoint="https://example.test/zalo/template",
        zalo_oa_timeout_seconds=7,
    )

    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: fake_settings)
    monkeypatch.setattr(
        "app.services.notification_service.send_zalo_template_message",
        fake_send_zalo_template_message,
    )

    notification = await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.ZALO_MOCK,
            recipient="zalo-operator-group",
            subject="Thông báo mô phỏng",
            message="Tin nhắn này chỉ là mock.",
            payload={"event": "demo"},
        ),
    )
    await db_session.commit()
    await db_session.refresh(notification)

    assert called is False
    assert notification.status is NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.payload is not None
    assert notification.payload["event"] == "demo"
    assert notification.payload["delivery"]["mode"] == "mock"


@pytest.mark.asyncio
async def test_create_notification_uses_email_delivery_when_enabled(
    db_session,
    monkeypatch,
):
    sent_messages: list[dict[str, object]] = []

    async def fake_send_email_message(**kwargs):
        sent_messages.append(kwargs)
        return SimpleNamespace(
            ok=True,
            message_id="<msg-456>",
            smtp_response="sent",
            error_message=None,
        )

    fake_settings = SimpleNamespace(
        email_notifications_enabled=True,
        email_smtp_host="smtp.example.test",
        email_smtp_port=587,
        email_smtp_username="ops@example.test",
        email_smtp_password=SecretStr("smtp-secret"),
        email_from_address="ops@example.test",
        email_use_tls=True,
        email_use_ssl=False,
        email_timeout_seconds=7,
        zalo_notifications_enabled=False,
    )

    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: fake_settings)
    monkeypatch.setattr(
        "app.services.notification_service.send_email_message",
        fake_send_email_message,
    )

    notification = await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.EMAIL_MOCK,
            recipient="ops@example.test",
            subject="Cảnh báo mặn tăng",
            message="Độ mặn đã vượt ngưỡng cảnh báo.",
            payload={"event": "risk_alert", "station_code": "TG-01"},
        ),
    )
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.status is NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.payload is not None
    assert notification.payload["delivery"]["mode"] == "smtp"
    assert notification.payload["delivery"]["provider"] == "email"
    assert notification.payload["delivery"]["message_id"] == "<msg-456>"
    assert sent_messages[0]["from_address"] == "ops@example.test"
    assert sent_messages[0]["recipient_email"] == "ops@example.test"
    assert sent_messages[0]["payload"]["event"] == "risk_alert"


@pytest.mark.asyncio
async def test_send_email_message_builds_and_sends_plain_text_email(monkeypatch):
    instances: list[SimpleNamespace] = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.starttls_called = False
            self.login_args = None
            self.sent_message = None
            instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def ehlo(self):
            return None

        def starttls(self, context=None):
            self.starttls_called = True
            self.tls_context = context

        def login(self, username, password):
            self.login_args = (username, password)

        def send_message(self, email_message):
            self.sent_message = email_message
            return {}

    monkeypatch.setattr("app.services.notify.email.smtplib.SMTP", FakeSMTP)

    result = await send_email_message(
        smtp_host="smtp.example.test",
        smtp_port=587,
        from_address="ops@example.test",
        recipient_email="farmer@example.test",
        subject="C???nh b??o m???n",
        message="????? m???n ???? v?????t ng?????ng.",
        payload={"event": "risk_alert", "severity": "critical"},
        smtp_username="ops@example.test",
        smtp_password="smtp-secret",
        use_tls=True,
        use_ssl=False,
        timeout_seconds=5,
    )

    assert result.ok is True
    assert result.message_id is not None
    assert len(instances) == 1
    smtp = instances[0]
    assert smtp.host == "smtp.example.test"
    assert smtp.port == 587
    assert smtp.starttls_called is True
    assert smtp.login_args == ("ops@example.test", "smtp-secret")
    assert smtp.sent_message["To"] == "farmer@example.test"
    assert smtp.sent_message["From"] == "ops@example.test"
    assert smtp.sent_message.is_multipart() is True

    plain_part = smtp.sent_message.get_body(preferencelist=("plain",))
    html_part = smtp.sent_message.get_body(preferencelist=("html",))

    assert plain_part is not None
    assert html_part is not None
    assert "Tiêu đề: Cảnh báo mặn" in plain_part.get_content()
    assert "Nội dung: Độ mặn đã vượt ngưỡng." in plain_part.get_content()
    assert "Sự kiện: cảnh báo rủi ro" in plain_part.get_content()
    assert "Chi tiết:" in plain_part.get_content()
    assert "<html" in html_part.get_content().lower()
    assert "Cảnh báo mặn" in html_part.get_content()


def test_build_zalo_template_data_localizes_common_labels():
    data = build_zalo_template_data(
        "Cảnh báo mặn tăng",
        "Độ mặn đã vượt ngưỡng cảnh báo.",
        payload={"event": "risk_alert", "severity": "critical", "station_code": "TG-01"},
    )

    assert data["event"] == "cảnh báo rủi ro"
    assert data["severity"] == "khẩn cấp"
    assert data["subject"] == "Cảnh báo mặn tăng"


def test_build_zalo_text_localizes_common_labels():
    text = build_zalo_text(
        "Cảnh báo mặn tăng",
        "Độ mặn đã vượt ngưỡng cảnh báo.",
        payload={"event": "risk_alert", "severity": "critical", "station_code": "TG-01"},
    )

    assert "Sự kiện: cảnh báo rủi ro" in text
    assert "Mức độ: khẩn cấp" in text
    assert "Trạm: TG-01" in text


def test_build_email_text_humanizes_execution_summary():
    text = build_email_text(
        "Tổng kết thực thi",
        "Tổng kết thực thi: success",
        payload={
            "event": "execution_summary",
            "outcome_class": "success",
            "action_summary": "Đã đóng cống mô phỏng và dừng bơm",
            "action_plan_id": "plan-123",
            "execution_batch_id": "batch-456",
            "replan_recommended": False,
        },
    )

    assert "Tóm tắt:" in text
    assert "Mô phỏng đã hoàn tất." in text
    assert "Kết quả: thành công" in text
    assert "Hành động chính: Đã đóng cống mô phỏng và dừng bơm" in text
    assert "Diễn giải: Luồng phản ứng đã đi đúng thứ tự" in text
    assert "Diễn giải ngắn:" not in text
    assert "plan-123" not in text
    assert "batch-456" not in text


def test_build_email_text_keeps_execution_summary_concise_when_inconclusive():
    text = build_email_text(
        "Tổng kết thực thi",
        "Tổng kết thực thi: inconclusive",
        payload={
            "event": "execution_summary",
            "outcome_class": "inconclusive",
            "action_summary": "Đã gửi cảnh báo mô phỏng tới các bên liên quan -> Đóng cống mô phỏng",
            "replan_recommended": True,
        },
    )

    assert "Kết quả: chưa đủ dữ liệu để kết luận" in text
    assert "Diễn giải: Quy trình đã chạy xong, nhưng cần thêm dữ liệu để xác nhận hiệu quả cuối cùng." in text
    assert "Khuyến nghị: xem xét lập lại kế hoạch để an toàn hơn" in text
    assert "Hành động chính: Đã gửi cảnh báo mô phỏng tới các bên liên quan; Đóng cống mô phỏng" in text
    assert "Điều này chứng minh" not in text
    assert "Các bước chính" not in text


def test_build_zalo_text_humanizes_execution_summary():
    text = build_zalo_text(
        "Tổng kết thực thi",
        "Tổng kết thực thi: success",
        payload={
            "event": "execution_summary",
            "outcome_class": "success",
            "action_summary": "Đã đóng cống mô phỏng và dừng bơm",
            "replan_recommended": False,
        },
    )

    assert "Diễn giải ngắn: Kết quả mô phỏng: thành công." in text
    assert "Các bước chính: Đã đóng cống mô phỏng và dừng bơm." in text
    assert "Điều này cho thấy hệ thống đã phản ứng đúng trình tự" in text
    assert "giảm nguy cơ lan rộng của salinity" in text
    assert "tạo ra một phản ứng có tổ chức" in text


def test_execution_summary_message_is_plain_language():
    message = _build_execution_summary_notification_message(
        plan=SimpleNamespace(objective="Bảo vệ chất lượng nước tưới"),
        feedback=SimpleNamespace(outcome_class="success", replan_recommended=False),
        executions=[
            SimpleNamespace(result_summary="Đã chấp nhận lệnh đóng cống mô phỏng."),
            SimpleNamespace(result_summary="Đã gửi cảnh báo mô phỏng tới các bên liên quan."),
        ],
    )

    assert message.startswith("Hệ thống đã hoàn tất mô phỏng")
    assert "Kết quả mô phỏng: thành công." in message
    assert "Các bước đã thực hiện:" in message
    assert "Đánh giá sự việc" not in message
    assert "Phương án xử lý" not in message
    assert "Kế hoạch" not in message


@pytest.mark.asyncio
async def test_create_notification_skips_duplicate_dedupe_key(
    db_session,
    monkeypatch,
):
    send_count = 0

    async def fake_send_email_message(**kwargs):
        nonlocal send_count
        send_count += 1
        return SimpleNamespace(
            ok=True,
            message_id="<msg-dup>",
            smtp_response="sent",
            error_message=None,
        )

    fake_settings = SimpleNamespace(
        email_notifications_enabled=True,
        email_smtp_host="smtp.example.test",
        email_smtp_port=587,
        email_smtp_username="ops@example.test",
        email_smtp_password=SecretStr("smtp-secret"),
        email_from_address="ops@example.test",
        email_use_tls=True,
        email_use_ssl=False,
        email_timeout_seconds=7,
        zalo_notifications_enabled=False,
    )

    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: fake_settings)
    monkeypatch.setattr(
        "app.services.notification_service.send_email_message",
        fake_send_email_message,
    )

    first = await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.EMAIL_MOCK,
            recipient="ops@example.test",
            subject="Cảnh báo mặn tăng",
            message="Độ mặn đã vượt ngưỡng cảnh báo.",
            payload={"event": "risk_alert", "dedupe_key": "execution-summary-001"},
        ),
    )
    await db_session.commit()

    second = await create_notification(
        db_session,
        NotificationCreate(
            channel=NotificationChannel.EMAIL_MOCK,
            recipient="ops@example.test",
            subject="Cảnh báo mặn tăng",
            message="Độ mặn đã vượt ngưỡng cảnh báo.",
            payload={"event": "risk_alert", "dedupe_key": "execution-summary-001"},
        ),
    )
    await db_session.commit()

    assert send_count == 1
    assert first.id == second.id


@pytest.mark.asyncio
async def test_create_operational_notifications_persists_email_delivery(
    db_session,
    monkeypatch,
):
    sent_messages: list[dict[str, object]] = []

    async def fake_send_email_message(**kwargs):
        sent_messages.append(kwargs)
        return SimpleNamespace(
            ok=True,
            message_id="<msg-operational>",
            smtp_response="sent",
            error_message=None,
        )

    fake_settings = SimpleNamespace(
        email_notifications_enabled=True,
        email_smtp_host="smtp.example.test",
        email_smtp_port=587,
        email_smtp_username="ops@example.test",
        email_smtp_password=SecretStr("smtp-secret"),
        email_from_address="ops@example.test",
        email_use_tls=True,
        email_use_ssl=False,
        email_timeout_seconds=7,
        zalo_notifications_enabled=False,
    )

    monkeypatch.setattr("app.services.notification_service.get_settings", lambda: fake_settings)
    monkeypatch.setattr(
        "app.services.notification_service.send_email_message",
        fake_send_email_message,
    )

    notifications = await create_operational_notifications(
        db_session,
        incident_id=None,
        subject="Thông báo điều hành",
        message="Đây là thông báo điều hành.",
        payload={"event": "incident_created", "dedupe_key": "operational-001"},
        channel_recipients=(
            (NotificationChannel.DASHBOARD, "dashboard"),
            (NotificationChannel.EMAIL_MOCK, "ops@example.test"),
        ),
    )
    await db_session.commit()

    notifications_on_disk = await list_notifications(db_session, limit=20)

    assert len(notifications) == 2
    assert {notification.channel for notification in notifications} == {
        NotificationChannel.DASHBOARD,
        NotificationChannel.EMAIL_MOCK,
    }
    assert len(sent_messages) == 1
    assert sent_messages[0]["recipient_email"] == "ops@example.test"
    assert {notification.channel for notification in notifications_on_disk} == {
        NotificationChannel.DASHBOARD,
        NotificationChannel.EMAIL_MOCK,
    }
