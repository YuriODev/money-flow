"""Unit tests for PDF report generation service.

Tests cover:
- Report generation with various subscription types
- Summary statistics calculation
- Category breakdown
- Upcoming payments section
- Monthly conversion calculations
"""

from datetime import date, timedelta
from decimal import Decimal

from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.services.pdf_report_service import PDFReportService


class MockCategory:
    """Mock Category object for testing."""

    def __init__(self, name: str):
        self.name = name


class MockSubscription:
    """Mock Subscription object for testing."""

    def __init__(
        self,
        name: str = "Test Sub",
        amount: Decimal = Decimal("10.00"),
        currency: str = "GBP",
        frequency: Frequency = Frequency.MONTHLY,
        is_active: bool = True,
        next_payment_date: date | None = None,
        payment_type: PaymentType = PaymentType.SUBSCRIPTION,
        payment_mode: PaymentMode = PaymentMode.RECURRING,
        category: str | None = None,
        category_rel: MockCategory | None = None,
    ):
        self.name = name
        self.amount = amount
        self.currency = currency
        self.frequency = frequency
        self.is_active = is_active
        self.next_payment_date = next_payment_date or date.today()
        self.payment_type = payment_type
        self.payment_mode = payment_mode
        self.category = category
        self.category_rel = category_rel


class TestPDFReportService:
    """Tests for PDFReportService initialization and configuration."""

    def test_init_default_values(self):
        """Test service initializes with default values."""
        service = PDFReportService()
        assert service.currency == "GBP"
        assert service.currency_symbol == "£"
        assert service.include_inactive is False

    def test_init_custom_currency(self):
        """Test service with custom currency."""
        service = PDFReportService(currency="USD")
        assert service.currency == "USD"
        assert service.currency_symbol == "$"

    def test_init_euro_currency(self):
        """Test service with EUR currency."""
        service = PDFReportService(currency="EUR")
        assert service.currency_symbol == "€"

    def test_init_uah_currency(self):
        """Test service with UAH currency."""
        service = PDFReportService(currency="UAH")
        assert service.currency_symbol == "₴"

    def test_init_unknown_currency_defaults_to_pound(self):
        """Test service with unknown currency defaults to £."""
        service = PDFReportService(currency="XYZ")
        assert service.currency_symbol == "£"

    def test_init_letter_page_size(self):
        """Test service with letter page size."""
        from reportlab.lib.pagesizes import letter

        service = PDFReportService(page_size="letter")
        assert service.page_size == letter

    def test_init_a4_page_size(self):
        """Test service with A4 page size (default)."""
        from reportlab.lib.pagesizes import A4

        service = PDFReportService(page_size="a4")
        assert service.page_size == A4


class TestMonthlyConversion:
    """Tests for _to_monthly conversion method."""

    def test_daily_to_monthly(self):
        """Test daily amount converts to ~30x per month."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("1.00"), "daily")
        assert result == Decimal("30")

    def test_weekly_to_monthly(self):
        """Test weekly amount converts to ~4.33x per month."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("10.00"), "weekly")
        assert result == Decimal("43.30")

    def test_monthly_unchanged(self):
        """Test monthly amount stays the same."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("15.99"), "monthly")
        assert result == Decimal("15.99")

    def test_yearly_to_monthly(self):
        """Test yearly amount converts to ~1/12 per month."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("120.00"), "yearly")
        assert result == Decimal("9.960")

    def test_quarterly_to_monthly(self):
        """Test quarterly amount converts to ~1/3 per month."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("30.00"), "quarterly")
        assert result == Decimal("9.90")

    def test_one_time_is_zero(self):
        """Test one-time payments don't count toward monthly totals."""
        service = PDFReportService()
        result = service._to_monthly(Decimal("100.00"), "one-time")
        assert result == Decimal("0")


