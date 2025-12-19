"""Unit tests for email service.

Tests cover:
- EmailService initialization
- Configuration checks
- Email sending
- Reminder email generation
- Daily/weekly digest generation
- HTML template generation
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.services.email_service import CURRENCY_SYMBOLS, EmailService


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


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    def test_default_init(self):
        """Test service initialization with defaults."""
        service = EmailService()
        # Without config, these should be empty strings
        assert service.smtp_host == ""
        assert service.smtp_port == 587
        assert service.smtp_user == ""
        assert service.smtp_password == ""
        assert service.from_name == "Money Flow"

    def test_custom_init(self):
        """Test service initialization with custom values."""
        service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=465,
            smtp_user="user@gmail.com",
            smtp_password="secret",
            from_email="noreply@example.com",
            from_name="Test App",
        )
        assert service.smtp_host == "smtp.gmail.com"
        assert service.smtp_port == 465
        assert service.smtp_user == "user@gmail.com"
        assert service.smtp_password == "secret"
        assert service.from_email == "noreply@example.com"
        assert service.from_name == "Test App"


class TestIsConfigured:
    """Tests for is_configured property."""

    def test_not_configured_no_host(self):
        """Test is_configured returns False without host."""
        service = EmailService(smtp_user="user", smtp_password="pass")
        assert service.is_configured is False

    def test_not_configured_no_user(self):
        """Test is_configured returns False without user."""
        service = EmailService(smtp_host="smtp.example.com", smtp_password="pass")
        assert service.is_configured is False

    def test_not_configured_no_password(self):
        """Test is_configured returns False without password."""
        service = EmailService(smtp_host="smtp.example.com", smtp_user="user")
        assert service.is_configured is False

    def test_configured(self):
        """Test is_configured returns True with all required settings."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
        )
        assert service.is_configured is True


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_not_configured(self):
        """Test send_email returns False when not configured."""
        service = EmailService()
        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test send_email returns True on success."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        with patch("src.services.email_service.aiosmtplib.send", new_callable=AsyncMock):
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_body="<p>Test body</p>",
                text_body="Test body",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test send_email returns False on failure."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        with patch(
            "src.services.email_service.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ):
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_body="<p>Test body</p>",
            )
            assert result is False


class TestSendReminder:
    """Tests for send_reminder method."""

    @pytest.mark.asyncio
    async def test_send_reminder_not_configured(self):
        """Test send_reminder returns False when not configured."""
        service = EmailService()
        sub = MockSubscription()
        result = await service.send_reminder(
            to_email="test@example.com",
            subscription=sub,
            days_until=3,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_reminder_upcoming(self):
        """Test send_reminder for upcoming payment."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription(
            name="Spotify",
            amount=Decimal("9.99"),
            next_payment_date=date.today() + timedelta(days=3),
        )

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=3,
            )
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_reminder_overdue(self):
        """Test send_reminder for overdue payment."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription(
            name="Netflix",
            amount=Decimal("15.99"),
            next_payment_date=date.today() - timedelta(days=5),
        )

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=-5,
            )
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_reminder_today(self):
        """Test send_reminder for payment due today."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription(
            name="Netflix",
            amount=Decimal("15.99"),
            next_payment_date=date.today(),
        )

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=0,
            )
            assert result is True
            mock_send.assert_called_once()


class TestSendDailyDigest:
    """Tests for send_daily_digest method."""

    @pytest.mark.asyncio
    async def test_send_daily_digest_empty(self):
        """Test send_daily_digest returns False for empty list."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )
        result = await service.send_daily_digest(
            to_email="test@example.com",
            subscriptions=[],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_daily_digest_success(self):
        """Test send_daily_digest sends email."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        subscriptions = [
            MockSubscription(name="Netflix", amount=Decimal("15.99")),
            MockSubscription(name="Spotify", amount=Decimal("9.99")),
            MockSubscription(name="Rent", amount=Decimal("1200.00")),
        ]

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_daily_digest(
                to_email="test@example.com",
                subscriptions=subscriptions,
                currency="GBP",
            )
            assert result is True
            mock_send.assert_called_once()


class TestSendWeeklyDigest:
    """Tests for send_weekly_digest method."""

    @pytest.mark.asyncio
    async def test_send_weekly_digest_empty(self):
        """Test send_weekly_digest returns False for empty list."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )
        result = await service.send_weekly_digest(
            to_email="test@example.com",
            subscriptions=[],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_weekly_digest_success(self):
        """Test send_weekly_digest sends email."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        subscriptions = [
            MockSubscription(name="Netflix", amount=Decimal("15.99")),
            MockSubscription(name="Spotify", amount=Decimal("9.99")),
        ]

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_weekly_digest(
                to_email="test@example.com",
                subscriptions=subscriptions,
                currency="EUR",
            )
            assert result is True
            mock_send.assert_called_once()


class TestSendTestNotification:
    """Tests for send_test_notification method."""

    @pytest.mark.asyncio
    async def test_send_test_notification_not_configured(self):
        """Test send_test_notification returns False when not configured."""
        service = EmailService()
        result = await service.send_test_notification("test@example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_test_notification_success(self):
        """Test send_test_notification sends test email."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            result = await service.send_test_notification("test@example.com")
            assert result is True
            mock_send.assert_called_once()


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


class TestHtmlTemplateGeneration:
    """Tests for HTML template generation."""

    def test_reminder_html_contains_subscription_name(self):
        """Test reminder HTML contains subscription name."""
        service = EmailService()
        sub = MockSubscription(name="Test Service")

        html = service._build_reminder_html(
            subscription=sub,
            amount="£15.99",
            urgency_text="Due in 3 days",
            color="#3b82f6",
        )

        assert "Test Service" in html
        assert "£15.99" in html
        assert "Due in 3 days" in html

    def test_digest_html_contains_stats(self):
        """Test digest HTML contains payment stats."""
        service = EmailService()
        subscriptions = [
            MockSubscription(name="Netflix", amount=Decimal("15.99")),
            MockSubscription(name="Spotify", amount=Decimal("9.99")),
        ]

        html = service._build_digest_html(
            subscriptions=subscriptions,
            today_payments=[subscriptions[0]],
            week_payments=subscriptions,
            currency_symbol="£",
            total=Decimal("25.98"),
            period="Daily",
        )

        assert "Netflix" in html
        assert "Spotify" in html
        assert "£25.98" in html
        assert "Daily" in html


class TestUrgencyClassification:
    """Tests for urgency classification in reminders."""

    @pytest.mark.asyncio
    async def test_overdue_urgency(self):
        """Test overdue payment urgency text."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription()

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=-3,
            )
            # Check the subject contains "Overdue"
            call_args = mock_send.call_args
            msg = call_args[0][0]
            assert "Overdue" in msg["Subject"] or "overdue" in msg["Subject"]

    @pytest.mark.asyncio
    async def test_today_urgency(self):
        """Test today payment urgency text."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription()

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=0,
            )
            call_args = mock_send.call_args
            msg = call_args[0][0]
            assert "Today" in msg["Subject"] or "today" in msg["Subject"]

    @pytest.mark.asyncio
    async def test_tomorrow_urgency(self):
        """Test tomorrow payment urgency text."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            from_email="noreply@example.com",
        )

        sub = MockSubscription()

        with patch(
            "src.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await service.send_reminder(
                to_email="test@example.com",
                subscription=sub,
                days_until=1,
            )
            call_args = mock_send.call_args
            msg = call_args[0][0]
            assert "tomorrow" in msg["Subject"] or "Upcoming" in msg["Subject"]
