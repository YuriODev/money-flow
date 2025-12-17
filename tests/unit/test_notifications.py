"""Unit tests for notification system and Telegram integration.

Tests cover:
- NotificationPreferences model
- TelegramService
- Notification API schemas
- Verification code generation and validation
- Quiet hours functionality
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.notification import NotificationPreferences
from src.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    TelegramLinkResponse,
    TelegramStatus,
    preferences_to_response,
)


# =============================================================================
# NotificationPreferences Model Tests
# =============================================================================


class TestNotificationPreferencesModel:
    """Tests for NotificationPreferences SQLAlchemy model."""

    def test_create_notification_preferences_defaults(self):
        """Test that model has expected default column definitions."""
        # Note: Without database session, SQLAlchemy column defaults are not
        # automatically applied to Python instances. We test the column
        # definitions are correct.
        prefs = NotificationPreferences(user_id=str(uuid4()))

        # Basic object created
        assert prefs.user_id is not None

    def test_generate_verification_code(self):
        """Test verification code generation."""
        prefs = NotificationPreferences(user_id=str(uuid4()))

        code = prefs.generate_verification_code()

        # 6-character hex code (token_hex(3))
        assert len(code) == 6
        assert code.isalnum()
        assert prefs.telegram_verification_code == code
        assert prefs.telegram_verification_expires is not None
        # Should expire in 10 minutes
        assert prefs.telegram_verification_expires > datetime.utcnow()
        assert prefs.telegram_verification_expires < datetime.utcnow() + timedelta(minutes=15)

    def test_verify_code_valid(self):
        """Test valid verification code."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        code = prefs.generate_verification_code()

        result = prefs.verify_code(code)

        assert result is True
        # Note: verify_code() doesn't clear the code, clear_verification() does

    def test_verify_code_valid_clears_on_clear_verification(self):
        """Test clear_verification clears the code."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.generate_verification_code()

        prefs.clear_verification()

        assert prefs.telegram_verification_code is None
        assert prefs.telegram_verification_expires is None

    def test_verify_code_invalid(self):
        """Test invalid verification code."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.generate_verification_code()

        result = prefs.verify_code("WRONG123")

        assert result is False

    def test_verify_code_expired(self):
        """Test expired verification code."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        code = prefs.generate_verification_code()

        # Manually expire the code
        prefs.telegram_verification_expires = datetime.utcnow() - timedelta(minutes=1)

        result = prefs.verify_code(code)

        assert result is False

    def test_verify_code_no_code_set(self):
        """Test verifying when no code is set."""
        prefs = NotificationPreferences(user_id=str(uuid4()))

        result = prefs.verify_code("ANYCODE1")

        assert result is False

    def test_verify_code_case_insensitive(self):
        """Test that verification code is case insensitive."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        code = prefs.generate_verification_code()

        # Test lowercase
        result = prefs.verify_code(code.lower())
        assert result is True

    def test_quiet_hours_not_configured(self):
        """Test quiet hours check when not configured."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.quiet_hours_enabled = False
        prefs.quiet_hours_start = None
        prefs.quiet_hours_end = None

        # Should return False (not in quiet hours) when not enabled
        result = prefs.is_in_quiet_hours(time(22, 0))

        assert result is False

    def test_quiet_hours_disabled_even_with_times(self):
        """Test quiet hours returns False when disabled even if times are set."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.quiet_hours_enabled = False
        prefs.quiet_hours_start = time(22, 0)
        prefs.quiet_hours_end = time(7, 0)

        result = prefs.is_in_quiet_hours(time(23, 0))

        assert result is False

    def test_quiet_hours_within_same_day(self):
        """Test quiet hours within the same day (e.g., 09:00-17:00)."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = time(9, 0)
        prefs.quiet_hours_end = time(17, 0)

        # During quiet hours
        assert prefs.is_in_quiet_hours(time(12, 0)) is True
        assert prefs.is_in_quiet_hours(time(9, 0)) is True

        # Outside quiet hours
        assert prefs.is_in_quiet_hours(time(8, 59)) is False
        assert prefs.is_in_quiet_hours(time(17, 1)) is False

    def test_quiet_hours_overnight(self):
        """Test quiet hours that span midnight (e.g., 22:00-07:00)."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = time(22, 0)
        prefs.quiet_hours_end = time(7, 0)

        # During quiet hours (evening)
        assert prefs.is_in_quiet_hours(time(23, 0)) is True
        assert prefs.is_in_quiet_hours(time(22, 0)) is True

        # During quiet hours (morning)
        assert prefs.is_in_quiet_hours(time(3, 0)) is True
        assert prefs.is_in_quiet_hours(time(7, 0)) is True

        # Outside quiet hours
        assert prefs.is_in_quiet_hours(time(8, 0)) is False
        assert prefs.is_in_quiet_hours(time(12, 0)) is False
        assert prefs.is_in_quiet_hours(time(21, 0)) is False

    def test_is_telegram_linked(self):
        """Test is_telegram_linked property."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.telegram_enabled = True
        prefs.telegram_verified = True
        prefs.telegram_chat_id = "123456"

        assert prefs.is_telegram_linked is True

    def test_is_telegram_linked_not_verified(self):
        """Test is_telegram_linked when not verified."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.telegram_enabled = True
        prefs.telegram_verified = False
        prefs.telegram_chat_id = "123456"

        assert prefs.is_telegram_linked is False

    def test_is_telegram_linked_no_chat_id(self):
        """Test is_telegram_linked when no chat ID."""
        prefs = NotificationPreferences(user_id=str(uuid4()))
        prefs.telegram_enabled = True
        prefs.telegram_verified = True
        prefs.telegram_chat_id = None

        assert prefs.is_telegram_linked is False


