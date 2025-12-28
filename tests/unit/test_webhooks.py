"""Unit tests for Webhook system.

Sprint 5.6 - Webhooks System

Tests cover:
- WebhookEvent and WebhookStatus enums
- WebhookSubscription model methods
- WebhookDelivery model methods
- Webhook schemas validation
- HMAC signature generation
"""

import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.models.webhook import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEvent,
    WebhookStatus,
    WebhookSubscription,
)
from src.schemas.webhook import (
    DeliveryListResponse,
    DeliveryResponse,
    DeliveryStatusEnum,
    WebhookCreate,
    WebhookEventEnum,
    WebhookListResponse,
    WebhookResponse,
    WebhookSecretResponse,
    WebhookStatsResponse,
    WebhookStatusEnum,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)


class TestWebhookEventEnum:
    """Tests for WebhookEvent enum."""

    def test_subscription_created(self):
        """Test subscription.created event value."""
        assert WebhookEvent.SUBSCRIPTION_CREATED.value == "subscription.created"

    def test_subscription_updated(self):
        """Test subscription.updated event value."""
        assert WebhookEvent.SUBSCRIPTION_UPDATED.value == "subscription.updated"

    def test_subscription_deleted(self):
        """Test subscription.deleted event value."""
        assert WebhookEvent.SUBSCRIPTION_DELETED.value == "subscription.deleted"

    def test_payment_due(self):
        """Test payment.due event value."""
        assert WebhookEvent.PAYMENT_DUE.value == "payment.due"

    def test_payment_overdue(self):
        """Test payment.overdue event value."""
        assert WebhookEvent.PAYMENT_OVERDUE.value == "payment.overdue"

    def test_payment_completed(self):
        """Test payment.completed event value."""
        assert WebhookEvent.PAYMENT_COMPLETED.value == "payment.completed"

    def test_payment_skipped(self):
        """Test payment.skipped event value."""
        assert WebhookEvent.PAYMENT_SKIPPED.value == "payment.skipped"

    def test_budget_alert(self):
        """Test budget.alert event value."""
        assert WebhookEvent.BUDGET_ALERT.value == "budget.alert"

    def test_import_completed(self):
        """Test import.completed event value."""
        assert WebhookEvent.IMPORT_COMPLETED.value == "import.completed"

    def test_calendar_synced(self):
        """Test calendar.synced event value."""
        assert WebhookEvent.CALENDAR_SYNCED.value == "calendar.synced"

    def test_all_events_present(self):
        """Test all expected events are defined."""
        expected = [
            "subscription.created",
            "subscription.updated",
            "subscription.deleted",
            "payment.due",
            "payment.overdue",
            "payment.completed",
            "payment.skipped",
            "budget.alert",
            "import.completed",
            "calendar.synced",
        ]
        actual = [e.value for e in WebhookEvent]
        for event in expected:
            assert event in actual


class TestWebhookStatusEnum:
    """Tests for WebhookStatus enum."""

    def test_active_status(self):
        """Test active status value."""
        assert WebhookStatus.ACTIVE.value == "active"

    def test_paused_status(self):
        """Test paused status value."""
        assert WebhookStatus.PAUSED.value == "paused"

    def test_disabled_status(self):
        """Test disabled status value."""
        assert WebhookStatus.DISABLED.value == "disabled"

    def test_deleted_status(self):
        """Test deleted status value."""
        assert WebhookStatus.DELETED.value == "deleted"


class TestDeliveryStatusEnum:
    """Tests for DeliveryStatus enum."""

    def test_pending_status(self):
        """Test pending status value."""
        assert DeliveryStatus.PENDING.value == "pending"

    def test_success_status(self):
        """Test success status value."""
        assert DeliveryStatus.SUCCESS.value == "success"

    def test_failed_status(self):
        """Test failed status value."""
        assert DeliveryStatus.FAILED.value == "failed"

    def test_retrying_status(self):
        """Test retrying status value."""
        assert DeliveryStatus.RETRYING.value == "retrying"


