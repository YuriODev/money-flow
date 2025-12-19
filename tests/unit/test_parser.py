"""Comprehensive tests for CommandParser.

Tests cover:
- AI parsing (mocked)
- Regex fallback parsing
- All supported intents
- Entity extraction
- Currency detection
- Error handling
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.agent.parser import CommandParser
from src.models.subscription import Frequency, PaymentMode, PaymentType


class TestCommandParserInit:
    """Tests for CommandParser initialization."""

    def test_init_without_api_key(self):
        """Test initialization without API key uses regex only."""
        parser = CommandParser()

        assert parser.use_ai is False
        assert parser.prompt_loader is not None

    def test_init_with_api_key(self):
        """Test initialization with API key enables AI."""
        parser = CommandParser(api_key="test-key")

        assert parser.use_ai is True
        assert parser.model == "claude-haiku-4.5-20250929"


class TestCommandParserRegex:
    """Tests for regex-based parsing."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()  # No API key = regex only

    def test_parse_create_add(self):
        """Test parsing 'add' command."""
        result = self.parser.parse("Add Netflix subscription for $15.99 monthly")

        assert result["intent"] == "CREATE"
        # Parser lowercases names
        assert result["entities"]["name"].lower() == "netflix"
        assert result["entities"]["amount"] == Decimal("15.99")
        assert result["entities"]["frequency"] == Frequency.MONTHLY

    def test_parse_create_subscribe(self):
        """Test parsing 'subscribe' command."""
        result = self.parser.parse("subscribe to Spotify $9.99 monthly")

        assert result["intent"] == "CREATE"
        # Parser lowercases names
        assert result["entities"]["name"].lower() == "spotify"

    def test_parse_create_new(self):
        """Test parsing 'new subscription' command."""
        result = self.parser.parse("new subscription Gym $50.00")

        assert result["intent"] == "CREATE"
        # Parser lowercases names
        assert result["entities"]["name"].lower() == "gym"
        assert result["entities"]["amount"] == Decimal("50.00")

    def test_parse_create_default_frequency(self):
        """Test default frequency is MONTHLY."""
        result = self.parser.parse("Add Netflix $15.99")

        assert result["entities"]["frequency"] == Frequency.MONTHLY

    def test_parse_create_weekly(self):
        """Test parsing weekly frequency."""
        result = self.parser.parse("Add Newspaper $5.00 weekly")

        assert result["entities"]["frequency"] == Frequency.WEEKLY

    def test_parse_create_yearly(self):
        """Test parsing yearly frequency."""
        result = self.parser.parse("Add Insurance $1200.00 yearly")

        assert result["entities"]["frequency"] == Frequency.YEARLY

    def test_parse_read_show(self):
        """Test parsing 'show' command."""
        result = self.parser.parse("Show all my subscriptions")

        assert result["intent"] == "READ"

    def test_parse_read_list(self):
        """Test parsing 'list' command."""
        result = self.parser.parse("List my subscriptions")

        assert result["intent"] == "READ"

    def test_parse_read_get(self):
        """Test parsing 'get' command."""
        result = self.parser.parse("Get active subscriptions")

        assert result["intent"] == "READ"
        assert result["entities"].get("is_active") is True

    def test_parse_read_what(self):
        """Test parsing 'what are' command."""
        result = self.parser.parse("What are my subscriptions?")

        assert result["intent"] == "READ"

    def test_parse_summary_spending(self):
        """Test parsing spending summary command."""
        result = self.parser.parse("How much am I spending?")

        assert result["intent"] == "SUMMARY"

    def test_parse_summary_show(self):
        """Test parsing 'show summary' command."""
        result = self.parser.parse("Show my spending summary")

        assert result["intent"] == "SUMMARY"

    def test_parse_summary_total(self):
        """Test parsing 'total' command."""
        result = self.parser.parse("Total spending")

        assert result["intent"] == "SUMMARY"

    def test_parse_upcoming_due(self):
        """Test parsing 'due' command."""
        result = self.parser.parse("What's due this week?")

        assert result["intent"] == "UPCOMING"

    def test_parse_upcoming_show(self):
        """Test parsing 'show upcoming' command."""
        result = self.parser.parse("Show upcoming payments")

        assert result["intent"] == "UPCOMING"

    def test_parse_upcoming_next(self):
        """Test parsing 'next' command."""
        result = self.parser.parse("Next payments")

        assert result["intent"] == "UPCOMING"

    def test_parse_delete_cancel(self):
        """Test parsing 'cancel' command."""
        result = self.parser.parse("Cancel my gym membership")

        assert result["intent"] == "DELETE"
        assert "gym" in result["entities"]["name"].lower()

    def test_parse_delete_remove(self):
        """Test parsing 'remove' command."""
        result = self.parser.parse("Remove Netflix subscription")

        assert result["intent"] == "DELETE"
        assert "netflix" in result["entities"]["name"].lower()

    def test_parse_update_change(self):
        """Test parsing 'update' command."""
        result = self.parser.parse("Update Netflix to $19.99")

        assert result["intent"] == "UPDATE"
        assert "netflix" in result["entities"]["name"].lower()
        assert result["entities"]["amount"] == Decimal("19.99")

    def test_parse_update_set(self):
        """Test parsing 'set' command."""
        result = self.parser.parse("Set Spotify amount to $12.99")

        assert result["intent"] == "UPDATE"
        assert result["entities"]["amount"] == Decimal("12.99")

    def test_parse_convert_currency(self):
        """Test parsing currency conversion command."""
        # The regex expects format: "convert 100 USD to GBP" or similar
        result = self.parser.parse("Convert 100 USD to GBP")

        assert result["intent"] == "CONVERT"
        assert result["entities"]["amount"] == Decimal("100")
        assert result["entities"]["to_currency"] == "GBP"

    def test_parse_convert_how_much(self):
        """Test parsing 'how much' conversion command."""
        result = self.parser.parse("How much is £50 in USD")

        assert result["intent"] == "CONVERT"
        assert result["entities"]["amount"] == Decimal("50")
        assert result["entities"]["to_currency"] == "USD"

    def test_parse_unknown(self):
        """Test parsing unknown command."""
        result = self.parser.parse("Hello world")

        assert result["intent"] == "UNKNOWN"
        assert result["confidence"] == 0.0

    def test_parse_confidence_regex(self):
        """Test regex parsing has correct confidence."""
        result = self.parser.parse("Show my subscriptions")

        assert result["confidence"] == 0.85


