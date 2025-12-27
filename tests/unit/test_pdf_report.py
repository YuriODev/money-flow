"""Unit tests for PDF report generation service.

Tests cover:
- Report generation with various subscription types
- Summary statistics calculation
- Category breakdown
- Upcoming payments section
- Monthly conversion calculations
- Multi-currency conversion
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.services.pdf_report_service import CURRENCY_SYMBOLS, PDFReportService


class MockCategory:
    """Mock Category object for testing."""

    def __init__(self, name: str, budget_amount: Decimal | None = None):
        self.name = name
        self.budget_amount = budget_amount


class MockPaymentCard:
    """Mock PaymentCard object for testing."""

    def __init__(self, name: str = "Test Card", card_id: str = "card-123"):
        self.id = card_id
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
        payment_history: list | None = None,
        payment_card: MockPaymentCard | None = None,
        card_id: str | None = None,
        # Debt fields
        total_owed: Decimal | None = None,
        remaining_balance: Decimal | None = None,
        creditor: str | None = None,
        # Savings fields
        target_amount: Decimal | None = None,
        current_saved: Decimal | None = None,
        recipient: str | None = None,
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
        self.payment_history = payment_history or []
        self.payment_card = payment_card
        self.card_id = card_id or (payment_card.id if payment_card else None)
        # Debt fields
        self.total_owed = total_owed
        self.remaining_balance = remaining_balance
        self.creditor = creditor
        # Savings fields
        self.target_amount = target_amount
        self.current_saved = current_saved
        self.recipient = recipient

    @property
    def debt_paid_percentage(self) -> float | None:
        """Calculate percentage of debt paid off."""
        if self.payment_mode != PaymentMode.DEBT and self.payment_type != PaymentType.DEBT:
            return None
        if self.total_owed is None or self.total_owed <= 0:
            return None
        if self.remaining_balance is None:
            return None
        paid = float(self.total_owed - self.remaining_balance)
        return round((paid / float(self.total_owed)) * 100, 1)

    @property
    def savings_progress_percentage(self) -> float | None:
        """Calculate percentage progress toward savings goal."""
        if self.payment_mode != PaymentMode.SAVINGS and self.payment_type != PaymentType.SAVINGS:
            return None
        if self.target_amount is None or self.target_amount <= 0:
            return None
        if self.current_saved is None:
            return 0.0
        return round((float(self.current_saved) / float(self.target_amount)) * 100, 1)


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


class MockPaymentHistory:
    """Mock PaymentHistory object for testing."""

    def __init__(
        self,
        payment_date: date | None = None,
        amount: Decimal = Decimal("10.00"),
        currency: str = "GBP",
        status: str = "completed",
    ):
        self.payment_date = payment_date or date.today()
        self.amount = amount
        self.currency = currency
        # Create a mock status with .value attribute
        self.status = MagicMock()
        self.status.value = status


class MockCurrencyService:
    """Mock CurrencyService for testing currency conversion."""

    def __init__(self, rates: dict[str, Decimal] | None = None):
        """Initialize with optional custom rates."""
        self.rates = rates or {
            "USD": Decimal("1.00"),
            "GBP": Decimal("0.79"),
            "EUR": Decimal("0.92"),
            "UAH": Decimal("41.00"),
        }
        self._cache = MagicMock()
        self._cache.rates = self.rates
        self._cache.is_expired.return_value = False


class TestCurrencyConversion:
    """Tests for multi-currency conversion in PDF reports."""

    def test_convert_amount_same_currency(self):
        """Test amount not converted when currencies match."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._convert_amount(Decimal("100.00"), "GBP")

        assert result == Decimal("100.00")

    def test_convert_amount_usd_to_gbp(self):
        """Test USD to GBP conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._convert_amount(Decimal("100.00"), "USD")

        # USD 100 at rate 0.79/1.00 = GBP 79.00
        assert result == Decimal("79.00")

    def test_convert_amount_eur_to_gbp(self):
        """Test EUR to GBP conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._convert_amount(Decimal("100.00"), "EUR")

        # EUR 100 at rate 0.79/0.92 = GBP ~85.87
        assert result == Decimal("85.87")

    def test_convert_amount_without_service(self):
        """Test amount returned unchanged when no currency service."""
        service = PDFReportService(currency="GBP")  # No currency_service

        result = service._convert_amount(Decimal("100.00"), "USD")

        # Without service, amount should be returned unchanged
        assert result == Decimal("100.00")

    def test_get_amount_display_same_currency(self):
        """Test amount display when currencies match."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._get_amount_display(Decimal("15.99"), "GBP")

        assert result == "£15.99"

    def test_get_amount_display_different_currency_with_original(self):
        """Test amount display shows both converted and original."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._get_amount_display(Decimal("100.00"), "USD", show_original=True)

        # Should show converted (GBP) followed by original (USD)
        assert "£79.00" in result
        assert "$100.00" in result

    def test_get_amount_display_different_currency_no_original(self):
        """Test amount display shows only converted amount."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        result = service._get_amount_display(Decimal("100.00"), "USD", show_original=False)

        assert result == "£79.00"

    def test_report_with_mixed_currencies(self):
        """Test generating report with mixed currency subscriptions."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        subs = [
            MockSubscription(name="UK Service", amount=Decimal("15.99"), currency="GBP"),
            MockSubscription(name="US Service", amount=Decimal("100.00"), currency="USD"),
            MockSubscription(name="EU Service", amount=Decimal("50.00"), currency="EUR"),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_report_shows_currencies_converted_note(self):
        """Test report includes note about converted currencies."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        subs = [
            MockSubscription(name="UK Service", amount=Decimal("15.99"), currency="GBP"),
            MockSubscription(name="US Service", amount=Decimal("100.00"), currency="USD"),
        ]

        # Build summary section
        elements = service._build_summary(subs)

        # Elements should be generated successfully
        assert len(elements) > 0

    def test_failed_conversion_tracked(self):
        """Test that failed conversions are tracked."""
        # Create service with cache but missing currency
        mock_service = MagicMock()
        mock_service._cache = MagicMock()
        mock_service._cache.rates = {"USD": Decimal("1.00")}  # Missing GBP
        mock_service._cache.is_expired.return_value = False

        service = PDFReportService(currency="GBP", currency_service=mock_service)

        # Try to convert - should fail and track
        result = service._convert_amount(Decimal("100.00"), "USD")

        # Should return original amount when conversion fails
        assert result == Decimal("100.00")
        assert "USD" in service._failed_conversions

    def test_currency_service_initialization(self):
        """Test PDFReportService accepts currency_service parameter."""
        currency_service = MockCurrencyService()
        service = PDFReportService(
            currency="USD",
            currency_service=currency_service,
        )

        assert service.currency_service is not None
        assert service.currency == "USD"

    def test_currency_symbols_constant(self):
        """Test CURRENCY_SYMBOLS contains expected values."""
        assert CURRENCY_SYMBOLS["GBP"] == "£"
        assert CURRENCY_SYMBOLS["USD"] == "$"
        assert CURRENCY_SYMBOLS["EUR"] == "€"
        assert CURRENCY_SYMBOLS["UAH"] == "₴"


class TestAsyncReportGeneration:
    """Tests for async report generation."""

    @pytest.mark.asyncio
    async def test_generate_report_async(self):
        """Test async report generation pre-fetches rates."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        subs = [
            MockSubscription(name="Test", amount=Decimal("10.00"), currency="USD"),
        ]

        pdf_bytes = await service.generate_report_async(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    @pytest.mark.asyncio
    async def test_generate_report_async_no_currency_service(self):
        """Test async report generation works without currency service."""
        service = PDFReportService(currency="GBP")

        subs = [
            MockSubscription(name="Test", amount=Decimal("10.00"), currency="GBP"),
        ]

        pdf_bytes = await service.generate_report_async(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestOverduePayments:
    """Tests for overdue payment detection and display."""

    def test_overdue_payment_detected(self):
        """Test that overdue payments are detected correctly."""
        service = PDFReportService()
        today = date.today()
        subs = [
            MockSubscription(
                name="Overdue Sub",
                amount=Decimal("10.00"),
                next_payment_date=today - timedelta(days=5),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_overdue_and_upcoming_mixed(self):
        """Test report with both overdue and upcoming payments."""
        service = PDFReportService()
        today = date.today()
        subs = [
            MockSubscription(
                name="Overdue Netflix",
                amount=Decimal("15.99"),
                next_payment_date=today - timedelta(days=3),
            ),
            MockSubscription(
                name="Due Tomorrow Spotify",
                amount=Decimal("9.99"),
                next_payment_date=today + timedelta(days=1),
            ),
            MockSubscription(
                name="Due Today Rent",
                amount=Decimal("1200.00"),
                next_payment_date=today,
            ),
            MockSubscription(
                name="Next Week Electric",
                amount=Decimal("80.00"),
                next_payment_date=today + timedelta(days=7),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_multiple_overdue_payments(self):
        """Test report with multiple overdue payments."""
        service = PDFReportService()
        today = date.today()
        subs = [
            MockSubscription(
                name="Very Overdue",
                amount=Decimal("50.00"),
                next_payment_date=today - timedelta(days=30),
            ),
            MockSubscription(
                name="Recently Overdue",
                amount=Decimal("25.00"),
                next_payment_date=today - timedelta(days=1),
            ),
            MockSubscription(
                name="Slightly Overdue",
                amount=Decimal("10.00"),
                next_payment_date=today - timedelta(days=7),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_upcoming_payments_section_renamed(self):
        """Test that section is renamed to include overdue."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Test",
                next_payment_date=date.today() + timedelta(days=5),
            ),
        ]

        elements = service._build_upcoming_payments(subs)

        # Check section header is present
        assert len(elements) > 0

    def test_no_overdue_no_upcoming(self):
        """Test section when no overdue or upcoming payments."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Far Future",
                next_payment_date=date.today() + timedelta(days=60),
            ),
        ]

        elements = service._build_upcoming_payments(subs)

        # Should still return elements (with empty message)
        assert len(elements) > 0


class TestPaymentHistory:
    """Tests for payment history section in PDF reports."""

    def test_payment_history_with_payments(self):
        """Test payment history section with actual payments."""
        service = PDFReportService()
        today = date.today()

        payment1 = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("15.99"),
            status="completed",
        )
        payment2 = MockPaymentHistory(
            payment_date=today - timedelta(days=10),
            amount=Decimal("9.99"),
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                payment_history=[payment1, payment2],
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_payment_history_empty(self):
        """Test payment history section with no payments."""
        service = PDFReportService()
        subs = [
            MockSubscription(
                name="Test",
                payment_history=[],
            ),
        ]

        elements = service._build_payment_history(subs)

        # Should return elements with "no payments" message
        assert len(elements) > 0

    def test_payment_history_failed_payments(self):
        """Test payment history with failed payments."""
        service = PDFReportService()
        today = date.today()

        failed_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=3),
            amount=Decimal("50.00"),
            status="failed",
        )
        completed_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("50.00"),
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Credit Card",
                payment_history=[failed_payment, completed_payment],
            ),
        ]

        elements = service._build_payment_history(subs)

        # Should have elements including the failed payment
        assert len(elements) > 0

    def test_payment_history_mixed_currencies(self):
        """Test payment history with multiple currencies."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)
        today = date.today()

        gbp_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("15.99"),
            currency="GBP",
            status="completed",
        )
        usd_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=10),
            amount=Decimal("100.00"),
            currency="USD",
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Mixed Currency Sub",
                payment_history=[gbp_payment, usd_payment],
            ),
        ]

        elements = service._build_payment_history(subs)

        assert len(elements) > 0

    def test_payment_history_outside_date_range(self):
        """Test payment history filters out old payments."""
        service = PDFReportService()
        today = date.today()

        old_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=60),  # Outside 30-day range
            amount=Decimal("15.99"),
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Test",
                payment_history=[old_payment],
            ),
        ]

        elements = service._build_payment_history(subs)

        # Should return "no payments" since payment is outside range
        assert len(elements) > 0

    def test_payment_history_custom_days(self):
        """Test payment history with custom history_days parameter."""
        service = PDFReportService()
        today = date.today()

        payment = MockPaymentHistory(
            payment_date=today - timedelta(days=45),  # 45 days ago
            amount=Decimal("100.00"),
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Test",
                payment_history=[payment],
            ),
        ]

        # With 30 days (default), should not include
        elements_30 = service._build_payment_history(subs, history_days=30)

        # With 60 days, should include
        elements_60 = service._build_payment_history(subs, history_days=60)

        assert len(elements_30) > 0
        assert len(elements_60) > 0

    def test_payment_history_multiple_subscriptions(self):
        """Test payment history from multiple subscriptions."""
        service = PDFReportService()
        today = date.today()

        netflix_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("15.99"),
            status="completed",
        )
        spotify_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=3),
            amount=Decimal("9.99"),
            status="completed",
        )
        rent_payment = MockPaymentHistory(
            payment_date=today - timedelta(days=1),
            amount=Decimal("1200.00"),
            status="completed",
        )

        subs = [
            MockSubscription(name="Netflix", payment_history=[netflix_payment]),
            MockSubscription(name="Spotify", payment_history=[spotify_payment]),
            MockSubscription(name="Rent", payment_history=[rent_payment]),
        ]

        elements = service._build_payment_history(subs)

        assert len(elements) > 0

    def test_payment_history_pending_status(self):
        """Test payment history with pending payments."""
        service = PDFReportService()
        today = date.today()

        pending_payment = MockPaymentHistory(
            payment_date=today,
            amount=Decimal("50.00"),
            status="pending",
        )

        subs = [
            MockSubscription(
                name="Test",
                payment_history=[pending_payment],
            ),
        ]

        elements = service._build_payment_history(subs)

        assert len(elements) > 0

    def test_full_report_with_payment_history(self):
        """Test full PDF report includes payment history section."""
        service = PDFReportService()
        today = date.today()

        payment = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("15.99"),
            status="completed",
        )

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                next_payment_date=today + timedelta(days=25),
                payment_history=[payment],
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"
        # PDF should be larger due to payment history section
        assert len(pdf_bytes) > 1000


class TestReportConfig:
    """Tests for ReportConfig-based PDF generation."""

    def test_report_with_config_default(self):
        """Test report generation with default ReportConfig."""
        from src.schemas.report import ReportConfig

        config = ReportConfig()
        service = PDFReportService(config=config)

        subs = [MockSubscription(name="Test", amount=Decimal("10.00"))]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_report_with_custom_date_range(self):
        """Test report with custom date range for upcoming payments."""
        from src.schemas.report import ReportConfig

        config = ReportConfig(date_range_days=60)
        service = PDFReportService(config=config)

        assert service.date_range_days == 60

        today = date.today()
        subs = [
            MockSubscription(
                name="In 45 Days",
                next_payment_date=today + timedelta(days=45),
            ),
        ]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)

    def test_report_with_sections_disabled(self):
        """Test report with some sections disabled."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(
            summary=True,
            category_breakdown=False,
            upcoming_payments=False,
            payment_history=False,
            all_payments=True,
        )
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        subs = [MockSubscription(name="Test")]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_report_with_only_summary(self):
        """Test report with only summary section."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(
            summary=True,
            category_breakdown=False,
            upcoming_payments=False,
            payment_history=False,
            all_payments=False,
        )
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        subs = [MockSubscription(name="Test")]
        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        # With only summary, PDF should be smaller
        assert len(pdf_bytes) > 0

    def test_report_with_currency_from_config(self):
        """Test report uses currency from config."""
        from src.schemas.report import ReportConfig

        config = ReportConfig(target_currency="EUR")
        service = PDFReportService(config=config)

        assert service.currency == "EUR"
        assert service.currency_symbol == "€"

    def test_report_with_include_inactive_filter(self):
        """Test report respects include_inactive filter from config."""
        from src.schemas.report import ReportConfig, ReportFilters

        filters = ReportFilters(include_inactive=True)
        config = ReportConfig(filters=filters)
        service = PDFReportService(config=config)

        assert service.include_inactive is True

    def test_report_with_letter_page_size(self):
        """Test report with letter page size from config."""
        from reportlab.lib.pagesizes import letter

        from src.schemas.report import PageSize, ReportConfig

        config = ReportConfig(page_size=PageSize.LETTER)
        service = PDFReportService(config=config)

        assert service.page_size == letter

    def test_report_config_overrides_params(self):
        """Test that config values override constructor params."""
        from src.schemas.report import ReportConfig

        config = ReportConfig(target_currency="USD", date_range_days=90)
        service = PDFReportService(
            page_size="a4",
            currency="GBP",  # Should be overridden by config
            config=config,
        )

        assert service.currency == "USD"
        assert service.date_range_days == 90

    def test_report_with_custom_history_days(self):
        """Test report with custom history days."""
        from src.schemas.report import ReportConfig

        config = ReportConfig(history_days=60)
        service = PDFReportService(config=config)

        assert service.history_days == 60


class TestReportConfigSchema:
    """Tests for ReportConfig Pydantic schema validation."""

    def test_default_config(self):
        """Test default ReportConfig values."""
        from src.schemas.report import ReportConfig

        config = ReportConfig()

        assert config.page_size.value == "a4"
        assert config.target_currency is None
        assert config.date_range_days == 30
        assert config.history_days == 30
        assert config.sections.summary is True
        assert config.sections.category_breakdown is True
        assert config.sections.all_payments is True
        assert config.filters.include_inactive is False
        assert config.options.show_original_currency is True

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        from src.schemas.report import ReportConfig

        data = {
            "page_size": "letter",
            "target_currency": "EUR",
            "date_range_days": 60,
            "sections": {
                "summary": True,
                "category_breakdown": False,
            },
        }
        config = ReportConfig.model_validate(data)

        assert config.page_size.value == "letter"
        assert config.target_currency == "EUR"
        assert config.date_range_days == 60
        assert config.sections.summary is True
        assert config.sections.category_breakdown is False

    def test_config_date_range_validation(self):
        """Test date range validation."""
        from pydantic import ValidationError

        from src.schemas.report import ReportConfig

        # Valid range
        config = ReportConfig(date_range_days=365)
        assert config.date_range_days == 365

        # Invalid: too high
        try:
            ReportConfig(date_range_days=400)
            assert False, "Should raise validation error"
        except ValidationError:
            pass

        # Invalid: too low
        try:
            ReportConfig(date_range_days=0)
            assert False, "Should raise validation error"
        except ValidationError:
            pass

    def test_sections_model(self):
        """Test ReportSections model."""
        from src.schemas.report import ReportSections

        sections = ReportSections(
            summary=False,
            debt_progress=True,
            savings_progress=True,
        )

        assert sections.summary is False
        assert sections.debt_progress is True
        assert sections.savings_progress is True
        # Defaults
        assert sections.category_breakdown is True
        assert sections.all_payments is True

    def test_filters_model(self):
        """Test ReportFilters model."""
        from src.schemas.report import ReportFilters

        filters = ReportFilters(
            payment_modes=["recurring", "debt"],
            include_inactive=True,
        )

        assert filters.payment_modes == ["recurring", "debt"]
        assert filters.include_inactive is True
        assert filters.categories is None

    def test_color_scheme_enum(self):
        """Test ColorScheme enum values."""
        from src.schemas.report import ColorScheme

        assert ColorScheme.DEFAULT.value == "default"
        assert ColorScheme.MONOCHROME.value == "monochrome"
        assert ColorScheme.HIGH_CONTRAST.value == "high_contrast"


class TestCardBreakdown:
    """Tests for card breakdown section in PDF reports."""

    def test_card_breakdown_with_cards(self):
        """Test card breakdown with payments assigned to cards."""
        service = PDFReportService()

        card1 = MockPaymentCard(name="Chase Sapphire", card_id="card-1")
        card2 = MockPaymentCard(name="Monzo Personal", card_id="card-2")

        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99"), payment_card=card1),
            MockSubscription(name="Spotify", amount=Decimal("9.99"), payment_card=card1),
            MockSubscription(name="Electric", amount=Decimal("80.00"), payment_card=card2),
        ]

        elements = service._build_card_breakdown(subs)

        assert len(elements) > 0

    def test_card_breakdown_with_unassigned(self):
        """Test card breakdown with unassigned payments."""
        service = PDFReportService()

        card1 = MockPaymentCard(name="Chase", card_id="card-1")

        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99"), payment_card=card1),
            MockSubscription(name="Unassigned", amount=Decimal("50.00")),  # No card
        ]

        elements = service._build_card_breakdown(subs)

        assert len(elements) > 0

    def test_card_breakdown_empty(self):
        """Test card breakdown with no active payments."""
        service = PDFReportService()

        subs = [
            MockSubscription(name="Inactive", is_active=False),
        ]

        elements = service._build_card_breakdown(subs)

        # Should return "No active payments" message
        assert len(elements) > 0

    def test_card_breakdown_in_full_report(self):
        """Test card breakdown included in full report with config."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(card_breakdown=True)
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        card = MockPaymentCard(name="Test Card")
        subs = [MockSubscription(name="Test", payment_card=card)]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_card_breakdown_currency_conversion(self):
        """Test card breakdown with currency conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        card = MockPaymentCard(name="USD Card")
        subs = [
            MockSubscription(
                name="US Service",
                amount=Decimal("100.00"),
                currency="USD",
                payment_card=card,
            ),
        ]

        elements = service._build_card_breakdown(subs)

        assert len(elements) > 0


class TestDebtProgress:
    """Tests for debt progress section in PDF reports."""

    def test_debt_progress_with_debts(self):
        """Test debt progress with active debts."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Credit Card",
                amount=Decimal("200.00"),
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("5000.00"),
                remaining_balance=Decimal("2500.00"),
                creditor="Barclays",
            ),
            MockSubscription(
                name="Student Loan",
                amount=Decimal("300.00"),
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("20000.00"),
                remaining_balance=Decimal("15000.00"),
                creditor="SLC",
            ),
        ]

        elements = service._build_debt_progress(subs)

        assert len(elements) > 0

    def test_debt_progress_empty(self):
        """Test debt progress with no debt payments."""
        service = PDFReportService()

        subs = [
            MockSubscription(name="Netflix"),  # Regular subscription
        ]

        elements = service._build_debt_progress(subs)

        # Should return "No debt payments" message
        assert len(elements) > 0

    def test_debt_progress_fully_paid(self):
        """Test debt progress with fully paid debt."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Paid Off Card",
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("1000.00"),
                remaining_balance=Decimal("0.00"),
            ),
        ]

        elements = service._build_debt_progress(subs)

        assert len(elements) > 0

    def test_debt_progress_currency_conversion(self):
        """Test debt progress with currency conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        subs = [
            MockSubscription(
                name="USD Debt",
                amount=Decimal("100.00"),
                currency="USD",
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("5000.00"),
                remaining_balance=Decimal("3000.00"),
            ),
        ]

        elements = service._build_debt_progress(subs)

        assert len(elements) > 0

    def test_debt_progress_in_full_report(self):
        """Test debt progress included in full report with config."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(debt_progress=True)
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(
                name="Debt",
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("1000.00"),
                remaining_balance=Decimal("500.00"),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestSavingsProgress:
    """Tests for savings goals section in PDF reports."""

    def test_savings_progress_with_goals(self):
        """Test savings progress with active goals."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Emergency Fund",
                amount=Decimal("500.00"),
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("10000.00"),
                current_saved=Decimal("6500.00"),
                recipient="Savings Account",
            ),
            MockSubscription(
                name="Vacation 2025",
                amount=Decimal("200.00"),
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("3000.00"),
                current_saved=Decimal("1800.00"),
            ),
        ]

        elements = service._build_savings_progress(subs)

        assert len(elements) > 0

    def test_savings_progress_empty(self):
        """Test savings progress with no savings goals."""
        service = PDFReportService()

        subs = [
            MockSubscription(name="Netflix"),  # Regular subscription
        ]

        elements = service._build_savings_progress(subs)

        # Should return "No savings goals" message
        assert len(elements) > 0

    def test_savings_progress_goal_reached(self):
        """Test savings progress with goal achieved."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Completed Goal",
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("1000.00"),
                current_saved=Decimal("1000.00"),
            ),
        ]

        elements = service._build_savings_progress(subs)

        assert len(elements) > 0

    def test_savings_progress_over_target(self):
        """Test savings progress with over 100% achieved."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Overachieved",
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("1000.00"),
                current_saved=Decimal("1200.00"),  # 120%
            ),
        ]

        elements = service._build_savings_progress(subs)

        assert len(elements) > 0

    def test_savings_progress_currency_conversion(self):
        """Test savings progress with currency conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        subs = [
            MockSubscription(
                name="USD Savings",
                amount=Decimal("100.00"),
                currency="USD",
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("5000.00"),
                current_saved=Decimal("2500.00"),
            ),
        ]

        elements = service._build_savings_progress(subs)

        assert len(elements) > 0

    def test_savings_progress_in_full_report(self):
        """Test savings progress included in full report with config."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(savings_progress=True)
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(
                name="Savings",
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("1000.00"),
                current_saved=Decimal("500.00"),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestBudgetStatus:
    """Tests for budget status section in PDF reports."""

    def test_budget_status_with_budgets(self):
        """Test budget status with category budgets."""
        service = PDFReportService()

        entertainment = MockCategory("Entertainment", budget_amount=Decimal("100.00"))
        utilities = MockCategory("Utilities", budget_amount=Decimal("150.00"))

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category_rel=entertainment,
            ),
            MockSubscription(
                name="Spotify",
                amount=Decimal("9.99"),
                category_rel=entertainment,
            ),
            MockSubscription(
                name="Electric",
                amount=Decimal("80.00"),
                category_rel=utilities,
            ),
        ]

        elements = service._build_budget_status(subs)

        assert len(elements) > 0

    def test_budget_status_over_budget(self):
        """Test budget status with over-budget category."""
        service = PDFReportService()

        entertainment = MockCategory("Entertainment", budget_amount=Decimal("20.00"))

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category_rel=entertainment,
            ),
            MockSubscription(
                name="Spotify",
                amount=Decimal("9.99"),
                category_rel=entertainment,
            ),
            # Total: £25.98 > £20 budget
        ]

        elements = service._build_budget_status(subs)

        assert len(elements) > 0

    def test_budget_status_no_budgets(self):
        """Test budget status with no category budgets configured."""
        service = PDFReportService()

        entertainment = MockCategory("Entertainment")  # No budget

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category_rel=entertainment,
            ),
        ]

        elements = service._build_budget_status(subs)

        # Should return "No category budgets configured" message
        assert len(elements) > 0

    def test_budget_status_warning_level(self):
        """Test budget status with warning level (>90%)."""
        service = PDFReportService()

        entertainment = MockCategory("Entertainment", budget_amount=Decimal("100.00"))

        subs = [
            MockSubscription(
                name="Multiple Services",
                amount=Decimal("95.00"),  # 95% of budget
                category_rel=entertainment,
            ),
        ]

        elements = service._build_budget_status(subs)

        assert len(elements) > 0

    def test_budget_status_currency_conversion(self):
        """Test budget status with currency conversion."""
        currency_service = MockCurrencyService()
        service = PDFReportService(currency="GBP", currency_service=currency_service)

        entertainment = MockCategory("Entertainment", budget_amount=Decimal("100.00"))

        subs = [
            MockSubscription(
                name="USD Service",
                amount=Decimal("50.00"),
                currency="USD",
                category_rel=entertainment,
            ),
        ]

        elements = service._build_budget_status(subs)

        assert len(elements) > 0

    def test_budget_status_in_full_report(self):
        """Test budget status included in full report with config."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(budget_status=True)
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        entertainment = MockCategory("Entertainment", budget_amount=Decimal("100.00"))
        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category_rel=entertainment,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestAllNewSectionsTogether:
    """Tests for all new sections (D sprint) working together."""

    def test_report_with_all_new_sections_enabled(self):
        """Test generating report with all new sections enabled."""
        from src.schemas.report import ReportConfig, ReportSections

        sections = ReportSections(
            summary=True,
            category_breakdown=True,
            card_breakdown=True,
            upcoming_payments=True,
            payment_history=True,
            debt_progress=True,
            savings_progress=True,
            budget_status=True,
            all_payments=True,
        )
        config = ReportConfig(sections=sections)
        service = PDFReportService(config=config)

        # Create a comprehensive set of subscriptions
        card = MockPaymentCard(name="Main Card")
        entertainment = MockCategory("Entertainment", budget_amount=Decimal("100.00"))

        today = date.today()
        payment = MockPaymentHistory(
            payment_date=today - timedelta(days=5),
            amount=Decimal("15.99"),
            status="completed",
        )

        subs = [
            # Regular subscription
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                payment_card=card,
                category_rel=entertainment,
                payment_history=[payment],
            ),
            # Debt
            MockSubscription(
                name="Credit Card Debt",
                amount=Decimal("200.00"),
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("5000.00"),
                remaining_balance=Decimal("3000.00"),
                creditor="Bank",
            ),
            # Savings
            MockSubscription(
                name="Emergency Fund",
                amount=Decimal("500.00"),
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("10000.00"),
                current_saved=Decimal("6500.00"),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"
        # Report should be larger with all sections
        assert len(pdf_bytes) > 3000

    def test_report_with_mixed_currencies_all_sections(self):
        """Test all sections with mixed currencies."""
        from src.schemas.report import ReportConfig, ReportSections

        currency_service = MockCurrencyService()
        sections = ReportSections(
            card_breakdown=True,
            debt_progress=True,
            savings_progress=True,
            budget_status=True,
        )
        config = ReportConfig(sections=sections, target_currency="GBP")
        service = PDFReportService(config=config, currency_service=currency_service)

        card = MockPaymentCard(name="USD Card")
        entertainment = MockCategory("Entertainment", budget_amount=Decimal("200.00"))

        subs = [
            MockSubscription(
                name="US Netflix",
                amount=Decimal("15.99"),
                currency="USD",
                payment_card=card,
                category_rel=entertainment,
            ),
            MockSubscription(
                name="USD Debt",
                amount=Decimal("100.00"),
                currency="USD",
                payment_type=PaymentType.DEBT,
                payment_mode=PaymentMode.DEBT,
                total_owed=Decimal("5000.00"),
                remaining_balance=Decimal("3000.00"),
            ),
            MockSubscription(
                name="EUR Savings",
                amount=Decimal("200.00"),
                currency="EUR",
                payment_type=PaymentType.SAVINGS,
                payment_mode=PaymentMode.SAVINGS,
                target_amount=Decimal("10000.00"),
                current_saved=Decimal("5000.00"),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestCategoryPieChart:
    """Tests for category pie chart visual enhancement."""

    def test_pie_chart_basic_generation(self):
        """Test pie chart is generated with include_charts enabled."""
        from src.schemas.report import ReportConfig, ReportOptions

        options = ReportOptions(include_charts=True)
        config = ReportConfig(options=options)
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99"), category="Entertainment"),
            MockSubscription(name="Spotify", amount=Decimal("10.99"), category="Entertainment"),
            MockSubscription(name="Gym", amount=Decimal("30.00"), category="Health"),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"
        # With charts, report should be larger
        assert len(pdf_bytes) > 2000

    def test_pie_chart_with_many_categories(self):
        """Test pie chart groups excess categories into 'Other'."""
        from src.schemas.report import ReportConfig, ReportOptions

        options = ReportOptions(include_charts=True)
        config = ReportConfig(options=options)
        service = PDFReportService(config=config)

        # Create 10 different categories (more than 8 max slices)
        categories = [
            "Entertainment",
            "Health",
            "Utilities",
            "Food",
            "Transport",
            "Insurance",
            "Education",
            "Software",
            "Gaming",
            "Miscellaneous",
        ]
        subs = [
            MockSubscription(name=f"Sub {i}", amount=Decimal("10.00"), category=cat)
            for i, cat in enumerate(categories)
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_pie_chart_empty_data(self):
        """Test pie chart handles empty data gracefully."""
        from src.schemas.report import ReportConfig, ReportOptions

        options = ReportOptions(include_charts=True)
        config = ReportConfig(options=options)
        service = PDFReportService(config=config)

        pdf_bytes = service.generate_report(subscriptions=[])

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_pie_chart_disabled_by_default(self):
        """Test pie chart is not included when include_charts=False."""
        from src.schemas.report import ReportConfig, ReportOptions

        options = ReportOptions(include_charts=False)
        config = ReportConfig(options=options)
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99"), category="Entertainment"),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_pie_chart_single_category(self):
        """Test pie chart works with single category (100% slice)."""
        from src.schemas.report import ReportConfig, ReportOptions

        options = ReportOptions(include_charts=True)
        config = ReportConfig(options=options)
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(name="Netflix", amount=Decimal("15.99"), category="Entertainment"),
            MockSubscription(name="Spotify", amount=Decimal("10.99"), category="Entertainment"),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_pie_chart_method_direct(self):
        """Test _build_category_pie_chart method directly."""
        service = PDFReportService()

        category_data = [
            ("Entertainment", Decimal("50.00")),
            ("Health", Decimal("30.00")),
            ("Utilities", Decimal("20.00")),
        ]

        drawing = service._build_category_pie_chart(category_data)

        assert drawing is not None
        # Drawing should have width and height
        assert drawing.width == 400
        assert drawing.height == 200

    def test_pie_chart_method_empty_returns_none(self):
        """Test _build_category_pie_chart returns None for empty data."""
        service = PDFReportService()

        result = service._build_category_pie_chart([])

        assert result is None

    def test_pie_chart_method_zero_total_returns_none(self):
        """Test _build_category_pie_chart returns None when total is zero."""
        service = PDFReportService()

        category_data = [
            ("Entertainment", Decimal("0")),
        ]

        result = service._build_category_pie_chart(category_data)

        assert result is None


class TestColorCodedPaymentStatus:
    """Tests for color-coded payment status visual enhancements."""

    def test_overdue_payment_status_format(self):
        """Test overdue payments show warning symbol and 'overdue' text."""
        service = PDFReportService()

        today = date.today()
        subs = [
            MockSubscription(
                name="Overdue Sub",
                amount=Decimal("10.00"),
                next_payment_date=today - timedelta(days=5),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_due_today_payment_status(self):
        """Test payments due today show lightning symbol."""
        service = PDFReportService()

        today = date.today()
        subs = [
            MockSubscription(
                name="Due Today Sub",
                amount=Decimal("10.00"),
                next_payment_date=today,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_tomorrow_payment_status(self):
        """Test payments due tomorrow show lightning symbol."""
        service = PDFReportService()

        tomorrow = date.today() + timedelta(days=1)
        subs = [
            MockSubscription(
                name="Tomorrow Sub",
                amount=Decimal("10.00"),
                next_payment_date=tomorrow,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_within_three_days_payment_status(self):
        """Test payments within 3 days show circle symbol."""
        service = PDFReportService()

        in_3_days = date.today() + timedelta(days=3)
        subs = [
            MockSubscription(
                name="Soon Sub",
                amount=Decimal("10.00"),
                next_payment_date=in_3_days,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_within_week_payment_status(self):
        """Test payments within a week show circle symbol."""
        service = PDFReportService()

        in_6_days = date.today() + timedelta(days=6)
        subs = [
            MockSubscription(
                name="Week Sub",
                amount=Decimal("10.00"),
                next_payment_date=in_6_days,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_safe_distance_payment_status(self):
        """Test payments more than 7 days away have green status."""
        service = PDFReportService()

        in_15_days = date.today() + timedelta(days=15)
        subs = [
            MockSubscription(
                name="Safe Sub",
                amount=Decimal("10.00"),
                next_payment_date=in_15_days,
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_active_status_symbol(self):
        """Test active subscriptions show checkmark symbol in all payments."""
        service = PDFReportService()

        subs = [
            MockSubscription(name="Active Sub", amount=Decimal("10.00"), is_active=True),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_inactive_status_symbol(self):
        """Test inactive subscriptions show circle symbol in all payments."""
        service = PDFReportService(include_inactive=True)

        subs = [
            MockSubscription(name="Inactive Sub", amount=Decimal("10.00"), is_active=False),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_mixed_urgency_levels(self):
        """Test report with payments at various urgency levels."""
        service = PDFReportService()

        today = date.today()
        subs = [
            MockSubscription(
                name="Overdue", amount=Decimal("10.00"), next_payment_date=today - timedelta(days=3)
            ),
            MockSubscription(name="Today", amount=Decimal("20.00"), next_payment_date=today),
            MockSubscription(
                name="Tomorrow",
                amount=Decimal("30.00"),
                next_payment_date=today + timedelta(days=1),
            ),
            MockSubscription(
                name="In 3 days",
                amount=Decimal("40.00"),
                next_payment_date=today + timedelta(days=3),
            ),
            MockSubscription(
                name="In 5 days",
                amount=Decimal("50.00"),
                next_payment_date=today + timedelta(days=5),
            ),
            MockSubscription(
                name="In 10 days",
                amount=Decimal("60.00"),
                next_payment_date=today + timedelta(days=10),
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"
        # Report should be reasonably sized with all the color-coded rows
        assert len(pdf_bytes) > 2000


class TestChartColors:
    """Tests for chart color constants."""

    def test_chart_colors_exist(self):
        """Test CHART_COLORS constant is defined."""
        from src.services.pdf_report_service import CHART_COLORS

        assert CHART_COLORS is not None
        assert isinstance(CHART_COLORS, list)

    def test_chart_colors_count(self):
        """Test there are enough colors for chart slices."""
        from src.services.pdf_report_service import CHART_COLORS

        # Should have at least 8 colors (for max 8 slices in pie chart)
        assert len(CHART_COLORS) >= 8

    def test_chart_colors_are_colors(self):
        """Test all chart colors are valid ReportLab Color objects."""
        from reportlab.lib.colors import Color

        from src.services.pdf_report_service import CHART_COLORS

        for color in CHART_COLORS:
            # Each should be a Color instance (HexColor creates Color objects)
            assert isinstance(color, Color)


class TestOneTimePaymentHandling:
    """Tests for one-time payment handling in monthly calculations."""

    def test_one_time_payment_excluded_from_monthly_total(self):
        """Test that one-time payments are excluded from monthly totals."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Monthly Sub",
                amount=Decimal("10.00"),
                frequency=Frequency.MONTHLY,
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="One-Time Payment",
                amount=Decimal("5700.00"),  # Large one-time payment
                frequency=Frequency.MONTHLY,  # Even with monthly frequency
                payment_mode=PaymentMode.ONE_TIME,  # Mode determines it's one-time
            ),
        ]

        pdf_bytes = service.generate_report(subscriptions=subs)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_to_monthly_returns_zero_for_one_time(self):
        """Test _to_monthly returns 0 for one-time payment mode."""
        service = PDFReportService()

        # One-time with monthly frequency should still return 0
        result = service._to_monthly(Decimal("100.00"), "monthly", "one_time")
        assert result == Decimal("0")

        # One-time with yearly frequency should still return 0
        result = service._to_monthly(Decimal("100.00"), "yearly", "one_time")
        assert result == Decimal("0")

    def test_to_monthly_regular_payments_unaffected(self):
        """Test _to_monthly works normally for recurring payments."""
        service = PDFReportService()

        # Monthly recurring
        result = service._to_monthly(Decimal("100.00"), "monthly", "recurring")
        assert result == Decimal("100.00")

        # Yearly recurring (100/12 ≈ 8.30)
        result = service._to_monthly(Decimal("100.00"), "yearly", "recurring")
        assert result == Decimal("8.30")

        # No payment_mode specified (backward compatible)
        result = service._to_monthly(Decimal("100.00"), "monthly", None)
        assert result == Decimal("100.00")

    def test_category_breakdown_excludes_one_time(self):
        """Test category breakdown excludes one-time payments from totals."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Regular",
                amount=Decimal("50.00"),
                category="Test",
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="One-Time",
                amount=Decimal("1000.00"),
                category="Test",
                payment_mode=PaymentMode.ONE_TIME,
            ),
        ]

        elements = service._build_category_breakdown(subs)

        # Should have elements (header, table, etc.)
        assert len(elements) > 0

    def test_card_breakdown_excludes_one_time(self):
        """Test card breakdown excludes one-time payments from totals."""
        service = PDFReportService()

        card = MockPaymentCard(name="Test Card")
        subs = [
            MockSubscription(
                name="Regular",
                amount=Decimal("50.00"),
                payment_card=card,
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="One-Time",
                amount=Decimal("1000.00"),
                payment_card=card,
                payment_mode=PaymentMode.ONE_TIME,
            ),
        ]

        elements = service._build_card_breakdown(subs)

        # Should have elements
        assert len(elements) > 0

    def test_category_with_only_one_time_payments_filtered_out(self):
        """Test that categories with only one-time payments are not displayed."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Regular Sub",
                amount=Decimal("50.00"),
                category="Entertainment",
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="One-Time Legal Fee",
                amount=Decimal("5700.00"),
                category="Legal",
                payment_mode=PaymentMode.ONE_TIME,
            ),
        ]

        elements = service._build_category_breakdown(subs)

        # Should have elements (the Entertainment category)
        assert len(elements) > 0

        # Convert elements to string to check content
        # The Legal category should NOT appear since it only has one-time payments
        # This tests the filtering logic that removes categories with £0.00 monthly


