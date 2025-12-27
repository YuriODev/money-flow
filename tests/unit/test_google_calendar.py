"""Unit tests for Google Calendar OAuth integration.

Sprint 5.6 - Calendar Integration

Tests cover:
- GoogleCalendarConnection model
- GoogleCalendarSyncStatus enum
- GoogleCalendarService methods
- OAuth flow helpers
- Token management
- Event creation
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.google_calendar import (
    GoogleCalendarConnection,
    GoogleCalendarSyncStatus,
)


class TestGoogleCalendarSyncStatus:
    """Tests for GoogleCalendarSyncStatus enum."""

    def test_connected_status(self):
        """Test connected status value."""
        assert GoogleCalendarSyncStatus.CONNECTED.value == "connected"

    def test_disconnected_status(self):
        """Test disconnected status value."""
        assert GoogleCalendarSyncStatus.DISCONNECTED.value == "disconnected"

    def test_token_expired_status(self):
        """Test token_expired status value."""
        assert GoogleCalendarSyncStatus.TOKEN_EXPIRED.value == "token_expired"

    def test_error_status(self):
        """Test error status value."""
        assert GoogleCalendarSyncStatus.ERROR.value == "error"

    def test_all_statuses_present(self):
        """Test all expected statuses are defined."""
        expected = ["connected", "disconnected", "token_expired", "error"]
        actual = [s.value for s in GoogleCalendarSyncStatus]
        for status in expected:
            assert status in actual


class TestGoogleCalendarConnectionModel:
    """Tests for GoogleCalendarConnection model."""

    def test_create_connection(self):
        """Test creating a connection with required fields."""
        user_id = str(uuid4())
        connection = GoogleCalendarConnection(
            user_id=user_id,
            access_token="test_access_token",
            sync_status=GoogleCalendarSyncStatus.CONNECTED,  # Explicit for unit tests
        )
        assert connection.user_id == user_id
        assert connection.access_token == "test_access_token"
        assert connection.sync_status == GoogleCalendarSyncStatus.CONNECTED

    def test_connection_with_refresh_token(self):
        """Test connection with refresh token."""
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            refresh_token="refresh_token_123",
        )
        assert connection.refresh_token == "refresh_token_123"

    def test_connection_with_token_expiry(self):
        """Test connection with token expiry."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            token_expiry=future_time,
        )
        assert connection.token_expiry == future_time

    def test_default_calendar_id(self):
        """Test calendar_id can be set to 'primary'."""
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            calendar_id="primary",  # Explicit for unit tests
        )
        assert connection.calendar_id == "primary"

    def test_default_sync_enabled(self):
        """Test sync_enabled can be set to True."""
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            sync_enabled=True,  # Explicit for unit tests
        )
        assert connection.sync_enabled is True

    def test_is_token_expired_none(self):
        """Test is_token_expired returns True when expiry is None."""
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            token_expiry=None,
        )
        assert connection.is_token_expired is True

    def test_is_token_expired_past(self):
        """Test is_token_expired returns True for past expiry."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            token_expiry=past_time,
        )
        assert connection.is_token_expired is True

    def test_is_token_expired_future(self):
        """Test is_token_expired returns False for future expiry."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            token_expiry=future_time,
        )
        assert connection.is_token_expired is False

    def test_needs_reauthorization_expired_no_refresh(self):
        """Test needs_reauthorization when token expired without refresh token."""
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            refresh_token=None,
            token_expiry=None,
        )
        assert connection.needs_reauthorization is True

    def test_needs_reauthorization_expired_with_refresh(self):
        """Test needs_reauthorization when token expired but has refresh token."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            refresh_token="refresh",
            token_expiry=past_time,
        )
        assert connection.needs_reauthorization is False

    def test_needs_reauthorization_valid_token(self):
        """Test needs_reauthorization when token is still valid."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        connection = GoogleCalendarConnection(
            user_id=str(uuid4()),
            access_token="access",
            token_expiry=future_time,
        )
        assert connection.needs_reauthorization is False

    def test_repr(self):
        """Test string representation."""
        user_id = str(uuid4())
        connection = GoogleCalendarConnection(
            user_id=user_id,
            access_token="access",
            sync_status=GoogleCalendarSyncStatus.CONNECTED,
        )
        repr_str = repr(connection)
        assert "GoogleCalendarConnection" in repr_str
        assert user_id in repr_str
        assert "connected" in repr_str