class TestWebhookSubscriptionModel:
    """Tests for WebhookSubscription model."""

    def test_create_webhook(self):
        """Test creating a webhook with required fields."""
        user_id = str(uuid4())
        webhook = WebhookSubscription(
            user_id=user_id,
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["payment.due", "payment.overdue"],
            status=WebhookStatus.ACTIVE,
            is_active=True,
            consecutive_failures=0,
            max_failures=5,
        )
        assert webhook.user_id == user_id
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == ["payment.due", "payment.overdue"]
        assert webhook.status == WebhookStatus.ACTIVE
        assert webhook.is_active is True

    def test_default_max_failures(self):
        """Test default max_failures value."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            max_failures=5,  # Explicit for unit test
        )
        assert webhook.max_failures == 5

    def test_regenerate_secret(self):
        """Test secret regeneration."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            secret="old_secret",
        )
        old_secret = webhook.secret
        new_secret = webhook.regenerate_secret()
        assert new_secret != old_secret
        assert len(new_secret) == 64  # 32 bytes hex = 64 chars
        assert webhook.secret == new_secret

    def test_record_success(self):
        """Test recording successful delivery."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            consecutive_failures=3,
            last_failure_reason="Previous error",
        )
        webhook.record_success()
        assert webhook.consecutive_failures == 0
        assert webhook.last_success_at is not None
        assert webhook.last_triggered_at is not None
        assert webhook.last_failure_reason is None

    def test_record_failure(self):
        """Test recording failed delivery."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            consecutive_failures=0,
            max_failures=5,
            status=WebhookStatus.ACTIVE,
            is_active=True,
        )
        webhook.record_failure("Connection timeout")
        assert webhook.consecutive_failures == 1
        assert webhook.last_failure_at is not None
        assert webhook.last_failure_reason == "Connection timeout"
        assert webhook.status == WebhookStatus.ACTIVE  # Not disabled yet

    def test_auto_disable_after_max_failures(self):
        """Test auto-disable after max failures."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            consecutive_failures=4,
            max_failures=5,
            status=WebhookStatus.ACTIVE,
            is_active=True,
        )
        webhook.record_failure("Final failure")
        assert webhook.consecutive_failures == 5
        assert webhook.status == WebhookStatus.DISABLED
        assert webhook.is_active is False

    def test_pause_webhook(self):
        """Test pausing a webhook."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            status=WebhookStatus.ACTIVE,
            is_active=True,
        )
        webhook.pause()
        assert webhook.status == WebhookStatus.PAUSED
        assert webhook.is_active is False

    def test_resume_webhook(self):
        """Test resuming a paused webhook."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            status=WebhookStatus.PAUSED,
            is_active=False,
            consecutive_failures=3,
        )
        webhook.resume()
        assert webhook.status == WebhookStatus.ACTIVE
        assert webhook.is_active is True
        assert webhook.consecutive_failures == 0  # Reset on resume

    def test_subscribes_to_event_string(self):
        """Test checking event subscription with string."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due", "payment.overdue"],
        )
        assert webhook.subscribes_to("payment.due") is True
        assert webhook.subscribes_to("payment.overdue") is True
        assert webhook.subscribes_to("subscription.created") is False

    def test_subscribes_to_event_enum(self):
        """Test checking event subscription with enum."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due", "payment.overdue"],
        )
        assert webhook.subscribes_to(WebhookEvent.PAYMENT_DUE) is True
        assert webhook.subscribes_to(WebhookEvent.SUBSCRIPTION_CREATED) is False

    def test_get_headers_dict_empty(self):
        """Test getting headers when none set."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            headers=None,
        )
        assert webhook.get_headers_dict() == {}

    def test_get_headers_dict_valid(self):
        """Test getting headers from JSON string."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            headers='{"X-Custom": "value", "Authorization": "Bearer token"}',
        )
        headers = webhook.get_headers_dict()
        assert headers == {"X-Custom": "value", "Authorization": "Bearer token"}

    def test_get_headers_dict_invalid_json(self):
        """Test getting headers with invalid JSON."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            headers="invalid json",
        )
        assert webhook.get_headers_dict() == {}

    def test_set_headers(self):
        """Test setting headers from dict."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
        )
        webhook.set_headers({"X-Custom": "value"})
        assert webhook.headers == '{"X-Custom": "value"}'
        assert webhook.get_headers_dict() == {"X-Custom": "value"}

    def test_set_headers_none(self):
        """Test setting empty headers."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            headers='{"old": "header"}',
        )
        webhook.set_headers({})
        assert webhook.headers is None

    def test_repr(self):
        """Test string representation."""
        webhook = WebhookSubscription(
            user_id=str(uuid4()),
            name="Test Webhook",
            url="https://example.com/very/long/path/to/webhook/endpoint",
            events=["payment.due"],
            status=WebhookStatus.ACTIVE,
        )
        repr_str = repr(webhook)
        assert "WebhookSubscription" in repr_str
        assert "Test Webhook" in repr_str
        assert "active" in repr_str


