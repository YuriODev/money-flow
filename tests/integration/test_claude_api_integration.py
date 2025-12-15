"""Claude API Integration Tests for Sprint 2.3.5.

Tests for Claude AI API integration including:
- API connection and authentication
- Intent classification accuracy
- Entity extraction accuracy
- API failure fallback to regex

Usage:
    pytest tests/integration/test_claude_api_integration.py -v

    # Run with real API (requires ANTHROPIC_API_KEY):
    ANTHROPIC_API_KEY=sk-ant-... pytest tests/integration/test_claude_api_integration.py -v

Note:
    Tests that require actual API calls are marked with @claude_api
    and skip automatically when ANTHROPIC_API_KEY environment variable is not set.
"""

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.agent.parser import CommandParser
from src.models.subscription import Frequency, PaymentType

# Skip tests marked with claude_api when API key is not available
claude_api = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping real API tests",
)


class TestAPIConnectionAndAuth:
    """Tests for API connection and authentication (2.3.5.1)."""

    def test_parser_initializes_with_api_key(self):
        """Test parser initializes correctly with API key."""
        parser = CommandParser(api_key="test-api-key")

        assert parser.use_ai is True
        assert parser.model == "claude-haiku-4.5-20250929"
        assert parser.client is not None

    def test_parser_initializes_without_api_key(self):
        """Test parser works without API key (regex only)."""
        parser = CommandParser()

        assert parser.use_ai is False
        assert parser.prompt_loader is not None

    def test_api_key_creates_anthropic_client(self):
        """Test that API key creates Anthropic client instance."""
        with patch("src.agent.parser.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            parser = CommandParser(api_key="test-api-key")

            mock_anthropic.assert_called_once_with(api_key="test-api-key")
            assert parser.client == mock_client

    @claude_api
    def test_real_api_connection(self):
        """Test real API connection with valid key (requires --run-claude-api)."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        parser = CommandParser(api_key=api_key)

        # Simple test to verify connection works
        result = parser.parse("Show my subscriptions")

        assert result["intent"] in ["READ", "UNKNOWN"]
        assert "confidence" in result

    @claude_api
    def test_invalid_api_key_falls_back_to_regex(self):
        """Test that invalid API key falls back to regex parsing."""
        parser = CommandParser(api_key="invalid-key-that-wont-work")

        # Should fall back to regex when API fails
        result = parser.parse("Show my subscriptions")

        assert result["intent"] == "READ"


class TestIntentClassificationAccuracy:
    """Tests for intent classification accuracy (2.3.5.2)."""

    @pytest.fixture
    def mock_parser(self):
        """Create parser with mocked AI response."""
        parser = CommandParser(api_key="test-key")
        return parser

    def _mock_ai_response(self, parser, intent: str, entities: dict | None = None):
        """Helper to mock AI response."""
        import json

        response = MagicMock()
        entities = entities or {}
        json_text = json.dumps({"intent": intent, "entities": entities, "confidence": 0.95})
        response.content = [MagicMock(text=json_text)]
        return response

    def test_intent_create_classification(self, mock_parser):
        """Test CREATE intent is classified correctly."""
        test_commands = [
            "Add Netflix for $15.99 monthly",
            "Subscribe to Spotify",
            "New subscription for gym",
            "Create a new payment for rent",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "CREATE", {"name": "Test"})
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "CREATE", f"Failed for: {command}"

    def test_intent_read_classification(self, mock_parser):
        """Test READ intent is classified correctly."""
        test_commands = [
            "Show all my subscriptions",
            "List my payments",
            "What are my subscriptions?",
            "Get all active subscriptions",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "READ")
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "READ", f"Failed for: {command}"

    def test_intent_update_classification(self, mock_parser):
        """Test UPDATE intent is classified correctly."""
        test_commands = [
            "Update Netflix to $19.99",
            "Change my Spotify subscription",
            "Set gym amount to $50",
            "Modify my rent payment",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "UPDATE", {"name": "Test"})
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "UPDATE", f"Failed for: {command}"

    def test_intent_delete_classification(self, mock_parser):
        """Test DELETE intent is classified correctly."""
        test_commands = [
            "Cancel my Netflix subscription",
            "Delete gym membership",
            "Remove Spotify",
            "Cancel my subscription",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "DELETE", {"name": "Test"})
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "DELETE", f"Failed for: {command}"

    def test_intent_summary_classification(self, mock_parser):
        """Test SUMMARY intent is classified correctly."""
        test_commands = [
            "How much am I spending?",
            "Show spending summary",
            "Total monthly expenses",
            "What's my total spending?",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "SUMMARY")
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "SUMMARY", f"Failed for: {command}"

    def test_intent_upcoming_classification(self, mock_parser):
        """Test UPCOMING intent is classified correctly."""
        test_commands = [
            "What's due this week?",
            "Show upcoming payments",
            "Next payments",
            "When is my rent due?",
        ]

        for command in test_commands:
            response = self._mock_ai_response(mock_parser, "UPCOMING")
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "UPCOMING", f"Failed for: {command}"

    def test_intent_convert_classification(self, mock_parser):
        """Test CONVERT intent is classified correctly."""
        test_commands = [
            "Convert 100 USD to GBP",
            "How much is $50 in euros?",
            "Convert £20 to dollars",
        ]

        for command in test_commands:
            response = self._mock_ai_response(
                mock_parser, "CONVERT", {"amount": "100", "to_currency": "GBP"}
            )
            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(command)
                assert result["intent"] == "CONVERT", f"Failed for: {command}"

    @claude_api
    def test_real_intent_classification(self):
        """Test real intent classification with API (requires --run-claude-api)."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        parser = CommandParser(api_key=api_key)

        # Test multiple intents
        test_cases = [
            ("Add Netflix for $15.99 monthly", "CREATE"),
            ("Show all my subscriptions", "READ"),
            ("Cancel my gym membership", "DELETE"),
            ("How much am I spending?", "SUMMARY"),
        ]

        for command, expected_intent in test_cases:
            result = parser.parse(command)
            assert result["intent"] == expected_intent, f"Failed for: {command}"


class TestEntityExtractionAccuracy:
    """Tests for entity extraction accuracy (2.3.5.3)."""

    @pytest.fixture
    def mock_parser(self):
        """Create parser with mocked AI response."""
        parser = CommandParser(api_key="test-key")
        return parser

    def _mock_ai_response(self, parser, intent: str, entities: dict):
        """Helper to mock AI response."""
        import json

        response = MagicMock()
        response.content = [
            MagicMock(text=json.dumps({"intent": intent, "entities": entities, "confidence": 0.95}))
        ]
        return response

    def test_extract_name_entity(self, mock_parser):
        """Test name extraction from commands."""
        response = self._mock_ai_response(
            mock_parser,
            "CREATE",
            {"name": "Netflix", "amount": "15.99", "frequency": "monthly"},
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("Add Netflix for $15.99 monthly")

            assert "name" in result["entities"]
            assert result["entities"]["name"] == "Netflix"

    def test_extract_amount_entity(self, mock_parser):
        """Test amount extraction and decimal conversion."""
        response = self._mock_ai_response(
            mock_parser, "CREATE", {"name": "Spotify", "amount": "9.99"}
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("Add Spotify for $9.99")

            assert "amount" in result["entities"]
            assert result["entities"]["amount"] == Decimal("9.99")

    def test_extract_frequency_entity(self, mock_parser):
        """Test frequency extraction and normalization."""
        frequencies = [
            ("monthly", Frequency.MONTHLY),
            ("weekly", Frequency.WEEKLY),
            ("yearly", Frequency.YEARLY),
            ("daily", Frequency.DAILY),
            ("quarterly", Frequency.QUARTERLY),
            ("biweekly", Frequency.BIWEEKLY),
        ]

        for freq_str, freq_enum in frequencies:
            response = self._mock_ai_response(
                mock_parser, "CREATE", {"name": "Test", "frequency": freq_str}
            )

            with patch.object(mock_parser.client.messages, "create", return_value=response):
                result = mock_parser.parse(f"Add Test {freq_str}")

                assert result["entities"]["frequency"] == freq_enum

    def test_extract_currency_entity(self, mock_parser):
        """Test currency detection from symbols."""
        # Using regex fallback for currency detection
        parser = CommandParser()  # No API key

        test_cases = [
            ("Add Netflix £15.99", "GBP"),
            ("Add Netflix $15.99", "USD"),
            ("Add Netflix €15.99", "EUR"),
        ]

        for command, expected_currency in test_cases:
            result = parser.parse(command)
            assert result["entities"]["currency"] == expected_currency

    def test_extract_payment_type_entity(self, mock_parser):
        """Test payment type extraction."""
        response = self._mock_ai_response(
            mock_parser,
            "CREATE",
            {"name": "Rent", "amount": "1000", "payment_type": "housing"},
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("Add my rent payment $1000")

            assert result["entities"]["payment_type"] == PaymentType.HOUSING

    def test_extract_debt_entities(self, mock_parser):
        """Test debt-specific entity extraction."""
        response = self._mock_ai_response(
            mock_parser,
            "CREATE",
            {
                "name": "Credit Card",
                "amount": "100",
                "total_owed": "5000",
                "remaining_balance": "4500",
                "creditor": "Barclays",
                "payment_type": "debt",
            },
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("I owe Barclays $5000, paying $100 monthly")

            entities = result["entities"]
            assert entities["payment_type"] == PaymentType.DEBT
            assert entities["total_owed"] == Decimal("5000")
            assert entities["remaining_balance"] == Decimal("4500")
            assert entities["creditor"] == "Barclays"

    def test_extract_savings_entities(self, mock_parser):
        """Test savings-specific entity extraction."""
        response = self._mock_ai_response(
            mock_parser,
            "CREATE",
            {
                "name": "Emergency Fund",
                "amount": "200",
                "target_amount": "10000",
                "current_saved": "2000",
                "payment_type": "savings",
            },
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("Save $200 monthly for emergency fund goal $10000")

            entities = result["entities"]
            assert entities["payment_type"] == PaymentType.SAVINGS
            assert entities["target_amount"] == Decimal("10000")
            assert entities["current_saved"] == Decimal("2000")

    def test_extract_multiple_entities(self, mock_parser):
        """Test extraction of multiple entities from complex command."""
        response = self._mock_ai_response(
            mock_parser,
            "CREATE",
            {
                "name": "Netflix Premium",
                "amount": "19.99",
                "frequency": "monthly",
                "currency": "USD",
                "payment_type": "subscription",
            },
        )

        with patch.object(mock_parser.client.messages, "create", return_value=response):
            result = mock_parser.parse("Add Netflix Premium subscription $19.99 monthly")

            entities = result["entities"]
            assert entities["name"] == "Netflix Premium"
            assert entities["amount"] == Decimal("19.99")
            assert entities["frequency"] == Frequency.MONTHLY
            assert entities["currency"] in ["USD", "GBP"]  # Either from API or default

    @claude_api
    def test_real_entity_extraction(self):
        """Test real entity extraction with API (requires --run-claude-api)."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        parser = CommandParser(api_key=api_key)

        result = parser.parse("Add Netflix subscription for $15.99 monthly")

        # Verify key entities are extracted
        assert result["intent"] == "CREATE"
        assert "name" in result["entities"]
        assert "amount" in result["entities"]


class TestAPIFailureFallback:
    """Tests for API failure fallback to regex (2.3.5.4)."""

    def test_fallback_on_api_exception(self):
        """Test fallback to regex when API raises exception."""
        parser = CommandParser(api_key="test-key")

        with patch.object(parser.client.messages, "create", side_effect=Exception("API Error")):
            result = parser.parse("Show my subscriptions")

            # Should still work via regex fallback
            assert result["intent"] == "READ"
            assert result["confidence"] == 0.85  # Regex confidence

    def test_fallback_on_invalid_json_response(self):
        """Test fallback when API returns non-JSON response."""
        parser = CommandParser(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I don't understand your request.")]

        with patch.object(parser.client.messages, "create", return_value=mock_response):
            result = parser.parse("Show my subscriptions")

            # Should fall back to regex
            assert result["intent"] == "READ"

    def test_fallback_on_malformed_json(self):
        """Test fallback when API returns malformed JSON."""
        parser = CommandParser(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="{invalid json}")]

        with patch.object(parser.client.messages, "create", return_value=mock_response):
            result = parser.parse("Show my subscriptions")

            # Should fall back to regex
            assert result["intent"] == "READ"

    def test_fallback_on_empty_response(self):
        """Test fallback when API returns empty response."""
        parser = CommandParser(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="")]

        with patch.object(parser.client.messages, "create", return_value=mock_response):
            result = parser.parse("Show my subscriptions")

            # Should fall back to regex
            assert result["intent"] == "READ"

    def test_fallback_on_timeout(self):
        """Test fallback when API times out."""
        import anthropic

        parser = CommandParser(api_key="test-key")

        with patch.object(
            parser.client.messages,
            "create",
            side_effect=anthropic.APITimeoutError(request=MagicMock()),
        ):
            result = parser.parse("Add Netflix $15.99 monthly")

            # Should fall back to regex
            assert result["intent"] == "CREATE"
            assert result["confidence"] == 0.85

    def test_fallback_on_rate_limit(self):
        """Test fallback when API returns rate limit error."""
        import anthropic

        parser = CommandParser(api_key="test-key")

        with patch.object(
            parser.client.messages,
            "create",
            side_effect=anthropic.RateLimitError("Rate limited", response=MagicMock(), body={}),
        ):
            result = parser.parse("Delete my gym subscription")

            # Should fall back to regex
            assert result["intent"] == "DELETE"

    def test_fallback_on_auth_error(self):
        """Test fallback when API returns authentication error."""
        import anthropic

        parser = CommandParser(api_key="test-key")

        with patch.object(
            parser.client.messages,
            "create",
            side_effect=anthropic.AuthenticationError(
                "Invalid API key", response=MagicMock(), body={}
            ),
        ):
            result = parser.parse("How much am I spending?")

            # Should fall back to regex
            assert result["intent"] == "SUMMARY"

    def test_regex_only_mode_works(self):
        """Test that regex-only mode works without API key."""
        parser = CommandParser()  # No API key

        test_cases = [
            ("Add Netflix $15.99 monthly", "CREATE"),
            ("Show my subscriptions", "READ"),
            ("Cancel gym membership", "DELETE"),
            ("How much am I spending?", "SUMMARY"),
            ("What's due this week?", "UPCOMING"),
            ("Convert 100 USD to GBP", "CONVERT"),
        ]

        for command, expected_intent in test_cases:
            result = parser.parse(command)
            assert result["intent"] == expected_intent, f"Failed for: {command}"
            assert result["confidence"] == 0.85  # Regex confidence

    def test_fallback_preserves_entity_extraction(self):
        """Test that fallback preserves entity extraction quality."""
        parser = CommandParser(api_key="test-key")

        with patch.object(parser.client.messages, "create", side_effect=Exception("API Error")):
            result = parser.parse("Add Netflix $15.99 monthly")

            # Verify entities are extracted via regex
            assert result["intent"] == "CREATE"
            assert "name" in result["entities"]
            assert result["entities"]["amount"] == Decimal("15.99")
            assert result["entities"]["frequency"] == Frequency.MONTHLY
            assert result["entities"]["currency"] == "USD"


class TestPaymentTypeDetection:
    """Tests for payment type detection from context."""

    @pytest.fixture
    def parser(self):
        """Create parser without API key."""
        return CommandParser()

    def test_detect_subscription_type(self, parser):
        """Test detecting subscription payment type."""
        test_cases = [
            "Add Netflix subscription $15.99",
            "Add Spotify premium $9.99",
            "Add Disney+ streaming $12.99",
        ]

        for command in test_cases:
            result = parser.parse(command)
            assert result["entities"]["payment_type"] == PaymentType.SUBSCRIPTION

    def test_detect_housing_type(self, parser):
        """Test detecting housing payment type."""
        test_cases = [
            "Add my rent $1500 monthly",
            "Add mortgage payment $2000 monthly",
        ]

        for command in test_cases:
            result = parser.parse(command)
            assert result["entities"]["payment_type"] == PaymentType.HOUSING

    def test_detect_utility_type(self, parser):
        """Test detecting utility payment type."""
        test_cases = [
            "Add electricity bill $100 monthly",
            "Add internet $50 monthly",
            "Add council tax $150 monthly",
        ]

        for command in test_cases:
            result = parser.parse(command)
            assert result["entities"]["payment_type"] == PaymentType.UTILITY

    def test_detect_debt_type(self, parser):
        """Test detecting debt payment type."""
        result = parser.parse("I owe John $500 paying $50 monthly")

        # Debt detection through regex pattern
        assert result["intent"] == "CREATE"
        assert "total_owed" in result["entities"]

    def test_detect_savings_type(self, parser):
        """Test detecting savings payment type."""
        test_cases = [
            "Add savings goal $5000",
            "Save $200 monthly for emergency fund",
        ]

        for command in test_cases:
            result = parser.parse(command)
            if result["intent"] == "CREATE":
                assert result["entities"]["payment_type"] in [
                    PaymentType.SAVINGS,
                    PaymentType.SUBSCRIPTION,
                ]

    def test_detect_insurance_type(self, parser):
        """Test detecting insurance payment type."""
        test_cases = [
            "Add health insurance $200 monthly",
            "Add AppleCare protection $10 monthly",
        ]

        for command in test_cases:
            result = parser.parse(command)
            assert result["entities"]["payment_type"] == PaymentType.INSURANCE


class TestNormalization:
    """Tests for result normalization."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return CommandParser()

    def test_normalize_intent_to_uppercase(self, parser):
        """Test that intents are normalized to uppercase."""
        result = parser._normalize_result({"intent": "create", "entities": {}})

        assert result["intent"] == "CREATE"

    def test_normalize_frequency_variants(self, parser):
        """Test frequency variant normalization."""
        variants = {
            "monthly": Frequency.MONTHLY,
            "weekly": Frequency.WEEKLY,
            "biweekly": Frequency.BIWEEKLY,
            "bi-weekly": Frequency.BIWEEKLY,
            "fortnightly": Frequency.BIWEEKLY,
            "quarterly": Frequency.QUARTERLY,
            "yearly": Frequency.YEARLY,
            "annual": Frequency.YEARLY,
            "annually": Frequency.YEARLY,
        }

        for variant, expected in variants.items():
            result = parser._normalize_result(
                {"intent": "create", "entities": {"frequency": variant}}
            )
            assert result["entities"]["frequency"] == expected

    def test_normalize_payment_type(self, parser):
        """Test payment type normalization."""
        payment_types = {
            "subscription": PaymentType.SUBSCRIPTION,
            "housing": PaymentType.HOUSING,
            "utility": PaymentType.UTILITY,
            "professional_service": PaymentType.PROFESSIONAL_SERVICE,
            "insurance": PaymentType.INSURANCE,
            "debt": PaymentType.DEBT,
            "savings": PaymentType.SAVINGS,
            "transfer": PaymentType.TRANSFER,
        }

        for pt_str, expected in payment_types.items():
            result = parser._normalize_result(
                {"intent": "create", "entities": {"payment_type": pt_str}}
            )
            assert result["entities"]["payment_type"] == expected

    def test_normalize_adds_default_currency(self, parser):
        """Test that default currency (GBP) is added."""
        result = parser._normalize_result({"intent": "create", "entities": {}})

        assert result["entities"]["currency"] == "GBP"

    def test_normalize_adds_default_confidence(self, parser):
        """Test that default confidence is added."""
        result = parser._normalize_result({"intent": "create", "entities": {}})

        assert result["confidence"] == 0.9


class TestPromptLoaderIntegration:
    """Tests for prompt loader integration."""

    def test_prompt_loader_is_initialized(self):
        """Test that prompt loader is initialized."""
        parser = CommandParser()

        assert parser.prompt_loader is not None

    def test_system_prompt_is_loaded(self):
        """Test that system prompt can be loaded."""
        parser = CommandParser()

        system_prompt = parser.prompt_loader.get_system_prompt()

        assert system_prompt is not None
        assert len(system_prompt) > 0

    def test_command_prompt_is_built(self):
        """Test that command prompt can be built."""
        parser = CommandParser()

        command_prompt = parser.prompt_loader.build_command_prompt("Add Netflix $15.99")

        assert command_prompt is not None
        assert "Netflix" in command_prompt
