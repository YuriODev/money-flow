"""Tests for HistoricalQueryService.

Tests cover:
- Temporal expression parsing
- Date range resolution
- Query type detection
- Historical data retrieval
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.services.historical_query_service import (
    DateRange,
    HistoricalQueryService,
    HistoricalSubscription,
    get_historical_query_service,
)


class TestHistoricalQueryServiceInit:
    """Tests for HistoricalQueryService initialization."""

    def test_init_sets_db(self):
        """Test that initialization sets database session."""
        mock_db = MagicMock()
        service = HistoricalQueryService(mock_db)

        assert service.db == mock_db

    def test_get_historical_query_service_factory(self):
        """Test factory function creates service."""
        mock_db = MagicMock()
        service = get_historical_query_service(mock_db)

        assert isinstance(service, HistoricalQueryService)


class TestTemporalParsing:
    """Tests for temporal expression parsing."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return HistoricalQueryService(MagicMock())

    def test_parse_today(self, service):
        """Test parsing 'today'."""
        result = service._parse_temporal_expression("show today's subscriptions")
        today = date.today()

        assert result.start == today
        assert result.end == today
        assert result.label == "today"

    def test_parse_yesterday(self, service):
        """Test parsing 'yesterday'."""
        result = service._parse_temporal_expression("what happened yesterday")
        yesterday = date.today() - timedelta(days=1)

        assert result.start == yesterday
        assert result.end == yesterday
        assert result.label == "yesterday"

    def test_parse_this_week(self, service):
        """Test parsing 'this week'."""
        result = service._parse_temporal_expression("show this week")
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        assert result.start == week_start
        assert result.end == today
        assert result.label == "this week"

    def test_parse_last_week(self, service):
        """Test parsing 'last week'."""
        result = service._parse_temporal_expression("what did I add last week")
        today = date.today()
        last_week_start = today - timedelta(days=today.weekday() + 7)

        assert result.start == last_week_start
        assert result.label == "last week"

    def test_parse_this_month(self, service):
        """Test parsing 'this month'."""
        result = service._parse_temporal_expression("subscriptions this month")
        today = date.today()

        assert result.start.month == today.month
        assert result.start.day == 1
        assert result.label == "this month"

    def test_parse_last_month(self, service):
        """Test parsing 'last month'."""
        result = service._parse_temporal_expression("what did I add last month")

        assert result.label == "last month"
        # Should be in the previous month
        today = date.today()
        assert result.start.month != today.month or result.start.year != today.year

    def test_parse_this_year(self, service):
        """Test parsing 'this year'."""
        result = service._parse_temporal_expression("spending this year")
        today = date.today()

        assert result.start == date(today.year, 1, 1)
        assert result.end == today
        assert result.label == "this year"

    def test_parse_last_year(self, service):
        """Test parsing 'last year'."""
        result = service._parse_temporal_expression("what was I paying last year")
        today = date.today()

        assert result.start.year == today.year - 1
        assert result.label == str(today.year - 1)

    def test_parse_days_ago(self, service):
        """Test parsing 'N days ago'."""
        result = service._parse_temporal_expression("5 days ago")
        target = date.today() - timedelta(days=5)

        assert result.start == target

    def test_parse_weeks_ago(self, service):
        """Test parsing 'N weeks ago'."""
        result = service._parse_temporal_expression("2 weeks ago")
        target = date.today() - timedelta(weeks=2)

        assert result.start == target

    def test_parse_months_ago(self, service):
        """Test parsing 'N months ago'."""
        result = service._parse_temporal_expression("3 months ago")

        # Should be approximately 3 months back
        today = date.today()
        diff = (today.year - result.start.year) * 12 + (today.month - result.start.month)
        assert diff == 3

    def test_parse_month_name_january(self, service):
        """Test parsing month name 'January'."""
        result = service._parse_temporal_expression("subscriptions in january")

        assert result.start.month == 1
        assert result.start.day == 1
        assert result.label.lower() == "january"

    def test_parse_month_name_abbreviated(self, service):
        """Test parsing abbreviated month name."""
        result = service._parse_temporal_expression("what about in dec")

        assert result.start.month == 12

    def test_parse_specific_year(self, service):
        """Test parsing specific year."""
        result = service._parse_temporal_expression("spending in 2024")

        assert result.start == date(2024, 1, 1)
        assert result.end == date(2024, 12, 31)
        assert result.label == "2024"

    def test_parse_quarter(self, service):
        """Test parsing quarter expressions."""
        result = service._parse_temporal_expression("Q1 spending")
        today = date.today()

        assert result.start.month == 1
        assert result.label == f"Q1 {today.year}"

    def test_default_to_this_month(self, service):
        """Test default to this month if no temporal expression."""
        result = service._parse_temporal_expression("show me subscriptions")
        today = date.today()

        assert result.start.month == today.month
        assert result.label == "this month"