class TestWebhookDeliveryModel:
    """Tests for WebhookDelivery model."""

    def test_create_delivery(self):
        """Test creating a delivery record."""
        webhook_id = str(uuid4())
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.PENDING,
            attempt_number=1,
            max_attempts=3,
        )
        assert delivery.webhook_id == webhook_id
        assert delivery.event_type == "payment.due"
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempt_number == 1

    def test_mark_success(self):
        """Test marking delivery as successful."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.PENDING,
        )
        delivery.mark_success(status_code=200, response_body='{"ok": true}', duration_ms=150)
        assert delivery.status == DeliveryStatus.SUCCESS
        assert delivery.status_code == 200
        assert delivery.response_body == '{"ok": true}'
        assert delivery.duration_ms == 150
        assert delivery.error_message is None
        assert delivery.next_retry_at is None

    def test_mark_failed(self):
        """Test marking delivery as failed."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.PENDING,
        )
        delivery.mark_failed(
            error_message="Connection refused",
            status_code=None,
            response_body=None,
            duration_ms=5000,
        )
        assert delivery.status == DeliveryStatus.FAILED
        assert delivery.error_message == "Connection refused"
        assert delivery.status_code is None
        assert delivery.duration_ms == 5000

    def test_mark_failed_with_http_error(self):
        """Test marking delivery as failed with HTTP error."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.PENDING,
        )
        delivery.mark_failed(
            error_message="HTTP 500",
            status_code=500,
            response_body="Internal Server Error",
            duration_ms=200,
        )
        assert delivery.status == DeliveryStatus.FAILED
        assert delivery.status_code == 500
        assert delivery.response_body == "Internal Server Error"

    def test_schedule_retry(self):
        """Test scheduling a retry."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.FAILED,
            attempt_number=1,
        )
        retry_at = datetime.utcnow() + timedelta(minutes=5)
        delivery.schedule_retry(retry_at)
        assert delivery.status == DeliveryStatus.RETRYING
        assert delivery.next_retry_at == retry_at
        assert delivery.attempt_number == 2

    def test_can_retry_true(self):
        """Test can_retry when attempts remaining."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            attempt_number=1,
            max_attempts=3,
        )
        assert delivery.can_retry is True

    def test_can_retry_false(self):
        """Test can_retry when max attempts reached."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            attempt_number=3,
            max_attempts=3,
        )
        assert delivery.can_retry is False

    def test_get_payload_dict(self):
        """Test getting payload as dictionary."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"subscription_id": "123", "amount": 9.99}',
        )
        payload = delivery.get_payload_dict()
        assert payload == {"subscription_id": "123", "amount": 9.99}

    def test_get_payload_dict_invalid_json(self):
        """Test getting payload with invalid JSON."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload="invalid json",
        )
        assert delivery.get_payload_dict() == {}

    def test_repr(self):
        """Test string representation."""
        delivery = WebhookDelivery(
            webhook_id=str(uuid4()),
            event_type="payment.due",
            event_id=str(uuid4()),
            payload='{"test": true}',
            status=DeliveryStatus.SUCCESS,
            attempt_number=1,
        )
        repr_str = repr(delivery)
        assert "WebhookDelivery" in repr_str
        assert "payment.due" in repr_str
        assert "success" in repr_str
        assert "attempt=1" in repr_str


