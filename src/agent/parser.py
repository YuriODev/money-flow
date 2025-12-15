"""Natural language command parser using Claude API with XML prompts.

This module provides the CommandParser class that extracts intent and entities
from natural language commands. It uses Claude Haiku 4.5 as the primary parser
with regex patterns as a fallback for reliability.

Supported intents: CREATE, READ, UPDATE, DELETE, SUMMARY, UPCOMING, CONVERT

Money Flow Support:
- Payment types: subscription, housing, utility, professional_service, insurance, debt, savings, transfer
- Debt tracking: total_owed, remaining_balance, creditor
- Savings tracking: target_amount, current_saved, recipient
"""

import json
import logging
import re
from decimal import Decimal
from typing import Any

import anthropic

from src.agent.prompt_loader import PromptLoader
from src.models.subscription import Frequency, PaymentType

logger = logging.getLogger(__name__)

# Payment type detection hints (keywords that suggest a payment type)
PAYMENT_TYPE_HINTS: dict[PaymentType, list[str]] = {
    PaymentType.SUBSCRIPTION: [
        "netflix",
        "spotify",
        "disney",
        "hulu",
        "youtube",
        "amazon prime",
        "streaming",
        "subscription",
        "sub",
        "premium",
        "plus",
    ],
    PaymentType.HOUSING: ["rent", "mortgage", "landlord", "property", "lease"],
    PaymentType.UTILITY: [
        "electric",
        "electricity",
        "gas",
        "water",
        "internet",
        "broadband",
        "council tax",
        "utility",
        "edf",
        "thames water",
        "energy",
        "phone bill",
    ],
    PaymentType.PROFESSIONAL_SERVICE: [
        "therapist",
        "therapy",
        "coach",
        "coaching",
        "trainer",
        "training",
        "tutor",
        "tutoring",
        "gym",
        "cleaner",
        "cleaning",
        "lesson",
    ],
    PaymentType.INSURANCE: [
        "insurance",
        "bupa",
        "applecare",
        "health insurance",
        "car insurance",
        "life insurance",
        "cover",
        "protection",
    ],
    PaymentType.DEBT: [
        "debt",
        "owe",
        "owed",
        "credit card",
        "loan",
        "repayment",
        "paying back",
        "borrowed",
        "balance",
        "repay",
    ],
    PaymentType.SAVINGS: [
        "savings",
        "saving",
        "save",
        "goal",
        "target",
        "emergency fund",
        "holiday fund",
        "investment",
        "invest",
    ],
    PaymentType.TRANSFER: [
        "transfer",
        "send money",
        "family support",
        "partner",
        "girlfriend",
        "boyfriend",
        "wife",
        "husband",
        "child",
        "daughter",
        "son",
    ],
}