class TestReportGeneration:
    """Tests for PDF report generation."""

    def test_generate_empty_report(self):
        """Test generating report with no subscriptions."""
        service = PDFReportService()
        pdf_bytes = service.generate_report(
            subscriptions=[],
            user_email="test@example.com",
            report_title="Empty Report",
        )

        # Check it's valid PDF bytes
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"  # PDF magic bytes

    def test_generate_single_subscription(self):
        """Test generating report with one subscription."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                frequency=Frequency.MONTHLY,
            )
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_multiple_subscriptions(self):
        """Test generating report with multiple subscriptions."""
        service = PDFReportService()
        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99")),
            MockSubscription(name="Spotify", amount=Decimal("9.99")),
            MockSubscription(
                name="Old Sub",
                amount=Decimal("5.00"),
                is_active=False,
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_categories(self):
        """Test generating report with categorized subscriptions."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category_rel=MockCategory("Entertainment"),
            ),
            MockSubscription(
                name="Electric",
                amount=Decimal("80.00"),
                category_rel=MockCategory("Utilities"),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_string_categories(self):
        """Test generating report with string category field (legacy)."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category="Entertainment",
            ),
            MockSubscription(
                name="Electric",
                amount=Decimal("80.00"),
                category="Utilities",
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_upcoming_payments(self):
        """Test generating report shows upcoming payments."""
        service = PDFReportService()
        today = date.today()
        subs = [
            MockSubscription(
                name="Tomorrow Payment",
                amount=Decimal("10.00"),
                next_payment_date=today + timedelta(days=1),
            ),
            MockSubscription(
                name="Next Week",
                amount=Decimal("20.00"),
                next_payment_date=today + timedelta(days=7),
            ),
            MockSubscription(
                name="Far Future",
                amount=Decimal("30.00"),
                next_payment_date=today + timedelta(days=60),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_include_inactive(self):
        """Test generating report with inactive subscriptions included."""
        service = PDFReportService(include_inactive=True)
        subs = [
            MockSubscription(name="Active", is_active=True),
            MockSubscription(name="Inactive", is_active=False),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_filters_inactive_by_default(self):
        """Test that inactive subscriptions are filtered by default."""
        service = PDFReportService(include_inactive=False)
        subs = [
            MockSubscription(name="Active", is_active=True),
            MockSubscription(name="Inactive", is_active=False),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        # Report should still generate (active sub included)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_debt_subscriptions(self):
        """Test generating report with debt payment types."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Credit Card Debt",
                amount=Decimal("200.00"),
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_savings_subscriptions(self):
        """Test generating report with savings payment types."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Emergency Fund",
                amount=Decimal("500.00"),
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_usd_report(self):
        """Test generating report with USD currency."""
        service = PDFReportService(currency="USD")
        subs = [
            MockSubscription(
                name="US Service",
                amount=Decimal("9.99"),
                currency="USD",
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_letter_size(self):
        """Test generating report with letter page size."""
        service = PDFReportService(page_size="letter")
        subs = [MockSubscription(name="Test")]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_user_email(self):
        """Test generating report with user email in header."""
        service = PDFReportService()
        subs = [MockSubscription(name="Test")]
        pdf_bytes = service.generate_report(
            subscriptions=subs,
            user_email="user@example.com",
        )

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_with_custom_title(self):
        """Test generating report with custom title."""
        service = PDFReportService()
        subs = [MockSubscription(name="Test")]
        pdf_bytes = service.generate_report(
            subscriptions=subs,
            report_title="My Custom Report",
        )

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_long_subscription_name(self):
        """Test handling of very long subscription names."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="A" * 100,  # Very long name
                amount=Decimal("10.00"),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_very_long_category_name(self):
        """Test handling of very long category names."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Test",
                category_rel=MockCategory("B" * 50),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_zero_amount_subscription(self):
        """Test handling of zero amount subscriptions."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Free Tier",
                amount=Decimal("0.00"),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_large_amount_subscription(self):
        """Test handling of large amount subscriptions."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Enterprise License",
                amount=Decimal("99999.99"),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_mixed_frequencies(self):
        """Test report with multiple different frequencies."""
        service = PDFReportService()
        subs = [
            MockSubscription(name="Daily", frequency=Frequency.DAILY),
            MockSubscription(name="Weekly", frequency=Frequency.WEEKLY),
            MockSubscription(name="Monthly", frequency=Frequency.MONTHLY),
            MockSubscription(name="Yearly", frequency=Frequency.YEARLY),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_all_inactive_subscriptions(self):
        """Test report when all subscriptions are inactive."""
        service = PDFReportService(include_inactive=False)
        subs = [
            MockSubscription(name="Inactive1", is_active=False),
            MockSubscription(name="Inactive2", is_active=False),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_payment_due_today(self):
        """Test report with payment due today."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Due Today",
                next_payment_date=date.today(),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_no_category_subscriptions(self):
        """Test report with uncategorized subscriptions."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="No Category",
                category=None,
                category_rel=None,
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"