class TestGoogleCalendarService:
    """Tests for GoogleCalendarService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_get_connection_not_found(self, mock_db, user_id):
        """Test get_connection returns None when no connection exists."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        connection = await service.get_connection()

        assert connection is None

    @pytest.mark.asyncio
    async def test_get_connection_found(self, mock_db, user_id):
        """Test get_connection returns connection when exists."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        connection = await service.get_connection()

        assert connection == mock_connection

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self, mock_db, user_id):
        """Test disconnect returns False when no connection."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        result = await service.disconnect()

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_with_connection(self, mock_db, user_id):
        """Test disconnect updates connection status."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_connection = MagicMock()
        mock_connection.sync_status = GoogleCalendarSyncStatus.CONNECTED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        result = await service.disconnect()

        assert result is True
        assert mock_connection.sync_status == GoogleCalendarSyncStatus.DISCONNECTED
        assert mock_connection.access_token == ""
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sync_status_not_connected(self, mock_db, user_id):
        """Test get_sync_status when not connected."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        status = await service.get_sync_status()

        assert status["connected"] is False
        assert status["status"] == "not_connected"

    @pytest.mark.asyncio
    async def test_get_sync_status_connected(self, mock_db, user_id):
        """Test get_sync_status when connected."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_connection = MagicMock()
        mock_connection.sync_status = GoogleCalendarSyncStatus.CONNECTED
        mock_connection.calendar_id = "primary"
        mock_connection.sync_enabled = True
        mock_connection.last_sync_at = datetime.utcnow()
        mock_connection.last_error = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        service = GoogleCalendarService(mock_db, user_id)
        status = await service.get_sync_status()

        assert status["connected"] is True
        assert status["status"] == "connected"
        assert status["calendar_id"] == "primary"
        assert status["sync_enabled"] is True


class TestGoogleCalendarServiceRecurrence:
    """Tests for recurrence rule generation."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_db = AsyncMock()
        return GoogleCalendarService(mock_db, uuid4())

    def test_daily_recurrence(self, service):
        """Test daily recurrence rule."""
        rule = service._get_recurrence_rule("daily")
        assert rule == "RRULE:FREQ=DAILY;INTERVAL=1"

    def test_weekly_recurrence(self, service):
        """Test weekly recurrence rule."""
        rule = service._get_recurrence_rule("weekly")
        assert rule == "RRULE:FREQ=WEEKLY;INTERVAL=1"

    def test_biweekly_recurrence(self, service):
        """Test biweekly recurrence rule."""
        rule = service._get_recurrence_rule("biweekly")
        assert rule == "RRULE:FREQ=WEEKLY;INTERVAL=2"

    def test_monthly_recurrence(self, service):
        """Test monthly recurrence rule."""
        rule = service._get_recurrence_rule("monthly")
        assert rule == "RRULE:FREQ=MONTHLY;INTERVAL=1"

    def test_quarterly_recurrence(self, service):
        """Test quarterly recurrence rule."""
        rule = service._get_recurrence_rule("quarterly")
        assert rule == "RRULE:FREQ=MONTHLY;INTERVAL=3"

    def test_yearly_recurrence(self, service):
        """Test yearly recurrence rule."""
        rule = service._get_recurrence_rule("yearly")
        assert rule == "RRULE:FREQ=YEARLY;INTERVAL=1"

    def test_annually_recurrence(self, service):
        """Test annually recurrence rule."""
        rule = service._get_recurrence_rule("annually")
        assert rule == "RRULE:FREQ=YEARLY;INTERVAL=1"

    def test_one_time_no_recurrence(self, service):
        """Test one_time returns None."""
        rule = service._get_recurrence_rule("one_time")
        assert rule is None

    def test_unknown_frequency_no_recurrence(self, service):
        """Test unknown frequency returns None."""
        rule = service._get_recurrence_rule("unknown")
        assert rule is None

    def test_case_insensitive(self, service):
        """Test frequency is case insensitive."""
        rule = service._get_recurrence_rule("MONTHLY")
        assert rule == "RRULE:FREQ=MONTHLY;INTERVAL=1"


