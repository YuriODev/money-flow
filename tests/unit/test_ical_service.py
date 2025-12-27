"""Unit tests for iCal feed generation service.

Sprint 5.6 - Calendar Integration

Tests cover:
- ICalService class and feed generation
- FREQUENCY_MAP mapping
- Event creation with all fields
- Currency symbol mapping
- Token generation and validation
- API endpoint responses
"""

import hashlib
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.ical_service import (
    FREQUENCY_MAP,
    ICalService,
    generate_feed_url,
    generate_ical_token,
    validate_ical_token,
)


class TestFrequencyMap:
    """Tests for FREQUENCY_MAP constant."""

    def test_daily_frequency(self):
        """Test daily frequency mapping."""
        assert FREQUENCY_MAP["daily"] == {"FREQ": "DAILY", "INTERVAL": 1}

    def test_weekly_frequency(self):
        """Test weekly frequency mapping."""
        assert FREQUENCY_MAP["weekly"] == {"FREQ": "WEEKLY", "INTERVAL": 1}

    def test_biweekly_frequency(self):
        """Test biweekly frequency mapping."""
        assert FREQUENCY_MAP["biweekly"] == {"FREQ": "WEEKLY", "INTERVAL": 2}

    def test_monthly_frequency(self):
        """Test monthly frequency mapping."""
        assert FREQUENCY_MAP["monthly"] == {"FREQ": "MONTHLY", "INTERVAL": 1}

    def test_quarterly_frequency(self):
        """Test quarterly frequency mapping."""
        assert FREQUENCY_MAP["quarterly"] == {"FREQ": "MONTHLY", "INTERVAL": 3}

    def test_yearly_frequency(self):
        """Test yearly frequency mapping."""
        assert FREQUENCY_MAP["yearly"] == {"FREQ": "YEARLY", "INTERVAL": 1}

    def test_annually_frequency(self):
        """Test annually frequency mapping (alias for yearly)."""
        assert FREQUENCY_MAP["annually"] == {"FREQ": "YEARLY", "INTERVAL": 1}

    def test_one_time_no_recurrence(self):
        """Test one-time has no recurrence rule."""
        assert FREQUENCY_MAP["one_time"] is None

    def test_all_frequencies_present(self):
        """Test all expected frequencies are in the map."""
        expected = ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly", "annually", "one_time"]
        for freq in expected:
            assert freq in FREQUENCY_MAP


class TestICalServiceCurrencySymbols:
    """Tests for currency symbol mapping."""

    @pytest.fixture
    def service(self):
        """Create ICalService instance with mocked db."""
        mock_db = AsyncMock()
        return ICalService(mock_db, uuid4())

    def test_gbp_symbol(self, service):
        """Test GBP currency symbol."""
        assert service._get_currency_symbol("GBP") == "£"

    def test_usd_symbol(self, service):
        """Test USD currency symbol."""
        assert service._get_currency_symbol("USD") == "$"

    def test_eur_symbol(self, service):
        """Test EUR currency symbol."""
        assert service._get_currency_symbol("EUR") == "€"

    def test_uah_symbol(self, service):
        """Test UAH currency symbol."""
        assert service._get_currency_symbol("UAH") == "₴"

    def test_cad_symbol(self, service):
        """Test CAD currency symbol."""
        assert service._get_currency_symbol("CAD") == "C$"

    def test_aud_symbol(self, service):
        """Test AUD currency symbol."""
        assert service._get_currency_symbol("AUD") == "A$"

    def test_jpy_symbol(self, service):
        """Test JPY currency symbol."""
        assert service._get_currency_symbol("JPY") == "¥"

    def test_chf_symbol(self, service):
        """Test CHF currency symbol."""
        assert service._get_currency_symbol("CHF") == "CHF "

    def test_cny_symbol(self, service):
        """Test CNY currency symbol."""
        assert service._get_currency_symbol("CNY") == "¥"

    def test_inr_symbol(self, service):
        """Test INR currency symbol."""
        assert service._get_currency_symbol("INR") == "₹"

    def test_brl_symbol(self, service):
        """Test BRL currency symbol."""
        assert service._get_currency_symbol("BRL") == "R$"

    def test_unknown_currency_fallback(self, service):
        """Test unknown currency returns code with space."""
        assert service._get_currency_symbol("XYZ") == "XYZ "

    def test_lowercase_currency(self, service):
        """Test currency code is case-insensitive."""
        assert service._get_currency_symbol("gbp") == "£"
        assert service._get_currency_symbol("usd") == "$"