class TestCurrencyDetection:
    """Tests for currency symbol detection."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()

    def test_detect_gbp(self):
        """Test detecting GBP from £ symbol."""
        result = self.parser.parse("Add Netflix £15.99 monthly")

        assert result["entities"]["currency"] == "GBP"

    def test_detect_usd(self):
        """Test detecting USD from $ symbol."""
        result = self.parser.parse("Add Netflix $15.99 monthly")

        assert result["entities"]["currency"] == "USD"

    def test_detect_eur(self):
        """Test detecting EUR from € symbol."""
        result = self.parser.parse("Add Netflix €15.99 monthly")

        assert result["entities"]["currency"] == "EUR"

    def test_default_gbp(self):
        """Test default currency is GBP when no symbol."""
        result = self.parser.parse("Add Netflix 15.99 monthly")

        assert result["entities"]["currency"] == "GBP"


class TestCategoryExtraction:
    """Tests for category extraction."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()

    def test_extract_category(self):
        """Test extracting category from command."""
        result = self.parser.parse("Add Netflix $15.99 category entertainment")

        assert result["entities"].get("category") == "entertainment"


class TestNormalizeResult:
    """Tests for result normalization."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()

    def test_normalize_intent_uppercase(self):
        """Test intent is uppercased."""
        result = self.parser._normalize_result({"intent": "create", "entities": {}})

        assert result["intent"] == "CREATE"

    def test_normalize_frequency(self):
        """Test frequency string is converted to enum."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {"frequency": "monthly"},
            }
        )

        assert result["entities"]["frequency"] == Frequency.MONTHLY

    def test_normalize_frequency_biweekly_variants(self):
        """Test biweekly frequency variants."""
        for variant in ["biweekly", "bi-weekly", "fortnightly"]:
            result = self.parser._normalize_result(
                {
                    "intent": "create",
                    "entities": {"frequency": variant},
                }
            )
            assert result["entities"]["frequency"] == Frequency.BIWEEKLY

    def test_normalize_frequency_yearly_variants(self):
        """Test yearly frequency variants."""
        for variant in ["yearly", "annual", "annually"]:
            result = self.parser._normalize_result(
                {
                    "intent": "create",
                    "entities": {"frequency": variant},
                }
            )
            assert result["entities"]["frequency"] == Frequency.YEARLY

    def test_normalize_amount_to_decimal(self):
        """Test amount is converted to Decimal."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {"amount": 15.99},
            }
        )

        assert result["entities"]["amount"] == Decimal("15.99")

    def test_normalize_default_currency(self):
        """Test default currency is added."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {},
            }
        )

        assert result["entities"]["currency"] == "GBP"

    def test_normalize_default_confidence(self):
        """Test default confidence is added."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {},
            }
        )

        assert result["confidence"] == 0.9


class TestAIParsing:
    """Tests for AI-based parsing (mocked)."""

    def test_parse_with_ai_success(self):
        """Test successful AI parsing."""
        parser = CommandParser(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"intent": "CREATE", "entities": {"name": "Netflix"}}')
        ]

        with patch.object(parser.client.messages, "create", return_value=mock_response):
            result = parser.parse("Add Netflix")

            assert result["intent"] == "CREATE"
            assert result["entities"]["name"] == "Netflix"

    def test_parse_with_ai_fallback(self):
        """Test AI parsing falls back to regex on error."""
        parser = CommandParser(api_key="test-key")

        with patch.object(parser.client.messages, "create", side_effect=Exception("API Error")):
            result = parser.parse("Show my subscriptions")

            # Should still work via regex fallback
            assert result["intent"] == "READ"

    def test_parse_with_ai_no_json(self):
        """Test AI parsing falls back when no JSON found."""
        parser = CommandParser(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I don't understand")]

        with patch.object(parser.client.messages, "create", return_value=mock_response):
            result = parser.parse("Show my subscriptions")

            # Should fall back to regex
            assert result["intent"] == "READ"


class TestPaymentModeDetection:
    """Tests for PaymentMode inference and detection."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()

    def test_infer_payment_mode_recurring_from_subscription(self):
        """Test recurring mode inferred from subscription type."""
        result = self.parser._infer_payment_mode(PaymentType.SUBSCRIPTION)
        assert result == PaymentMode.RECURRING

    def test_infer_payment_mode_recurring_from_housing(self):
        """Test recurring mode inferred from housing type."""
        result = self.parser._infer_payment_mode(PaymentType.HOUSING)
        assert result == PaymentMode.RECURRING

    def test_infer_payment_mode_recurring_from_utility(self):
        """Test recurring mode inferred from utility type."""
        result = self.parser._infer_payment_mode(PaymentType.UTILITY)
        assert result == PaymentMode.RECURRING

    def test_infer_payment_mode_debt_from_debt_type(self):
        """Test debt mode inferred from debt type."""
        result = self.parser._infer_payment_mode(PaymentType.DEBT)
        assert result == PaymentMode.DEBT

    def test_infer_payment_mode_savings_from_savings_type(self):
        """Test savings mode inferred from savings type."""
        result = self.parser._infer_payment_mode(PaymentType.SAVINGS)
        assert result == PaymentMode.SAVINGS

    def test_infer_payment_mode_one_time(self):
        """Test one_time mode inferred from one_time type."""
        result = self.parser._infer_payment_mode(PaymentType.ONE_TIME)
        assert result == PaymentMode.ONE_TIME

    def test_infer_payment_mode_default_recurring(self):
        """Test default is recurring when type is None."""
        result = self.parser._infer_payment_mode(None)
        assert result == PaymentMode.RECURRING

    def test_parse_create_sets_payment_mode_for_debt(self):
        """Test CREATE command for debt sets payment_mode to DEBT."""
        result = self.parser.parse("Add debt to John £500, paying £50 monthly")
        assert result["intent"] == "CREATE"
        assert result["entities"]["payment_mode"] == PaymentMode.DEBT

    def test_parse_create_sets_payment_mode_for_savings(self):
        """Test CREATE command for savings sets payment_mode to SAVINGS."""
        result = self.parser.parse("Add savings goal Emergency Fund £1000, saving £100 monthly")
        assert result["intent"] == "CREATE"
        assert result["entities"]["payment_mode"] == PaymentMode.SAVINGS

    def test_parse_create_sets_payment_mode_recurring_for_regular(self):
        """Test CREATE command for regular subscription sets payment_mode to RECURRING."""
        result = self.parser.parse("Add Netflix £15.99 monthly")
        assert result["intent"] == "CREATE"
        assert result["entities"]["payment_mode"] == PaymentMode.RECURRING

    def test_normalize_payment_mode_string(self):
        """Test normalizing payment_mode from string."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {"payment_mode": "debt"},
            }
        )
        assert result["entities"]["payment_mode"] == PaymentMode.DEBT

    def test_normalize_payment_mode_one_time_variants(self):
        """Test normalizing one_time variants."""
        for variant in ["one_time", "one-time", "onetime"]:
            result = self.parser._normalize_result(
                {
                    "intent": "create",
                    "entities": {"payment_mode": variant},
                }
            )
            assert result["entities"]["payment_mode"] == PaymentMode.ONE_TIME

    def test_normalize_payment_mode_savings_variant(self):
        """Test normalizing savings/saving variants."""
        for variant in ["savings", "saving"]:
            result = self.parser._normalize_result(
                {
                    "intent": "create",
                    "entities": {"payment_mode": variant},
                }
            )
            assert result["entities"]["payment_mode"] == PaymentMode.SAVINGS

    def test_normalize_infers_payment_mode_from_payment_type(self):
        """Test payment_mode is inferred from payment_type when not set."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {"payment_type": "debt"},
            }
        )
        assert result["entities"]["payment_mode"] == PaymentMode.DEBT

    def test_normalize_default_payment_mode_is_recurring(self):
        """Test default payment_mode is RECURRING when neither mode nor type set."""
        result = self.parser._normalize_result(
            {
                "intent": "create",
                "entities": {},
            }
        )
        assert result["entities"]["payment_mode"] == PaymentMode.RECURRING