class TestWebhookSchemas:
    """Tests for Webhook Pydantic schemas."""

    def test_webhook_create_valid(self):
        """Test valid webhook creation schema."""
        data = WebhookCreate(
            name="Payment Alerts",
            url="https://example.com/webhook",
            events=[WebhookEventEnum.PAYMENT_DUE, WebhookEventEnum.PAYMENT_OVERDUE],
        )
        assert data.name == "Payment Alerts"
        assert str(data.url) == "https://example.com/webhook"
        assert len(data.events) == 2

    def test_webhook_create_with_headers(self):
        """Test webhook creation with custom headers."""
        data = WebhookCreate(
            name="Test",
            url="https://example.com/webhook",
            events=[WebhookEventEnum.PAYMENT_DUE],
            headers={"Authorization": "Bearer token"},
        )
        assert data.headers == {"Authorization": "Bearer token"}

    def test_webhook_create_unique_events(self):
        """Test that duplicate events are removed."""
        data = WebhookCreate(
            name="Test",
            url="https://example.com/webhook",
            events=[
                WebhookEventEnum.PAYMENT_DUE,
                WebhookEventEnum.PAYMENT_DUE,
                WebhookEventEnum.PAYMENT_OVERDUE,
            ],
        )
        # Duplicates should be removed
        assert len(data.events) == 2

    def test_webhook_create_invalid_url(self):
        """Test that invalid URL is rejected."""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="Test",
                url="not-a-url",
                events=[WebhookEventEnum.PAYMENT_DUE],
            )

    def test_webhook_create_empty_name(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="",
                url="https://example.com/webhook",
                events=[WebhookEventEnum.PAYMENT_DUE],
            )

    def test_webhook_create_empty_events(self):
        """Test that empty events list is rejected."""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="Test",
                url="https://example.com/webhook",
                events=[],
            )

    def test_webhook_update_partial(self):
        """Test partial webhook update."""
        data = WebhookUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.url is None
        assert data.events is None
        assert data.is_active is None

    def test_webhook_update_pause(self):
        """Test pausing via update."""
        data = WebhookUpdate(is_active=False)
        assert data.is_active is False

    def test_webhook_response_from_model(self):
        """Test creating response from model."""
        webhook_data = {
            "id": str(uuid4()),
            "name": "Test",
            "url": "https://example.com",
            "events": ["payment.due"],
            "status": WebhookStatus.ACTIVE,
            "is_active": True,
            "headers": None,
            "consecutive_failures": 0,
            "last_triggered_at": None,
            "last_success_at": None,
            "last_failure_at": None,
            "last_failure_reason": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        class MockWebhook:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        webhook = MockWebhook(**webhook_data)
        response = WebhookResponse.model_validate(webhook)
        assert response.name == "Test"
        assert response.status == WebhookStatusEnum.ACTIVE

    def test_webhook_response_parses_headers(self):
        """Test that response parses JSON headers."""
        response = WebhookResponse(
            id=str(uuid4()),
            name="Test",
            url="https://example.com",
            events=["payment.due"],
            status=WebhookStatusEnum.ACTIVE,
            is_active=True,
            headers='{"X-Custom": "value"}',
            consecutive_failures=0,
            last_triggered_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_failure_reason=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert response.headers == {"X-Custom": "value"}

    def test_webhook_secret_response(self):
        """Test secret response schema."""
        response = WebhookSecretResponse(
            id=str(uuid4()),
            secret="abcd1234" * 8,
        )
        assert len(response.secret) == 64

    def test_delivery_response_from_model(self):
        """Test creating delivery response from model."""
        delivery_data = {
            "id": str(uuid4()),
            "webhook_id": str(uuid4()),
            "event_type": "payment.due",
            "event_id": str(uuid4()),
            "status": DeliveryStatus.SUCCESS,
            "status_code": 200,
            "error_message": None,
            "attempt_number": 1,
            "duration_ms": 150,
            "created_at": datetime.utcnow(),
        }

        class MockDelivery:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        delivery = MockDelivery(**delivery_data)
        response = DeliveryResponse.model_validate(delivery)
        assert response.event_type == "payment.due"
        assert response.status == DeliveryStatusEnum.SUCCESS
        assert response.status_code == 200

    def test_webhook_test_request_default(self):
        """Test test request with default event."""
        request = WebhookTestRequest()
        assert request.event_type == WebhookEventEnum.SUBSCRIPTION_CREATED

    def test_webhook_test_request_custom_event(self):
        """Test test request with custom event."""
        request = WebhookTestRequest(event_type=WebhookEventEnum.PAYMENT_DUE)
        assert request.event_type == WebhookEventEnum.PAYMENT_DUE

    def test_webhook_test_response_success(self):
        """Test successful test response."""
        response = WebhookTestResponse(
            success=True,
            status_code=200,
            response_time_ms=150,
            error=None,
        )
        assert response.success is True
        assert response.error is None

    def test_webhook_test_response_failure(self):
        """Test failed test response."""
        response = WebhookTestResponse(
            success=False,
            status_code=500,
            response_time_ms=5000,
            error="Internal Server Error",
        )
        assert response.success is False
        assert response.error == "Internal Server Error"

    def test_webhook_stats_response(self):
        """Test stats response schema."""
        stats = WebhookStatsResponse(
            total_webhooks=5,
            active_webhooks=3,
            paused_webhooks=1,
            disabled_webhooks=1,
            total_deliveries=100,
            successful_deliveries=95,
            failed_deliveries=5,
            avg_response_time_ms=150.5,
        )
        assert stats.total_webhooks == 5
        assert stats.active_webhooks == 3
        assert stats.avg_response_time_ms == 150.5

    def test_webhook_list_response(self):
        """Test list response schema."""
        response = WebhookListResponse(
            webhooks=[],
            total=0,
        )
        assert response.webhooks == []
        assert response.total == 0

    def test_delivery_list_response(self):
        """Test delivery list response schema."""
        response = DeliveryListResponse(
            deliveries=[],
            total=0,
        )
        assert response.deliveries == []
        assert response.total == 0


class TestHMACSignature:
    """Tests for HMAC signature generation."""

    def test_signature_generation(self):
        """Test HMAC-SHA256 signature generation."""
        import hashlib
        import hmac

        secret = "test_secret_12345"
        payload = '{"event_type": "payment.due", "data": {"id": "123"}}'

        # Generate signature
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Verify format (64 hex characters)
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_signature_verification(self):
        """Test signature verification."""
        import hashlib
        import hmac

        secret = "test_secret"
        payload = '{"test": true}'

        # Generate signature
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Verify signature
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert hmac.compare_digest(signature, expected)

    def test_signature_differs_with_different_secret(self):
        """Test that different secrets produce different signatures."""
        import hashlib
        import hmac

        payload = '{"test": true}'

        sig1 = hmac.new(b"secret1", payload.encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new(b"secret2", payload.encode(), hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_signature_differs_with_different_payload(self):
        """Test that different payloads produce different signatures."""
        import hashlib
        import hmac

        secret = b"test_secret"

        sig1 = hmac.new(secret, b'{"a": 1}', hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret, b'{"a": 2}', hashlib.sha256).hexdigest()

        assert sig1 != sig2
