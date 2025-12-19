"""Unit tests for push notification service.

Tests cover:
- PushService initialization
- Configuration checks
- Notification sending
- Reminder notifications
- Daily/weekly digest notifications
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.services.push_service import CURRENCY_SYMBOLS, PushService


class MockSubscription:
    """Mock Subscription object for testing."""

    def __init__(
        self,
        sub_id: str = "sub-123",
        name: str = "Netflix",
        amount: Decimal = Decimal("15.99"),
        currency: str = "GBP",
        frequency: Frequency = Frequency.MONTHLY,
        next_payment_date: date | None = None,
        category: str | None = "Entertainment",
        payment_type: PaymentType = PaymentType.SUBSCRIPTION,
        payment_mode: PaymentMode = PaymentMode.RECURRING,
        is_active: bool = True,
    ):
        self.id = sub_id
        self.name = name
        self.amount = amount
        self.currency = currency
        self.frequency = frequency
        self.next_payment_date = next_payment_date or date.today()
        self.category = category
        self.payment_type = payment_type
        self.payment_mode = payment_mode
        self.is_active = is_active


class TestPushServiceInit:
    """Tests for PushService initialization."""

    def test_default_init(self):
        """Test service initialization with defaults."""
        service = PushService()
        # Without config, these should be empty strings
        assert service.vapid_private_key == ""
        assert service.vapid_public_key == ""
        assert service.vapid_email == ""

    def test_custom_init(self):
        """Test service initialization with custom values."""
        service = PushService(
            vapid_private_key="private-key-123",
            vapid_public_key="public-key-456",
            vapid_email="admin@example.com",
        )
        assert service.vapid_private_key == "private-key-123"
        assert service.vapid_public_key == "public-key-456"
        assert service.vapid_email == "admin@example.com"
        assert service.vapid_claims == {"sub": "mailto:admin@example.com"}


class TestIsConfigured:
    """Tests for is_configured property."""

    def test_not_configured_no_private_key(self):
        """Test is_configured returns False without private key."""
        service = PushService(
            vapid_public_key="key",
            vapid_email="admin@example.com",
        )
        assert service.is_configured is False

    def test_not_configured_no_public_key(self):
        """Test is_configured returns False without public key."""
        service = PushService(
            vapid_private_key="key",
            vapid_email="admin@example.com",
        )
        assert service.is_configured is False

    def test_not_configured_no_email(self):
        """Test is_configured returns False without email."""
        service = PushService(
            vapid_private_key="key",
            vapid_public_key="key",
        )
        assert service.is_configured is False

    def test_configured(self):
        """Test is_configured returns True with all required settings."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )
        assert service.is_configured is True


class TestSendNotification:
    """Tests for send_notification method."""

    def test_send_notification_not_configured(self):
        """Test send_notification returns False when not configured."""
        service = PushService()
        result = service.send_notification(
            subscription_info={"endpoint": "https://push.example.com", "keys": {}},
            title="Test",
            body="Test body",
        )
        assert result is False

    @patch("src.services.push_service.webpush")
    def test_send_notification_success(self, mock_webpush):
        """Test send_notification returns True on success."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_notification(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            title="Test Title",
            body="Test body",
        )

        assert result is True
        mock_webpush.assert_called_once()

    @patch("src.services.push_service.webpush")
    def test_send_notification_with_optional_params(self, mock_webpush):
        """Test send_notification with all optional parameters."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_notification(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            title="Test Title",
            body="Test body",
            icon="/custom-icon.png",
            badge="/custom-badge.png",
            tag="test-tag",
            data={"type": "test", "id": "123"},
            actions=[{"action": "view", "title": "View"}],
        )

        assert result is True
        mock_webpush.assert_called_once()

    @patch("src.services.push_service.webpush")
    def test_send_notification_failure(self, mock_webpush):
        """Test send_notification returns False on failure."""
        from pywebpush import WebPushException

        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        # Create a mock response object
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_webpush.side_effect = WebPushException("Push failed", mock_response)

        result = service.send_notification(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            title="Test Title",
            body="Test body",
        )

        assert result is False

    @patch("src.services.push_service.webpush")
    def test_send_notification_subscription_expired(self, mock_webpush):
        """Test handling of expired subscription (410 Gone)."""
        from pywebpush import WebPushException

        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_response = MagicMock()
        mock_response.status_code = 410

        mock_webpush.side_effect = WebPushException("Gone", mock_response)

        result = service.send_notification(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            title="Test Title",
            body="Test body",
        )

        assert result is False


