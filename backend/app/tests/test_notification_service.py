"""Tests for notification delivery behavior."""

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.models.enums import NotificationChannel, NotificationStatus
from app.schemas.notification import NotificationCreate
from app.services.notification_service import create_notification
from app.services.notify.email import send_email_message
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
        subject="Cảnh báo mặn",
        message="Độ mặn đã vượt ngưỡng.",
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
    assert "Độ mặn đã vượt ngưỡng." in smtp.sent_message.get_content()
    assert "Sự kiện: cảnh báo rủi ro" in smtp.sent_message.get_content()


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