class TestICalServiceRrule:
    """Tests for RRULE generation."""

    @pytest.fixture
    def service(self):
        """Create ICalService instance with mocked db."""
        mock_db = AsyncMock()
        return ICalService(mock_db, uuid4())

    def test_get_rrule_monthly(self, service):
        """Test RRULE for monthly frequency."""
        rrule = service._get_rrule("monthly")
        assert rrule == {"FREQ": "MONTHLY", "INTERVAL": 1}

    def test_get_rrule_weekly(self, service):
        """Test RRULE for weekly frequency."""
        rrule = service._get_rrule("weekly")
        assert rrule == {"FREQ": "WEEKLY", "INTERVAL": 1}

    def test_get_rrule_yearly(self, service):
        """Test RRULE for yearly frequency."""
        rrule = service._get_rrule("yearly")
        assert rrule == {"FREQ": "YEARLY", "INTERVAL": 1}

    def test_get_rrule_one_time_none(self, service):
        """Test RRULE is None for one-time payments."""
        rrule = service._get_rrule("one_time")
        assert rrule is None

    def test_get_rrule_with_spaces(self, service):
        """Test RRULE handles frequency with spaces."""
        rrule = service._get_rrule("one time")
        assert rrule is None

    def test_get_rrule_case_insensitive(self, service):
        """Test RRULE is case-insensitive."""
        rrule = service._get_rrule("MONTHLY")
        assert rrule == {"FREQ": "MONTHLY", "INTERVAL": 1}


class TestICalServiceCreateEvent:
    """Tests for event creation."""

    @pytest.fixture
    def service(self):
        """Create ICalService instance with mocked db."""
        mock_db = AsyncMock()
        return ICalService(mock_db, uuid4())

    @pytest.fixture
    def mock_subscription(self):
        """Create a mock subscription object."""
        sub = MagicMock()
        sub.id = uuid4()
        sub.name = "Netflix"
        sub.amount = 15.99
        sub.currency = "GBP"
        sub.frequency = "monthly"
        sub.payment_type = "subscription"
        sub.next_payment_date = date.today() + timedelta(days=7)
        sub.notes = "Test notes"
        sub.card_id = uuid4()
        sub.created_at = datetime.utcnow()
        return sub

    def test_create_event_basic(self, service, mock_subscription):
        """Test basic event creation."""
        event = service._create_event(mock_subscription, 365)
        assert event is not None

    def test_create_event_uid(self, service, mock_subscription):
        """Test event UID is based on subscription ID."""
        event = service._create_event(mock_subscription, 365)
        assert str(mock_subscription.id) in str(event.get("uid"))
        assert "@moneyflow.app" in str(event.get("uid"))

    def test_create_event_summary(self, service, mock_subscription):
        """Test event summary contains name and amount."""
        event = service._create_event(mock_subscription, 365)
        summary = str(event.get("summary"))
        assert "Netflix" in summary
        assert "£15.99" in summary
        assert "💰" in summary

    def test_create_event_categories(self, service, mock_subscription):
        """Test event has payment category."""
        event = service._create_event(mock_subscription, 365)
        categories = event.get("categories")
        # Categories is a vCategory object, convert to list
        cat_list = list(categories.cats) if hasattr(categories, "cats") else categories.to_ical().decode()
        assert "Payment" in str(cat_list)

    def test_create_event_no_next_payment_date(self, service, mock_subscription):
        """Test event is None when no next payment date."""
        mock_subscription.next_payment_date = None
        event = service._create_event(mock_subscription, 365)
        assert event is None

    def test_create_event_too_far_future(self, service, mock_subscription):
        """Test event is None when payment is too far in future."""
        mock_subscription.next_payment_date = date.today() + timedelta(days=400)
        event = service._create_event(mock_subscription, 365)
        assert event is None

    def test_create_event_has_alarm(self, service, mock_subscription):
        """Test event has alarm component."""
        event = service._create_event(mock_subscription, 365)
        # Check that subcomponents exist
        subcomponents = list(event.subcomponents)
        assert len(subcomponents) > 0
        alarm = subcomponents[0]
        assert str(alarm.get("action")) == "DISPLAY"

    def test_create_event_priority_high(self, service, mock_subscription):
        """Test high priority for large amounts."""
        mock_subscription.amount = 500.00
        event = service._create_event(mock_subscription, 365)
        assert event.get("priority") == 1

    def test_create_event_priority_medium(self, service, mock_subscription):
        """Test medium priority for medium amounts."""
        mock_subscription.amount = 150.00
        event = service._create_event(mock_subscription, 365)
        assert event.get("priority") == 5

    def test_create_event_priority_low(self, service, mock_subscription):
        """Test low priority for small amounts."""
        mock_subscription.amount = 10.00
        event = service._create_event(mock_subscription, 365)
        assert event.get("priority") == 9

    def test_create_event_with_enum_frequency(self, service, mock_subscription):
        """Test event creation with Enum frequency."""
        mock_frequency = MagicMock()
        mock_frequency.value = "monthly"
        mock_subscription.frequency = mock_frequency
        event = service._create_event(mock_subscription, 365)
        assert event is not None

    def test_create_event_with_enum_payment_type(self, service, mock_subscription):
        """Test event creation with Enum payment_type."""
        mock_payment_type = MagicMock()
        mock_payment_type.value = "subscription"
        mock_subscription.payment_type = mock_payment_type
        event = service._create_event(mock_subscription, 365)
        assert event is not None