class TestPaymentTypeDetection:
    """Tests for PaymentType detection from command text."""

    def setup_method(self):
        """Set up parser for testing."""
        self.parser = CommandParser()

    def test_detect_housing_from_rent(self):
        """Test detecting housing type from 'rent' keyword."""
        result = self.parser._detect_payment_type("add my rent payment")
        assert result == PaymentType.HOUSING

    def test_detect_housing_from_mortgage(self):
        """Test detecting housing type from 'mortgage' keyword."""
        result = self.parser._detect_payment_type("add mortgage payment")
        assert result == PaymentType.HOUSING

    def test_detect_utility_from_electric(self):
        """Test detecting utility type from 'electric' keyword."""
        result = self.parser._detect_payment_type("add electric bill")
        assert result == PaymentType.UTILITY

    def test_detect_utility_from_internet(self):
        """Test detecting utility type from 'internet' keyword."""
        result = self.parser._detect_payment_type("add internet bill")
        assert result == PaymentType.UTILITY

    def test_detect_debt_from_owe(self):
        """Test detecting debt type from 'owe' keyword."""
        result = self.parser._detect_payment_type("I owe John money")
        assert result == PaymentType.DEBT

    def test_detect_debt_from_credit_card(self):
        """Test detecting debt type from 'credit card' keyword."""
        result = self.parser._detect_payment_type("add credit card payment")
        assert result == PaymentType.DEBT

    def test_detect_savings_from_save(self):
        """Test detecting savings type from 'save' keyword."""
        result = self.parser._detect_payment_type("save for vacation")
        assert result == PaymentType.SAVINGS

    def test_detect_savings_from_goal(self):
        """Test detecting savings type from 'goal' keyword."""
        result = self.parser._detect_payment_type("savings goal for car")
        assert result == PaymentType.SAVINGS

    def test_detect_insurance_from_insurance(self):
        """Test detecting insurance type from 'insurance' keyword."""
        result = self.parser._detect_payment_type("add health insurance")
        assert result == PaymentType.INSURANCE

    def test_detect_subscription_default(self):
        """Test default is subscription for unrecognized keywords."""
        result = self.parser._detect_payment_type("add something random")
        assert result == PaymentType.SUBSCRIPTION

    def test_detect_subscription_from_netflix(self):
        """Test detecting subscription from 'netflix' keyword."""
        result = self.parser._detect_payment_type("add netflix")
        assert result == PaymentType.SUBSCRIPTION

    def test_detect_subscription_from_spotify(self):
        """Test detecting subscription from 'spotify' keyword."""
        result = self.parser._detect_payment_type("add spotify premium")
        assert result == PaymentType.SUBSCRIPTION