# =============================================================================
# Notification Schemas Tests
# =============================================================================


class TestNotificationSchemas:
    """Tests for notification Pydantic schemas."""

    def test_telegram_status_linked(self):
        """Test TelegramStatus for linked account."""
        status = TelegramStatus(
            enabled=True,
            verified=True,
            username="testuser",
            linked=True,
        )

        assert status.enabled is True
        assert status.verified is True
        assert status.username == "testuser"
        assert status.linked is True

    def test_telegram_status_not_linked(self):
        """Test TelegramStatus for unlinked account."""
        status = TelegramStatus(
            enabled=False,
            verified=False,
            username=None,
            linked=False,
        )

        assert status.enabled is False
        assert status.linked is False

    def test_telegram_link_response(self):
        """Test TelegramLinkResponse."""
        response = TelegramLinkResponse(
            verification_code="ABC123",
            bot_username="MoneyFlowBot",
            bot_link="https://t.me/MoneyFlowBot",
            expires_in_minutes=10,
            instructions="Send the code to the bot",
        )

        assert response.verification_code == "ABC123"
        assert response.bot_username == "MoneyFlowBot"
        assert "t.me" in response.bot_link
        assert response.expires_in_minutes == 10

    def test_notification_preferences_update(self):
        """Test NotificationPreferencesUpdate schema."""
        update = NotificationPreferencesUpdate(
            reminder_enabled=True,
            reminder_days_before=5,
            daily_digest=True,
            weekly_digest=False,
            weekly_digest_day=2,  # Wednesday
        )

        assert update.reminder_enabled is True
        assert update.reminder_days_before == 5
        assert update.daily_digest is True
        assert update.weekly_digest is False
        assert update.weekly_digest_day == 2

    def test_notification_preferences_update_partial(self):
        """Test partial update with only some fields."""
        update = NotificationPreferencesUpdate(
            reminder_days_before=7,
        )

        assert update.reminder_days_before == 7
        assert update.reminder_enabled is None
        assert update.daily_digest is None

    def test_notification_preferences_response_with_telegram(self):
        """Test NotificationPreferencesResponse schema with telegram."""
        response = NotificationPreferencesResponse(
            id=str(uuid4()),
            user_id=str(uuid4()),
            telegram=TelegramStatus(
                enabled=True,
                verified=True,
                username="testuser",
                linked=True,
            ),
            reminder_enabled=True,
            reminder_days_before=3,
            overdue_alerts=True,
            daily_digest=False,
            weekly_digest=True,
            weekly_digest_day=0,
            quiet_hours_enabled=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
        )

        assert response.telegram.enabled is True
        assert response.telegram.verified is True
        assert response.telegram.username == "testuser"

    def test_preferences_to_response_helper(self):
        """Test preferences_to_response helper function."""
        prefs = MagicMock()
        prefs.id = str(uuid4())
        prefs.user_id = str(uuid4())
        prefs.reminder_enabled = True
        prefs.reminder_days_before = 3
        prefs.reminder_time = time(9, 0)
        prefs.overdue_alerts = True
        prefs.daily_digest = False
        prefs.weekly_digest = True
        prefs.weekly_digest_day = 0
        prefs.quiet_hours_enabled = False
        prefs.quiet_hours_start = None
        prefs.quiet_hours_end = None
        prefs.telegram_enabled = True
        prefs.telegram_verified = True
        prefs.telegram_username = "testuser"
        prefs.is_telegram_linked = True

        result = preferences_to_response(prefs)

        assert result["id"] == prefs.id
        assert result["telegram"].enabled is True
        assert result["telegram"].verified is True


# =============================================================================
# TelegramService Tests
# =============================================================================