class TestQueryTypeDetection:
    """Tests for query type detection."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return HistoricalQueryService(MagicMock())

    def test_detect_added_query(self, service):
        """Test detecting 'added' query type."""
        assert service._detect_query_type("what did I add") == "added"
        assert service._detect_query_type("subscriptions I added") == "added"
        assert service._detect_query_type("new subscriptions") == "added"

    def test_detect_cancelled_query(self, service):
        """Test detecting 'cancelled' query type."""
        assert service._detect_query_type("what did I cancel") == "cancelled"
        assert service._detect_query_type("removed subscriptions") == "cancelled"

    def test_detect_spending_query(self, service):
        """Test detecting 'spending' query type."""
        assert service._detect_query_type("how much was I spending") == "spending"
        assert service._detect_query_type("total cost") == "spending"
        assert service._detect_query_type("what did I pay") == "spending"

    def test_detect_default_active(self, service):
        """Test default to 'active' query type."""
        assert service._detect_query_type("show subscriptions") == "active"
        assert service._detect_query_type("list all") == "active"


class TestGetMonthRange:
    """Tests for month range calculation."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return HistoricalQueryService(MagicMock())

    def test_january_range(self, service):
        """Test January range."""
        result = service._get_month_range(2025, 1, "January")

        assert result.start == date(2025, 1, 1)
        assert result.end == date(2025, 1, 31)

    def test_february_range_non_leap(self, service):
        """Test February range in non-leap year."""
        result = service._get_month_range(2025, 2, "February")

        assert result.start == date(2025, 2, 1)
        assert result.end == date(2025, 2, 28)

    def test_december_range(self, service):
        """Test December range."""
        result = service._get_month_range(2025, 12, "December")

        assert result.start == date(2025, 12, 1)
        assert result.end == date(2025, 12, 31)


class TestCalculateMonthlyTotal:
    """Tests for monthly total calculation."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return HistoricalQueryService(MagicMock())

    def test_empty_list_returns_zero(self, service):
        """Test empty list returns zero."""
        result = service._calculate_monthly_total([])

        assert result == Decimal("0")

    def test_active_subscription_counted(self, service):
        """Test active subscriptions are counted."""
        sub = HistoricalSubscription(
            id="sub-1",
            name="Netflix",
            amount=Decimal("15"),
            frequency="monthly",
            category="entertainment",
            created_at=date.today(),
            was_active=True,
        )

        result = service._calculate_monthly_total([sub])

        assert result == Decimal("15")

    def test_inactive_subscription_not_counted(self, service):
        """Test inactive subscriptions are not counted."""
        sub = HistoricalSubscription(
            id="sub-1",
            name="Netflix",
            amount=Decimal("15"),
            frequency="monthly",
            category="entertainment",
            created_at=date.today(),
            was_active=False,
        )

        result = service._calculate_monthly_total([sub])

        assert result == Decimal("0")


class TestGenerateSummary:
    """Tests for summary generation."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return HistoricalQueryService(MagicMock())

    @pytest.fixture
    def date_range(self):
        """Create test date range."""
        return DateRange(
            start=date(2025, 1, 1),
            end=date(2025, 1, 31),
            label="January 2025",
        )

    def test_added_summary_with_results(self, service, date_range):
        """Test added summary with results."""
        subs = [
            HistoricalSubscription(
                id="sub-1",
                name="Netflix",
                amount=Decimal("15"),
                frequency="monthly",
                category="entertainment",
                created_at=date.today(),
                was_active=True,
            )
        ]

        result = service._generate_summary(
            query_type="added",
            date_range=date_range,
            subscriptions=subs,
            total_monthly=Decimal("15"),
        )

        assert "Added" in result
        assert "Netflix" in result
        assert "January 2025" in result

    def test_added_summary_empty(self, service, date_range):
        """Test added summary with no results."""
        result = service._generate_summary(
            query_type="added",
            date_range=date_range,
            subscriptions=[],
            total_monthly=Decimal("0"),
        )

        assert "No subscriptions were added" in result

    def test_spending_summary(self, service, date_range):
        """Test spending summary."""
        subs = [
            HistoricalSubscription(
                id="sub-1",
                name="Netflix",
                amount=Decimal("15"),
                frequency="monthly",
                category="entertainment",
                created_at=date.today(),
                was_active=True,
            )
        ]

        result = service._generate_summary(
            query_type="spending",
            date_range=date_range,
            subscriptions=subs,
            total_monthly=Decimal("15"),
        )

        assert "£15" in result
        assert "January 2025" in result


class TestDateRange:
    """Tests for DateRange dataclass."""

    def test_date_range_creation(self):
        """Test DateRange creation."""
        range_ = DateRange(
            start=date(2025, 1, 1),
            end=date(2025, 1, 31),
            label="January 2025",
        )

        assert range_.start == date(2025, 1, 1)
        assert range_.end == date(2025, 1, 31)
        assert range_.label == "January 2025"


class TestHistoricalSubscription:
    """Tests for HistoricalSubscription dataclass."""

    def test_historical_subscription_creation(self):
        """Test HistoricalSubscription creation."""
        sub = HistoricalSubscription(
            id="sub-1",
            name="Netflix",
            amount=Decimal("15.99"),
            frequency="monthly",
            category="entertainment",
            created_at=date(2025, 1, 1),
            was_active=True,
        )

        assert sub.id == "sub-1"
        assert sub.name == "Netflix"
        assert sub.amount == Decimal("15.99")
        assert sub.was_active is True