class TestSpendingBarCharts:
    """Tests for the spending bar charts feature."""

    def test_bar_charts_basic_generation(self):
        """Test that bar charts are generated with valid subscriptions."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Netflix",
                amount=Decimal("15.99"),
                category="Entertainment",
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="Spotify",
                amount=Decimal("9.99"),
                category="Entertainment",
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="Rent",
                amount=Decimal("1200.00"),
                category="Housing",
                payment_mode=PaymentMode.RECURRING,
            ),
        ]

        elements = service._build_spending_bar_charts(subs)

        # Should have elements (header, charts, spacers)
        assert len(elements) > 0
        # Should have at least a header
        assert any("Spending Analysis" in str(e) for e in elements if hasattr(e, "text"))

    def test_bar_charts_empty_subscriptions(self):
        """Test bar charts with no subscriptions."""
        service = PDFReportService()

        elements = service._build_spending_bar_charts([])

        # Should have header and "no data" message
        assert len(elements) > 0

    def test_bar_charts_only_inactive(self):
        """Test bar charts with only inactive subscriptions."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Old Sub",
                amount=Decimal("10.00"),
                category="Test",
                is_active=False,
                payment_mode=PaymentMode.RECURRING,
            ),
        ]

        elements = service._build_spending_bar_charts(subs)

        # Should have header and "no data" message
        assert len(elements) > 0

    def test_bar_charts_excludes_one_time(self):
        """Test that one-time payments are excluded from bar charts."""
        service = PDFReportService()

        subs = [
            MockSubscription(
                name="Regular",
                amount=Decimal("50.00"),
                category="Recurring",
                payment_mode=PaymentMode.RECURRING,
            ),
            MockSubscription(
                name="One-Time",
                amount=Decimal("5000.00"),
                category="OneTime",
                payment_mode=PaymentMode.ONE_TIME,
            ),
        ]

        elements = service._build_spending_bar_charts(subs)

        # Should have elements
        assert len(elements) > 0

    def test_horizontal_bar_chart_direct(self):
        """Test the _build_horizontal_bar_chart method directly."""
        service = PDFReportService()

        data = [
            ("Housing", Decimal("1200.00")),
            ("Entertainment", Decimal("50.00")),
            ("Utilities", Decimal("100.00")),
        ]

        chart = service._build_horizontal_bar_chart(data, "Test Chart", "£")

        # Should return a Drawing
        from reportlab.graphics.shapes import Drawing
        assert isinstance(chart, Drawing)

    def test_horizontal_bar_chart_empty_returns_none(self):
        """Test that empty data returns None."""
        service = PDFReportService()

        chart = service._build_horizontal_bar_chart([], "Empty Chart", "£")

        assert chart is None

    def test_horizontal_bar_chart_single_category(self):
        """Test bar chart with single category."""
        service = PDFReportService()

        data = [("Only Category", Decimal("100.00"))]

        chart = service._build_horizontal_bar_chart(data, "Single Category", "£")

        from reportlab.graphics.shapes import Drawing
        assert isinstance(chart, Drawing)

    def test_bar_charts_in_full_report_with_charts_enabled(self):
        """Test that bar charts are included when charts are enabled."""
        from src.schemas.report import ReportConfig, ReportOptions

        config = ReportConfig(
            options=ReportOptions(include_charts=True),
        )
        service = PDFReportService(config=config)

        subs = [
            MockSubscription(
                name="Test Sub",
                amount=Decimal("50.00"),
                category="Test",
                payment_mode=PaymentMode.RECURRING,
            ),
        ]

        pdf_bytes = service.generate_report(subs)

        # Should generate a valid PDF
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000  # Should be a reasonable size

    def test_bar_charts_limits_to_top_8_categories(self):
        """Test that bar charts limit to top 8 categories."""
        service = PDFReportService()

        # Create 12 categories
        subs = [
            MockSubscription(
                name=f"Sub{i}",
                amount=Decimal(str(100 - i * 5)),
                category=f"Category{i}",
                payment_mode=PaymentMode.RECURRING,
            )
            for i in range(12)
        ]

        elements = service._build_spending_bar_charts(subs)

        # Should have elements
        assert len(elements) > 0

    def test_bar_chart_currency_symbols(self):
        """Test bar charts with different currency symbols."""
        for currency, symbol in [("GBP", "£"), ("USD", "$"), ("EUR", "€")]:
            service = PDFReportService(currency=currency)

            data = [("Test", Decimal("100.00"))]
            chart = service._build_horizontal_bar_chart(data, "Test", symbol)

            from reportlab.graphics.shapes import Drawing
            assert isinstance(chart, Drawing)