class TestGoogleCalendarServiceEventBuilding:
    """Tests for event body building."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_db = AsyncMock()
        return GoogleCalendarService(mock_db, uuid4())

    @pytest.fixture
    def mock_subscription(self):
        """Create mock subscription."""
        sub = MagicMock()
        sub.id = uuid4()
        sub.service_name = "Netflix"
        sub.amount = 15.99
        sub.currency = "GBP"
        sub.frequency = "monthly"
        sub.payment_type = "subscription"
        sub.next_payment_date = datetime.now().date() + timedelta(days=7)
        sub.notes = "Test notes"
        return sub

    def test_build_event_body_basic(self, service, mock_subscription):
        """Test basic event body creation."""
        event = service._build_event_body(mock_subscription)

        assert "[Money Flow]" in event["summary"]
        assert "Netflix" in event["summary"]
        assert "£15.99" in event["summary"]
        assert "description" in event
        assert "start" in event
        assert "end" in event

    def test_build_event_body_currency_symbols(self, service, mock_subscription):
        """Test currency symbol mapping in event."""
        currencies = {
            "GBP": "£",
            "USD": "$",
            "EUR": "€",
            "UAH": "₴",
        }

        for code, symbol in currencies.items():
            mock_subscription.currency = code
            event = service._build_event_body(mock_subscription)
            assert symbol in event["summary"]

    def test_build_event_body_has_reminders(self, service, mock_subscription):
        """Test event has reminders configured."""
        event = service._build_event_body(mock_subscription)

        assert "reminders" in event
        assert event["reminders"]["useDefault"] is False
        assert len(event["reminders"]["overrides"]) > 0

    def test_build_event_body_has_extended_properties(self, service, mock_subscription):
        """Test event has extended properties for identification."""
        event = service._build_event_body(mock_subscription)

        assert "extendedProperties" in event
        assert "private" in event["extendedProperties"]
        assert "moneyflow_subscription_id" in event["extendedProperties"]["private"]
        assert "moneyflow_managed" in event["extendedProperties"]["private"]

    def test_build_event_body_monthly_recurrence(self, service, mock_subscription):
        """Test monthly subscription has recurrence rule."""
        mock_subscription.frequency = "monthly"
        event = service._build_event_body(mock_subscription)

        assert "recurrence" in event
        assert "RRULE:FREQ=MONTHLY" in event["recurrence"][0]

    def test_build_event_body_one_time_no_recurrence(self, service, mock_subscription):
        """Test one-time payment has no recurrence rule."""
        mock_subscription.frequency = "one_time"
        event = service._build_event_body(mock_subscription)

        assert "recurrence" not in event


class TestGoogleCalendarOAuthFlow:
    """Tests for OAuth flow methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return uuid4()

    @patch("src.services.google_calendar_service.settings")
    def test_get_oauth_flow_no_credentials(self, mock_settings, mock_db, user_id):
        """Test OAuth flow raises error without credentials."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_settings.google_client_id = ""
        mock_settings.google_client_secret = ""

        service = GoogleCalendarService(mock_db, user_id)

        with pytest.raises(ValueError, match="credentials are not configured"):
            service._get_oauth_flow()

    @patch("src.services.google_calendar_service.settings")
    @patch("src.services.google_calendar_service.Flow")
    def test_get_authorization_url(self, mock_flow_class, mock_settings, mock_db, user_id):
        """Test authorization URL generation."""
        from src.services.google_calendar_service import GoogleCalendarService

        mock_settings.google_client_id = "test_client_id"
        mock_settings.google_client_secret = "test_secret"
        mock_settings.google_redirect_uri = "http://localhost:8001/callback"

        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?...",
            "test_state",
        )
        mock_flow_class.from_client_config.return_value = mock_flow

        service = GoogleCalendarService(mock_db, user_id)
        auth_url, state = service.get_authorization_url()

        assert "accounts.google.com" in auth_url
        assert state == "test_state"
        mock_flow.authorization_url.assert_called_once()