class TestSendReminder:
    """Tests for send_reminder method."""

    @patch("src.services.push_service.webpush")
    def test_send_reminder_upcoming(self, mock_webpush):
        """Test send_reminder for upcoming payment."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        sub = MockSubscription(name="Spotify", amount=Decimal("9.99"))

        result = service.send_reminder(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            subscription=sub,
            days_until=3,
        )

        assert result is True
        mock_webpush.assert_called_once()

    @patch("src.services.push_service.webpush")
    def test_send_reminder_today(self, mock_webpush):
        """Test send_reminder for payment due today."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        sub = MockSubscription(name="Netflix", amount=Decimal("15.99"))

        result = service.send_reminder(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            subscription=sub,
            days_until=0,
        )

        assert result is True

    @patch("src.services.push_service.webpush")
    def test_send_reminder_tomorrow(self, mock_webpush):
        """Test send_reminder for payment due tomorrow."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        sub = MockSubscription(name="Gym", amount=Decimal("29.99"))

        result = service.send_reminder(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            subscription=sub,
            days_until=1,
        )

        assert result is True

    @patch("src.services.push_service.webpush")
    def test_send_reminder_overdue(self, mock_webpush):
        """Test send_reminder for overdue payment."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        sub = MockSubscription(name="Rent", amount=Decimal("1200.00"))

        result = service.send_reminder(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            subscription=sub,
            days_until=-5,
        )

        assert result is True


class TestSendDailyDigest:
    """Tests for send_daily_digest method."""

    @patch("src.services.push_service.webpush")
    def test_send_daily_digest_no_payments(self, mock_webpush):
        """Test send_daily_digest with no upcoming payments."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_daily_digest(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            payment_count=0,
            total_amount=0.0,
            currency="GBP",
        )

        assert result is True

    @patch("src.services.push_service.webpush")
    def test_send_daily_digest_one_payment(self, mock_webpush):
        """Test send_daily_digest with one payment."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_daily_digest(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            payment_count=1,
            total_amount=15.99,
            currency="GBP",
        )

        assert result is True

    @patch("src.services.push_service.webpush")
    def test_send_daily_digest_multiple_payments(self, mock_webpush):
        """Test send_daily_digest with multiple payments."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_daily_digest(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            payment_count=3,
            total_amount=125.97,
            currency="EUR",
        )

        assert result is True


class TestSendWeeklyDigest:
    """Tests for send_weekly_digest method."""

    @patch("src.services.push_service.webpush")
    def test_send_weekly_digest_no_payments(self, mock_webpush):
        """Test send_weekly_digest with no upcoming payments."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_weekly_digest(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            payment_count=0,
            total_amount=0.0,
            currency="GBP",
        )

        assert result is True

    @patch("src.services.push_service.webpush")
    def test_send_weekly_digest_with_payments(self, mock_webpush):
        """Test send_weekly_digest with upcoming payments."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_weekly_digest(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            },
            payment_count=5,
            total_amount=299.50,
            currency="USD",
        )

        assert result is True


class TestSendTestNotification:
    """Tests for send_test_notification method."""

    @patch("src.services.push_service.webpush")
    def test_send_test_notification_success(self, mock_webpush):
        """Test send_test_notification sends test push."""
        service = PushService(
            vapid_private_key="private-key",
            vapid_public_key="public-key",
            vapid_email="admin@example.com",
        )

        mock_webpush.return_value = MagicMock()

        result = service.send_test_notification(
            subscription_info={
                "endpoint": "https://push.example.com/send/123",
                "keys": {"p256dh": "key1", "auth": "key2"},
            }
        )

        assert result is True
        mock_webpush.assert_called_once()


class TestCurrencySymbols:
    """Tests for currency symbol mapping."""

    def test_gbp_symbol(self):
        """Test GBP symbol."""
        assert CURRENCY_SYMBOLS["GBP"] == "£"

    def test_usd_symbol(self):
        """Test USD symbol."""
        assert CURRENCY_SYMBOLS["USD"] == "$"

    def test_eur_symbol(self):
        """Test EUR symbol."""
        assert CURRENCY_SYMBOLS["EUR"] == "€"

    def test_uah_symbol(self):
        """Test UAH symbol."""
        assert CURRENCY_SYMBOLS["UAH"] == "₴"

    def test_default_symbol(self):
        """Test default symbol for unknown currency."""
        assert CURRENCY_SYMBOLS.get("XYZ", "£") == "£"
