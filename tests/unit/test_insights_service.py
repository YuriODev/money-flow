"""Tests for InsightsService.

Tests cover:
- Spending trend analysis
- Category breakdown
- Renewal predictions
- Cancellation recommendations
- Summary generation
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from src.models.subscription import Frequency
from src.services.insights_service import (
    CancellationRecommendation,
    CategoryBreakdown,
    InsightsService,
    RenewalPrediction,
    SpendingInsights,
    SpendingTrend,
    get_insights_service,
)


class TestInsightsServiceInit:
    """Tests for InsightsService initialization."""

    def test_init_sets_db(self):
        """Test that initialization sets database session."""
        mock_db = MagicMock()
        service = InsightsService(mock_db)

        assert service.db == mock_db

    def test_get_insights_service_factory(self):
        """Test factory function creates service."""
        mock_db = MagicMock()
        service = get_insights_service(mock_db)

        assert isinstance(service, InsightsService)
        assert service.db == mock_db


class TestMonthlyAmountConversion:
    """Tests for amount conversion to monthly."""

    def test_daily_to_monthly(self):
        """Test daily amount conversion."""
        service = InsightsService(MagicMock())

        result = service._to_monthly_amount(Decimal("1"), Frequency.DAILY)

        assert result == Decimal("30")

    def test_weekly_to_monthly(self):
        """Test weekly amount conversion."""
        service = InsightsService(MagicMock())

        result = service._to_monthly_amount(Decimal("10"), Frequency.WEEKLY)

        assert result == Decimal("43.3")

    def test_monthly_stays_same(self):
        """Test monthly amount stays the same."""
        service = InsightsService(MagicMock())

        result = service._to_monthly_amount(Decimal("15"), Frequency.MONTHLY)

        assert result == Decimal("15")

    def test_yearly_to_monthly(self):
        """Test yearly amount conversion."""
        service = InsightsService(MagicMock())

        result = service._to_monthly_amount(Decimal("120"), Frequency.YEARLY)

        # 120 * 0.083 ≈ 9.96
        assert result < Decimal("10")


class TestDailyAmountConversion:
    """Tests for amount conversion to daily."""

    def test_daily_stays_same(self):
        """Test daily amount stays the same."""
        service = InsightsService(MagicMock())

        result = service._to_daily_amount(Decimal("5"), Frequency.DAILY)

        assert result == Decimal("5")

    def test_monthly_to_daily(self):
        """Test monthly to daily conversion."""
        service = InsightsService(MagicMock())

        result = service._to_daily_amount(Decimal("30"), Frequency.MONTHLY)

        assert result == Decimal("1")


class TestCalculateTotalMonthly:
    """Tests for total monthly calculation."""

    def test_empty_list_returns_zero(self):
        """Test empty subscription list returns zero."""
        service = InsightsService(MagicMock())

        result = service._calculate_total_monthly([])

        assert result == Decimal("0")

    def test_single_subscription(self):
        """Test single subscription calculation."""
        service = InsightsService(MagicMock())
        sub = MagicMock()
        sub.amount = Decimal("15.99")
        sub.frequency = Frequency.MONTHLY

        result = service._calculate_total_monthly([sub])

        assert result == Decimal("15.99")

    def test_multiple_subscriptions(self):
        """Test multiple subscriptions calculation."""
        service = InsightsService(MagicMock())

        sub1 = MagicMock()
        sub1.amount = Decimal("10")
        sub1.frequency = Frequency.MONTHLY

        sub2 = MagicMock()
        sub2.amount = Decimal("20")
        sub2.frequency = Frequency.MONTHLY

        result = service._calculate_total_monthly([sub1, sub2])

        assert result == Decimal("30")


class TestAnalyzeCategories:
    """Tests for category analysis."""

    def test_empty_list_returns_empty(self):
        """Test empty subscription list returns empty breakdown."""
        service = InsightsService(MagicMock())

        result = service._analyze_categories([], Decimal("0"))

        assert result == []

    def test_single_category(self):
        """Test single category breakdown."""
        service = InsightsService(MagicMock())

        sub = MagicMock()
        sub.name = "Netflix"
        sub.amount = Decimal("15")
        sub.frequency = Frequency.MONTHLY
        sub.category = "entertainment"

        result = service._analyze_categories([sub], Decimal("15"))

        assert len(result) == 1
        assert result[0].category == "entertainment"
        assert result[0].total == Decimal("15")
        assert result[0].percentage == 100.0

    def test_multiple_categories_sorted_by_total(self):
        """Test categories are sorted by total descending."""
        service = InsightsService(MagicMock())

        sub1 = MagicMock()
        sub1.name = "Netflix"
        sub1.amount = Decimal("10")
        sub1.frequency = Frequency.MONTHLY
        sub1.category = "entertainment"

        sub2 = MagicMock()
        sub2.name = "Gym"
        sub2.amount = Decimal("50")
        sub2.frequency = Frequency.MONTHLY
        sub2.category = "health"

        result = service._analyze_categories([sub1, sub2], Decimal("60"))

        assert result[0].category == "health"
        assert result[1].category == "entertainment"

    def test_uncategorized_subscriptions(self):
        """Test subscriptions without category."""
        service = InsightsService(MagicMock())

        sub = MagicMock()
        sub.name = "Random"
        sub.amount = Decimal("10")
        sub.frequency = Frequency.MONTHLY
        sub.category = None

        result = service._analyze_categories([sub], Decimal("10"))

        assert result[0].category == "uncategorized"


class TestPredictRenewals:
    """Tests for renewal predictions."""

    def test_empty_list_returns_empty(self):
        """Test empty subscription list returns no predictions."""
        service = InsightsService(MagicMock())

        result = service._predict_renewals([], days_ahead=30)

        assert result == []

    def test_renewal_within_range(self):
        """Test subscription with renewal within range."""
        service = InsightsService(MagicMock())
        today = date.today()

        sub = MagicMock()
        sub.id = "sub-1"
        sub.name = "Netflix"
        sub.amount = Decimal("15.99")
        sub.next_payment_date = today + timedelta(days=5)
        sub.frequency = Frequency.MONTHLY

        result = service._predict_renewals([sub], days_ahead=30)

        assert len(result) == 1
        assert result[0].subscription_name == "Netflix"
        assert result[0].days_until == 5

    def test_renewal_outside_range(self):
        """Test subscription with renewal outside range."""
        service = InsightsService(MagicMock())
        today = date.today()

        sub = MagicMock()
        sub.id = "sub-1"
        sub.name = "Netflix"
        sub.next_payment_date = today + timedelta(days=60)
        sub.frequency = Frequency.MONTHLY

        result = service._predict_renewals([sub], days_ahead=30)

        assert len(result) == 0

    def test_annual_subscription_flagged(self):
        """Test annual subscriptions are flagged."""
        service = InsightsService(MagicMock())
        today = date.today()

        sub = MagicMock()
        sub.id = "sub-1"
        sub.name = "Software"
        sub.amount = Decimal("99")
        sub.next_payment_date = today + timedelta(days=5)
        sub.frequency = Frequency.YEARLY

        result = service._predict_renewals([sub], days_ahead=30)

        assert result[0].is_annual is True


class TestGenerateRecommendations:
    """Tests for recommendation generation."""

    def test_empty_list_returns_empty(self):
        """Test empty subscription list returns no recommendations."""
        service = InsightsService(MagicMock())

        result = service._generate_recommendations([])

        assert result == []

    def test_duplicate_category_recommendation(self):
        """Test recommendation for duplicate categories."""
        service = InsightsService(MagicMock())

        sub1 = MagicMock()
        sub1.id = "sub-1"
        sub1.name = "Netflix"
        sub1.amount = Decimal("15")
        sub1.frequency = Frequency.MONTHLY
        sub1.category = "entertainment"

        sub2 = MagicMock()
        sub2.id = "sub-2"
        sub2.name = "Disney+"
        sub2.amount = Decimal("10")
        sub2.frequency = Frequency.MONTHLY
        sub2.category = "entertainment"

        result = service._generate_recommendations([sub1, sub2])

        # Should recommend the cheaper one for review
        assert len(result) >= 1
        assert any("entertainment" in r.reason.lower() for r in result)

    def test_high_cost_recommendation(self):
        """Test recommendation for high-cost subscriptions."""
        service = InsightsService(MagicMock())

        sub = MagicMock()
        sub.id = "sub-1"
        sub.name = "Expensive"
        sub.amount = Decimal("100")
        sub.frequency = Frequency.MONTHLY
        sub.category = "software"

        result = service._generate_recommendations([sub])

        assert len(result) >= 1
        assert any("high" in r.reason.lower() for r in result)


class TestGenerateSummary:
    """Tests for summary generation."""

    def test_basic_summary(self):
        """Test basic summary generation."""
        service = InsightsService(MagicMock())

        summary = service._generate_summary(
            total_monthly=Decimal("100"),
            trends=[],
            category_breakdown=[],
            recommendations=[],
        )

        assert "£100" in summary
        assert "£1200" in summary  # yearly

    def test_summary_with_top_category(self):
        """Test summary includes top category."""
        service = InsightsService(MagicMock())

        category = CategoryBreakdown(
            category="entertainment",
            total=Decimal("50"),
            percentage=50.0,
            subscription_count=2,
            subscriptions=["Netflix", "Spotify"],
        )

        summary = service._generate_summary(
            total_monthly=Decimal("100"),
            trends=[],
            category_breakdown=[category],
            recommendations=[],
        )

        assert "entertainment" in summary
        assert "50%" in summary

    def test_summary_with_trend_increase(self):
        """Test summary includes spending increase."""
        service = InsightsService(MagicMock())

        trends = [
            SpendingTrend(period="2025-01", total=Decimal("90"), change=Decimal("0")),
            SpendingTrend(
                period="2025-02",
                total=Decimal("100"),
                change=Decimal("10"),
                change_percent=11.1,
            ),
        ]

        summary = service._generate_summary(
            total_monthly=Decimal("100"),
            trends=trends,
            category_breakdown=[],
            recommendations=[],
        )

        assert "increased" in summary.lower()

    def test_summary_with_recommendations(self):
        """Test summary includes recommendation count."""
        service = InsightsService(MagicMock())

        recs = [
            CancellationRecommendation(
                subscription_name="Netflix",
                subscription_id="sub-1",
                reason="test",
                potential_savings=Decimal("15"),
                confidence=0.8,
            )
        ]

        summary = service._generate_summary(
            total_monthly=Decimal("100"),
            trends=[],
            category_breakdown=[],
            recommendations=recs,
        )

        assert "savings" in summary.lower()


class TestSpendingDataclasses:
    """Tests for dataclass creation."""

    def test_spending_trend_creation(self):
        """Test SpendingTrend dataclass."""
        trend = SpendingTrend(
            period="2025-01",
            total=Decimal("100"),
            change=Decimal("10"),
            change_percent=10.0,
            subscription_count=5,
        )

        assert trend.period == "2025-01"
        assert trend.total == Decimal("100")

    def test_category_breakdown_creation(self):
        """Test CategoryBreakdown dataclass."""
        breakdown = CategoryBreakdown(
            category="entertainment",
            total=Decimal("50"),
            percentage=50.0,
            subscription_count=2,
            subscriptions=["Netflix", "Spotify"],
        )

        assert breakdown.category == "entertainment"
        assert len(breakdown.subscriptions) == 2

    def test_renewal_prediction_creation(self):
        """Test RenewalPrediction dataclass."""
        prediction = RenewalPrediction(
            subscription_name="Netflix",
            subscription_id="sub-1",
            renewal_date=date.today(),
            amount=Decimal("15.99"),
            days_until=5,
            is_annual=False,
        )

        assert prediction.subscription_name == "Netflix"
        assert prediction.days_until == 5

    def test_cancellation_recommendation_creation(self):
        """Test CancellationRecommendation dataclass."""
        rec = CancellationRecommendation(
            subscription_name="Netflix",
            subscription_id="sub-1",
            reason="Duplicate service",
            potential_savings=Decimal("15"),
            confidence=0.8,
        )

        assert rec.subscription_name == "Netflix"
        assert rec.confidence == 0.8

    def test_spending_insights_creation(self):
        """Test SpendingInsights dataclass."""
        insights = SpendingInsights(
            total_monthly=Decimal("100"),
            total_yearly=Decimal("1200"),
            trends=[],
            category_breakdown=[],
            renewal_predictions=[],
            recommendations=[],
            summary="Test summary",
        )

        assert insights.total_monthly == Decimal("100")
        assert insights.summary == "Test summary"