class CommandParser:
    """Parse natural language commands using Claude Haiku 4.5 with XML prompts.

    This dual-mode parser uses Claude AI as primary with regex fallback,
    ensuring reliable command parsing even when the AI API is unavailable.

    Attributes:
        prompt_loader: Loads XML prompts for Claude API.
        use_ai: Whether AI parsing is enabled (requires API key).
        client: Anthropic client instance (if AI enabled).
        model: Claude model identifier.

    Example:
        >>> parser = CommandParser(api_key="sk-ant-...")
        >>> result = parser.parse("Add Netflix for £15.99 monthly")
        >>> result["intent"]
        'CREATE'
        >>> result["entities"]["name"]
        'Netflix'
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize parser with Claude API client.

        Args:
            api_key: Anthropic API key for AI parsing. If None, uses
                regex-only parsing mode.

        Example:
            >>> # AI-enabled parsing
            >>> parser = CommandParser(api_key="sk-ant-...")

            >>> # Regex-only parsing
            >>> parser = CommandParser()
        """
        self.prompt_loader = PromptLoader()
        self.use_ai = api_key is not None

        if self.use_ai:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-haiku-4.5-20250929"  # Haiku 4.5

    def parse(self, command: str) -> dict[str, Any]:
        """Parse a command and return intent and entities.

        Routes to AI or regex parsing based on availability.

        Args:
            command: Natural language command from user.

        Returns:
            Dictionary containing:
            - intent: Classified intent (CREATE, READ, UPDATE, etc.)
            - entities: Extracted entities (name, amount, frequency, etc.)
            - confidence: Parsing confidence score (0.0-1.0)

        Example:
            >>> result = parser.parse("Show all subscriptions")
            >>> result["intent"]
            'READ'
        """
        if self.use_ai:
            return self._parse_with_ai(command)
        else:
            return self._parse_with_regex(command)

    def _parse_with_ai(self, command: str) -> dict[str, Any]:
        """Parse command using Claude Haiku 4.5.

        Sends the command to Claude API with structured XML prompts
        and extracts JSON response with intent and entities.

        Args:
            command: Natural language command to parse.

        Returns:
            Normalized parsing result with intent, entities, confidence.
            Falls back to regex parsing on any error.

        Example:
            >>> result = parser._parse_with_ai("Add Spotify £9.99 monthly")
            >>> result["intent"]
            'CREATE'
        """
        try:
            system_prompt = self.prompt_loader.get_system_prompt()
            user_prompt = self.prompt_loader.build_command_prompt(command)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract JSON from response
            content = response.content[0].text
            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Normalize the result
                return self._normalize_result(result)
            else:
                # Fall back to regex parsing
                return self._parse_with_regex(command)

        except Exception as e:
            logger.warning(f"AI parsing error: {e}")
            # Fall back to regex parsing
            return self._parse_with_regex(command)

    def _normalize_result(self, result: dict) -> dict[str, Any]:
        """Normalize AI parsing result.

        Converts raw AI output to standardized format with proper types.
        Includes Money Flow payment type normalization.

        Args:
            result: Raw JSON result from Claude API.

        Returns:
            Normalized dictionary with:
            - intent: Uppercase intent string
            - entities: Type-converted entities (Decimal amounts, Frequency/PaymentType enums)
            - confidence: Confidence score

        Example:
            >>> normalized = parser._normalize_result({
            ...     "intent": "create",
            ...     "entities": {"amount": "15.99", "payment_type": "debt"}
            ... })
            >>> normalized["entities"]["amount"]
            Decimal('15.99')
        """
        intent = result.get("intent", "UNKNOWN").upper()
        entities = result.get("entities", {})

        # Normalize frequency
        if "frequency" in entities:
            freq = entities["frequency"].lower()
            freq_map = {
                "daily": Frequency.DAILY,
                "weekly": Frequency.WEEKLY,
                "biweekly": Frequency.BIWEEKLY,
                "bi-weekly": Frequency.BIWEEKLY,
                "fortnightly": Frequency.BIWEEKLY,
                "monthly": Frequency.MONTHLY,
                "quarterly": Frequency.QUARTERLY,
                "yearly": Frequency.YEARLY,
                "annual": Frequency.YEARLY,
                "annually": Frequency.YEARLY,
            }
            entities["frequency"] = freq_map.get(freq, Frequency.MONTHLY)

        # Normalize amount fields (amount, total_owed, remaining_balance, target_amount, current_saved)
        decimal_fields = [
            "amount",
            "total_owed",
            "remaining_balance",
            "target_amount",
            "current_saved",
        ]
        for field in decimal_fields:
            if field in entities and entities[field] is not None:
                if not isinstance(entities[field], Decimal):
                    try:
                        entities[field] = Decimal(str(entities[field]))
                    except Exception:
                        pass

        # Normalize payment_type
        if "payment_type" in entities:
            pt = entities["payment_type"].lower()
            pt_map = {
                "subscription": PaymentType.SUBSCRIPTION,
                "housing": PaymentType.HOUSING,
                "utility": PaymentType.UTILITY,
                "professional_service": PaymentType.PROFESSIONAL_SERVICE,
                "insurance": PaymentType.INSURANCE,
                "debt": PaymentType.DEBT,
                "savings": PaymentType.SAVINGS,
                "transfer": PaymentType.TRANSFER,
            }
            entities["payment_type"] = pt_map.get(pt, PaymentType.SUBSCRIPTION)

        # Ensure currency is set
        if "currency" not in entities:
            entities["currency"] = "GBP"

        return {
            "intent": intent,
            "entities": entities,
            "confidence": result.get("confidence", 0.9),
        }

    def _parse_with_regex(self, command: str) -> dict[str, Any]:
        """Fallback regex-based parsing with Money Flow support.

        Uses predefined patterns to extract intent and entities when
        AI parsing is unavailable or fails. Includes payment type detection
        for debt, savings, housing, utilities, etc.

        Args:
            command: Natural language command to parse.

        Returns:
            Dictionary with intent, entities, and confidence.
            Returns UNKNOWN intent if no patterns match.

        Example:
            >>> result = parser._parse_with_regex("show my subscriptions")
            >>> result["intent"]
            'READ'
        """
        command_lower = command.lower().strip()

        # Define patterns with GBP as default - expanded for Money Flow
        patterns = {
            "create": [
                # Debt patterns (must come before generic patterns)
                r"(?:add\s+)?(?:i\s+)?owe\s+(?P<creditor>\w+)\s+(?:£|\$|€)?(?P<total_owed>[\d.]+).*?paying\s+(?:back\s+)?(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                r"add\s+(?:debt\s+to|credit\s+card)\s+(?P<name>.+?)\s+(?:£|\$|€)?(?P<total_owed>[\d.]+).*?paying\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                # Savings patterns
                r"add\s+(?:savings?\s+(?:goal|target)?|emergency\s+fund)\s+(?P<name>.+?)\s+(?:£|\$|€)?(?P<target_amount>[\d.]+).*?saving\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                r"save\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?\s+(?:to|for)\s+(?P<recipient>.+)",
                # Housing patterns
                r"add\s+(?:my\s+)?(?:rent|mortgage)\s+(?:payment\s+)?(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                # General patterns
                r"add\s+(?P<name>.+?)\s+(?:subscription\s+)?(?:for\s+)?(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                r"subscribe\s+to\s+(?P<name>.+?)\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s*(?P<frequency>daily|weekly|biweekly|monthly|quarterly|yearly)?",
                r"new\s+(?:subscription|payment)\s+(?P<name>.+?)\s+(?:£|\$|€)?(?P<amount>[\d.]+)",
            ],
            "read": [
                # Money Flow patterns
                r"(?:show|list|get)\s+(?:all\s+)?(?:my\s+)?(?P<payment_type>debts?|savings?|utilities?|subscriptions?|payments?|housing|insurance)",
                r"(?:show|list|get)\s+(?:all\s+)?(?:my\s+)?(?P<filter>active\s+)?(?:subscriptions?|payments?)",
                r"what\s+(?:are\s+)?(?:my\s+)?(?:subscriptions?|payments?|debts?|savings?)",
            ],
            "summary": [
                # Money Flow summary patterns
                r"(?:how\s+much|what(?:'s|\s+is))\s+(?:my\s+)?total\s+(?P<payment_type>debt|savings?)",
                r"(?:show|get)\s+(?:my\s+)?(?P<payment_type>debt|savings?)\s+(?:summary|progress|total)",
                r"(?:how\s+much|what)\s+am\s+i\s+spending",
                r"(?:show|get)\s+(?:my\s+)?(?:spending\s+)?summary",
                r"total\s+(?:spending|cost|expenses?)",
                r"how\s+much\s+have\s+i\s+saved",
                # Historical date period patterns
                r"(?:how\s+much|what)\s+(?:did\s+i\s+)?spen[dt]\s+(?:in\s+)?(?P<date_period>last\s+month|last\s+year|this\s+month|this\s+year|(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?)",
                r"(?:spending|expenses?)\s+(?:in\s+|for\s+)?(?P<date_period>last\s+month|last\s+year|this\s+month|this\s+year|(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?)",
                r"(?:show|get)\s+(?:my\s+)?(?P<date_period>last\s+month(?:'s)?|last\s+year(?:'s)?|this\s+month(?:'s)?|this\s+year(?:'s)?)\s+(?:spending|expenses?|summary)",
            ],
            "upcoming": [
                r"what(?:'s|\s+is)\s+(?:due|coming|upcoming)",
                r"(?:show|list)\s+upcoming\s+(?:payments?|subscriptions?)",
                r"next\s+(?:payments?|bills?)",
                r"when\s+is\s+(?:my\s+)?(?P<name>.+?)\s+due",
            ],
            "delete": [
                r"(?:mark\s+)?(?P<name>.+?)\s+(?:debt\s+)?(?:as\s+)?paid\s+off",
                r"(?:cancel|delete|remove)\s+(?:my\s+)?(?P<name>.+?)(?:\s+(?:subscription|payment|debt|goal))?$",
            ],
            "update": [
                # Money Flow update patterns
                r"(?:i\s+)?paid\s+(?:£|\$|€)?(?P<payment_amount>[\d.]+)\s+off\s+(?:my\s+)?(?P<name>.+)",
                r"add\s+(?:£|\$|€)?(?P<add_amount>[\d.]+)\s+to\s+(?:my\s+)?(?P<name>.+?)\s+savings?",
                r"update\s+(?:my\s+)?(?P<name>.+?)\s+(?:remaining\s+)?balance\s+to\s+(?:£|\$|€)?(?P<remaining_balance>[\d.]+)",
                r"update\s+(?:my\s+)?(?P<name>.+?)\s+(?:savings?\s+)?goal\s+to\s+(?:£|\$|€)?(?P<target_amount>[\d.]+)",
                r"(?:update|change|modify)\s+(?P<name>.+?)\s+to\s+(?:£|\$|€)?(?P<amount>[\d.]+)",
                r"(?:set|change)\s+(?P<name>.+?)\s+(?:amount\s+)?to\s+(?:£|\$|€)?(?P<amount>[\d.]+)",
            ],
            "convert": [
                r"convert\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s+(?:from\s+)?(?P<from_curr>\w{3})?\s+to\s+(?P<to_curr>\w{3})",
                r"how\s+much\s+is\s+(?:£|\$|€)?(?P<amount>[\d.]+)\s+in\s+(?P<to_curr>\w{3})",
            ],
        }

        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, command_lower, re.IGNORECASE)
                if match:
                    entities = self._extract_entities(intent, match, command_lower)
                    return {
                        "intent": intent.upper(),
                        "entities": entities,
                        "confidence": 0.85,
                    }

        return {
            "intent": "UNKNOWN",
            "entities": {},
            "confidence": 0.0,
            "original": command,
        }

    def _extract_entities(self, intent: str, match: re.Match, command: str) -> dict[str, Any]:
        """Extract entities from regex match with Money Flow support.

        Extracts named groups from regex match and converts to proper
        types. Handles currency detection, payment type inference,
        and Money Flow specific fields (debt, savings).

        Args:
            intent: Classified intent string.
            match: Regex match object with named groups.
            command: Original command for additional extraction.

        Returns:
            Dictionary of extracted entities with proper types.

        Example:
            >>> match = re.search(r"add (?P<name>\\w+) £(?P<amount>[\\d.]+)", "add netflix £15")
            >>> entities = parser._extract_entities("create", match, "add netflix £15")
            >>> entities["currency"]
            'GBP'
        """
        entities: dict[str, Any] = {}
        groups = match.groupdict()

        # Extract name
        if "name" in groups and groups["name"]:
            entities["name"] = groups["name"].strip()

        # Extract amount fields (all converted to Decimal)
        decimal_fields = [
            "amount",
            "total_owed",
            "remaining_balance",
            "target_amount",
            "current_saved",
            "payment_amount",
            "add_amount",
        ]
        for field in decimal_fields:
            if field in groups and groups[field]:
                entities[field] = Decimal(groups[field])

        # Extract creditor/recipient
        if "creditor" in groups and groups["creditor"]:
            entities["creditor"] = groups["creditor"].strip()
            # Auto-generate name from creditor if not present
            if "name" not in entities:
                entities["name"] = f"Debt to {groups['creditor'].strip().title()}"

        if "recipient" in groups and groups["recipient"]:
            entities["recipient"] = groups["recipient"].strip()
            # Auto-generate name from recipient if not present
            if "name" not in entities:
                entities["name"] = f"Savings: {groups['recipient'].strip().title()}"

        # Detect currency from symbol or default to GBP
        currency = "GBP"
        if "£" in command:
            currency = "GBP"
        elif "$" in command:
            currency = "USD"
        elif "€" in command:
            currency = "EUR"
        elif "₴" in command or "uah" in command.lower():
            currency = "UAH"
        entities["currency"] = currency

        # Extract frequency
        if "frequency" in groups and groups["frequency"]:
            freq_map = {
                "daily": Frequency.DAILY,
                "weekly": Frequency.WEEKLY,
                "biweekly": Frequency.BIWEEKLY,
                "monthly": Frequency.MONTHLY,
                "quarterly": Frequency.QUARTERLY,
                "yearly": Frequency.YEARLY,
            }
            entities["frequency"] = freq_map.get(groups["frequency"].lower(), Frequency.MONTHLY)
        elif intent == "create":
            entities["frequency"] = Frequency.MONTHLY

        # Detect payment type from command context
        if intent == "create" and "payment_type" not in entities:
            entities["payment_type"] = self._detect_payment_type(command)

        # Handle payment_type from read/summary patterns
        if "payment_type" in groups and groups["payment_type"]:
            pt_text = groups["payment_type"].lower().rstrip("s")  # Remove trailing 's'
            pt_map = {
                "debt": PaymentType.DEBT,
                "saving": PaymentType.SAVINGS,
                "utility": PaymentType.UTILITY,
                "subscription": PaymentType.SUBSCRIPTION,
                "payment": None,  # All payments
                "housing": PaymentType.HOUSING,
                "insurance": PaymentType.INSURANCE,
            }
            if pt_text in pt_map:
                entities["payment_type"] = pt_map[pt_text]

        if "filter" in groups and groups["filter"]:
            if "active" in groups["filter"].lower():
                entities["is_active"] = True

        # Extract date period for historical queries
        if "date_period" in groups and groups["date_period"]:
            date_range = self._parse_date_period(groups["date_period"])
            if date_range:
                entities["date_from"] = date_range["from"]
                entities["date_to"] = date_range["to"]
                entities["date_period_label"] = groups["date_period"].strip()

        # Extract category from command if mentioned
        category_match = re.search(r"(?:category|type|for)\s+(\w+)", command, re.IGNORECASE)
        if category_match:
            entities["category"] = category_match.group(1)

        # Handle currency conversion
        if intent == "convert":
            if "from_curr" in groups and groups["from_curr"]:
                entities["from_currency"] = groups["from_curr"].upper()
            elif "£" in command:
                entities["from_currency"] = "GBP"
            elif "$" in command:
                entities["from_currency"] = "USD"
            elif "€" in command:
                entities["from_currency"] = "EUR"

            if "to_curr" in groups and groups["to_curr"]:
                entities["to_currency"] = groups["to_curr"].upper()

        return entities

    def _detect_payment_type(self, command: str) -> PaymentType:
        """Detect payment type from command text using keyword hints.

        Args:
            command: The command text to analyze.

        Returns:
            Detected PaymentType or SUBSCRIPTION as default.

        Example:
            >>> parser._detect_payment_type("add my rent payment")
            PaymentType.HOUSING
        """
        command_lower = command.lower()

        for payment_type, keywords in PAYMENT_TYPE_HINTS.items():
            for keyword in keywords:
                if keyword in command_lower:
                    return payment_type

        return PaymentType.SUBSCRIPTION

    def _parse_date_period(self, period: str) -> dict[str, str] | None:
        """Parse a date period string into start and end dates.

        Converts human-readable date periods (e.g., "last month", "january")
        into ISO date strings for filtering historical queries.

        Args:
            period: Date period string (e.g., "last month", "january 2024").

        Returns:
            Dictionary with 'from' and 'to' ISO date strings, or None if invalid.

        Example:
            >>> # If current date is 2025-03-15
            >>> parser._parse_date_period("last month")
            {'from': '2025-02-01', 'to': '2025-02-28'}
            >>> parser._parse_date_period("january")
            {'from': '2025-01-01', 'to': '2025-01-31'}
        """
        from calendar import monthrange
        from datetime import datetime

        period_lower = period.lower().strip().rstrip("'s")  # Remove possessive
        today = datetime.now()
        current_year = today.year
        current_month = today.month

        # Month name mapping
        month_names = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        try:
            if period_lower == "last month":
                # Previous month
                if current_month == 1:
                    year, month = current_year - 1, 12
                else:
                    year, month = current_year, current_month - 1
                _, last_day = monthrange(year, month)
                return {
                    "from": f"{year}-{month:02d}-01",
                    "to": f"{year}-{month:02d}-{last_day:02d}",
                }

            elif period_lower == "this month":
                _, last_day = monthrange(current_year, current_month)
                return {
                    "from": f"{current_year}-{current_month:02d}-01",
                    "to": f"{current_year}-{current_month:02d}-{last_day:02d}",
                }

            elif period_lower == "last year":
                last_year = current_year - 1
                return {
                    "from": f"{last_year}-01-01",
                    "to": f"{last_year}-12-31",
                }

            elif period_lower == "this year":
                return {
                    "from": f"{current_year}-01-01",
                    "to": f"{current_year}-12-31",
                }

            else:
                # Check for month name (with optional year)
                parts = period_lower.split()
                month_name = parts[0]

                if month_name in month_names:
                    month = month_names[month_name]
                    # Check if year is specified
                    if len(parts) > 1 and parts[1].isdigit():
                        year = int(parts[1])
                    else:
                        # Use current year, or previous year if month is in future
                        year = current_year
                        if month > current_month:
                            year = current_year - 1

                    _, last_day = monthrange(year, month)
                    return {
                        "from": f"{year}-{month:02d}-01",
                        "to": f"{year}-{month:02d}-{last_day:02d}",
                    }

        except (ValueError, KeyError):
            logger.warning(f"Could not parse date period: {period}")

        return None