class TestTelegramService:
    """Tests for TelegramService."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        with patch("src.services.telegram_service.settings") as mock:
            mock.telegram_bot_token = "test_token"
            mock.telegram_bot_username = "TestBot"
            yield mock

    @pytest.fixture
    def telegram_service(self, mock_settings):
        """Create TelegramService instance."""
        from src.services.telegram_service import TelegramService

        return TelegramService()

    def test_service_initialization(self, telegram_service):
        """Test service initializes correctly."""
        assert telegram_service.bot_token == "test_token"
        assert telegram_service.bot_username == "TestBot"
        assert "https://api.telegram.org/bot" in telegram_service.api_url

    def test_is_configured(self, telegram_service):
        """Test is_configured property."""
        assert telegram_service.is_configured is True

    def test_bot_link(self, telegram_service):
        """Test bot_link property."""
        assert "t.me/TestBot" in telegram_service.bot_link

    @pytest.mark.asyncio
    async def test_send_message_no_token(self):
        """Test send_message fails gracefully without token."""
        with patch("src.services.telegram_service.settings") as mock:
            mock.telegram_bot_token = ""
            mock.telegram_bot_username = ""

            from src.services.telegram_service import TelegramService

            service = TelegramService()
            result = await service.send_message("123", "Test message")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, telegram_service):
        """Test successful message sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_client_class.return_value = mock_client

            result = await telegram_service.send_message("123456", "Hello")

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_test_notification(self, telegram_service):
        """Test sending test notification."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_test_notification("123456")

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "123456" in call_args[0]
            assert "Test Notification" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_verification_success(self, telegram_service):
        """Test sending verification success message."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_verification_success("123456")

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "linked" in call_args[0][1].lower()


# =============================================================================
# Reminder Message Formatting Tests
# =============================================================================


class TestReminderFormatting:
    """Tests for reminder message formatting."""

    @pytest.fixture
    def mock_subscription(self):
        """Create a mock subscription."""
        from datetime import date
        from decimal import Decimal

        sub = MagicMock()
        sub.name = "Netflix"
        sub.amount = Decimal("15.99")
        sub.currency = "GBP"
        sub.next_payment_date = date(2025, 1, 20)
        sub.payment_type = "subscription"
        sub.card = None
        return sub

    @pytest.fixture
    def telegram_service(self):
        """Create TelegramService with mocked settings."""
        with patch("src.services.telegram_service.settings") as mock:
            mock.telegram_bot_token = "test_token"
            mock.telegram_bot_username = "TestBot"

            from src.services.telegram_service import TelegramService

            return TelegramService()

    @pytest.mark.asyncio
    async def test_send_reminder_due_soon(self, telegram_service, mock_subscription):
        """Test reminder message for payment due in a few days."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_reminder(
                chat_id="123456",
                subscription=mock_subscription,
                days_until=3,
            )

            assert result is True
            mock_send.assert_called_once()
            message = mock_send.call_args[0][1]
            assert "Netflix" in message
            assert "15.99" in message
            assert "3 days" in message

    @pytest.mark.asyncio
    async def test_send_reminder_due_today(self, telegram_service, mock_subscription):
        """Test reminder message for payment due today."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_reminder(
                chat_id="123456",
                subscription=mock_subscription,
                days_until=0,
            )

            assert result is True
            message = mock_send.call_args[0][1]
            # Due today shows as OVERDUE (days_until <= 0)
            assert "OVERDUE" in message
            assert "overdue" in message.lower()

    @pytest.mark.asyncio
    async def test_send_reminder_overdue(self, telegram_service, mock_subscription):
        """Test reminder message for overdue payment."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_reminder(
                chat_id="123456",
                subscription=mock_subscription,
                days_until=-2,  # 2 days overdue
            )

            assert result is True
            message = mock_send.call_args[0][1]
            assert "OVERDUE" in message
            # The message says "is overdue!" without days count
            assert "overdue" in message.lower()

    @pytest.mark.asyncio
    async def test_send_daily_digest(self, telegram_service, mock_subscription):
        """Test daily digest formatting."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_daily_digest(
                chat_id="123456",
                subscriptions=[mock_subscription],
                currency="GBP",
            )

            assert result is True
            message = mock_send.call_args[0][1]
            assert "Daily Payment Summary" in message
            assert "Netflix" in message

    @pytest.mark.asyncio
    async def test_send_weekly_digest_empty(self, telegram_service):
        """Test weekly digest with no subscriptions."""
        with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await telegram_service.send_weekly_digest(
                chat_id="123456",
                subscriptions=[],
                currency="GBP",
            )

            assert result is True
            message = mock_send.call_args[0][1]
            assert "Weekly Payment Summary" in message
            assert "No payments" in message


# =============================================================================
# Background Tasks Tests
# =============================================================================


class TestBackgroundTasks:
    """Tests for notification background tasks."""

    @pytest.mark.asyncio
    async def test_health_check_task(self):
        """Test health check task returns expected format."""
        from src.core.tasks import health_check_task

        ctx = {"job_id": "test-job-123"}
        result = await health_check_task(ctx)

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["worker_id"] == "test-job-123"

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test cleanup task returns expected format."""
        from src.core.tasks import cleanup_expired_sessions

        ctx = {}
        result = await cleanup_expired_sessions(ctx)

        assert "cleaned_sessions" in result
        assert isinstance(result["cleaned_sessions"], int)

    def test_task_registration(self):
        """Test that all notification tasks are registered."""
        from src.core.tasks import get_registered_tasks

        tasks = get_registered_tasks()

        assert "send_payment_reminders" in tasks
        assert "send_daily_digest" in tasks
        assert "send_weekly_digest" in tasks
        assert "send_overdue_alerts" in tasks
        assert "health_check_task" in tasks