class TestTokenGeneration:
    """Tests for token generation functions."""

    def test_generate_feed_url(self):
        """Test feed URL generation."""
        base_url = "https://api.moneyflow.app"
        user_id = uuid4()
        token = "abc123"

        url = generate_feed_url(base_url, user_id, token)

        assert base_url in url
        assert str(user_id) in url
        assert token in url
        assert "payments.ics" in url

    @pytest.mark.asyncio
    async def test_generate_ical_token_deterministic(self):
        """Test token generation is deterministic for same user."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.ical_token = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        token1 = await generate_ical_token(mock_db, user_id)

        # Generate expected token
        expected = hashlib.sha256(f"{user_id}-ical-feed".encode()).hexdigest()[:32]
        assert token1 == expected

    @pytest.mark.asyncio
    async def test_generate_ical_token_user_not_found(self):
        """Test token generation raises error for missing user."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await generate_ical_token(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_generate_ical_token_returns_existing(self):
        """Test token generation returns existing token if present."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.ical_token = "existing_token_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        token = await generate_ical_token(mock_db, user_id)

        assert token == "existing_token_123"

    @pytest.mark.asyncio
    async def test_validate_ical_token_returns_none(self):
        """Test token validation returns None (not yet implemented)."""
        mock_db = AsyncMock()
        result = await validate_ical_token(mock_db, "some_token")
        assert result is None


class TestICalServiceGenerateFeed:
    """Tests for feed generation."""

    @pytest.fixture
    def mock_subscription(self):
        """Create a mock subscription object."""
        sub = MagicMock()
        sub.id = uuid4()
        sub.name = "Spotify"
        sub.amount = 9.99
        sub.currency = "GBP"
        sub.frequency = "monthly"
        sub.payment_type = "subscription"
        sub.next_payment_date = date.today() + timedelta(days=14)
        sub.notes = None
        sub.card_id = None
        sub.created_at = datetime.utcnow()
        sub.is_active = True
        return sub

    @pytest.mark.asyncio
    async def test_generate_feed_empty(self):
        """Test generate feed with no subscriptions."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ICalService(mock_db, uuid4())
        feed_bytes = await service.generate_feed()

        feed_str = feed_bytes.decode("utf-8")
        assert "BEGIN:VCALENDAR" in feed_str
        assert "END:VCALENDAR" in feed_str
        assert "PRODID:-//Money Flow//Subscription Tracker//EN" in feed_str

    @pytest.mark.asyncio
    async def test_generate_feed_with_subscription(self, mock_subscription):
        """Test generate feed with a subscription."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        mock_db.execute.return_value = mock_result

        service = ICalService(mock_db, uuid4())
        feed_bytes = await service.generate_feed()

        feed_str = feed_bytes.decode("utf-8")
        assert "BEGIN:VEVENT" in feed_str
        assert "END:VEVENT" in feed_str
        assert "Spotify" in feed_str
        assert "£9.99" in feed_str

    @pytest.mark.asyncio
    async def test_generate_feed_has_rrule(self, mock_subscription):
        """Test feed includes RRULE for recurring payments."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        mock_db.execute.return_value = mock_result

        service = ICalService(mock_db, uuid4())
        feed_bytes = await service.generate_feed()

        feed_str = feed_bytes.decode("utf-8")
        assert "RRULE:FREQ=MONTHLY" in feed_str

    @pytest.mark.asyncio
    async def test_generate_feed_has_alarm(self, mock_subscription):
        """Test feed includes VALARM for reminders."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        mock_db.execute.return_value = mock_result

        service = ICalService(mock_db, uuid4())
        feed_bytes = await service.generate_feed()

        feed_str = feed_bytes.decode("utf-8")
        assert "BEGIN:VALARM" in feed_str
        assert "TRIGGER:-P1D" in feed_str

    @pytest.mark.asyncio
    async def test_generate_feed_calendar_properties(self):
        """Test feed has required calendar properties."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = ICalService(mock_db, uuid4())
        feed_bytes = await service.generate_feed()

        feed_str = feed_bytes.decode("utf-8")
        assert "VERSION:2.0" in feed_str
        assert "CALSCALE:GREGORIAN" in feed_str
        assert "METHOD:PUBLISH" in feed_str
        assert "X-WR-CALNAME:Money Flow - Payments" in feed_str
        assert "X-WR-TIMEZONE:UTC" in feed_str
