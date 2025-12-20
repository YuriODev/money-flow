"""AI-powered statement analysis service.

This module provides AI-powered analysis of bank statement transactions
to detect recurring payment patterns and classify payment types.

Features:
- Transaction grouping by merchant/description
- Recurring pattern detection (frequency, amount consistency)
- Payment type classification (subscription, utility, housing, etc.)
- Confidence scoring for each detection
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from statistics import mean, stdev
from typing import Any

from anthropic import Anthropic

from src.core.config import settings
from src.services.parsers.base import StatementData, Transaction, TransactionType

logger = logging.getLogger(__name__)


class PaymentTypeClassification(str, Enum):
    """Classification of detected payment types."""

    SUBSCRIPTION = "subscription"
    HOUSING = "housing"
    UTILITY = "utility"
    INSURANCE = "insurance"
    PROFESSIONAL = "professional"
    DEBT = "debt"
    SAVINGS = "savings"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class FrequencyType(str, Enum):
    """Detected payment frequency."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    IRREGULAR = "irregular"


@dataclass
class DetectedPattern:
    """A detected recurring payment pattern."""

    merchant_name: str
    normalized_name: str
    amount: Decimal
    amount_variance: float  # 0.0 = exact, 1.0 = high variance
    frequency: FrequencyType
    payment_type: PaymentTypeClassification
    confidence: float  # 0.0 to 1.0
    transaction_count: int
    first_seen: date
    last_seen: date
    sample_descriptions: list[str] = field(default_factory=list)
    avg_days_between: float = 0.0
    raw_transactions: list[Transaction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "merchant_name": self.merchant_name,
            "normalized_name": self.normalized_name,
            "amount": float(self.amount),
            "amount_variance": self.amount_variance,
            "frequency": self.frequency.value,
            "payment_type": self.payment_type.value,
            "confidence": self.confidence,
            "transaction_count": self.transaction_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "sample_descriptions": self.sample_descriptions[:3],
            "avg_days_between": self.avg_days_between,
        }


# Keywords for payment type classification
PAYMENT_TYPE_KEYWORDS: dict[PaymentTypeClassification, list[str]] = {
    PaymentTypeClassification.SUBSCRIPTION: [
        "netflix",
        "spotify",
        "disney",
        "hbo",
        "amazon prime",
        "apple music",
        "youtube",
        "hulu",
        "paramount",
        "peacock",
        "crunchyroll",
        "audible",
        "adobe",
        "microsoft 365",
        "dropbox",
        "icloud",
        "google one",
        "notion",
        "slack",
        "zoom",
        "github",
        "gitlab",
        "jira",
        "confluence",
        "figma",
        "canva",
        "grammarly",
        "lastpass",
        "1password",
        "nordvpn",
        "expressvpn",
        "openai",
        "anthropic",
        "claude",
        "chatgpt",
        "midjourney",
        "copilot",
        "gym",
        "fitness",
        "peloton",
        "strava",
        "headspace",
        "calm",
    ],
    PaymentTypeClassification.HOUSING: [
        "rent",
        "mortgage",
        "landlord",
        "property",
        "letting",
        "housing",
        "apartment",
        "flat",
        "lease",
        "tenancy",
        "council tax",
        "rates",
    ],
    PaymentTypeClassification.UTILITY: [
        "electric",
        "electricity",
        "gas",
        "water",
        "sewage",
        "energy",
        "british gas",
        "edf",
        "octopus",
        "bulb",
        "ovo",
        "eon",
        "npower",
        "thames water",
        "severn trent",
        "internet",
        "broadband",
        "wifi",
        "bt",
        "virgin media",
        "sky",
        "talk talk",
        "vodafone",
        "ee",
        "o2",
        "three",
        "mobile",
        "phone",
        "tv license",
        "council",
    ],
    PaymentTypeClassification.INSURANCE: [
        "insurance",
        "insure",
        "cover",
        "premium",
        "policy",
        "aviva",
        "axa",
        "admiral",
        "direct line",
        "compare the market",
        "moneysupermarket",
        "health",
        "dental",
        "vision",
        "life insurance",
        "car insurance",
        "home insurance",
        "pet insurance",
        "travel insurance",
        "applecare",
    ],
    PaymentTypeClassification.PROFESSIONAL: [
        "therapist",
        "therapy",
        "counseling",
        "coach",
        "coaching",
        "trainer",
        "tutor",
        "lessons",
        "class",
        "course",
        "membership",
        "professional",
        "consultant",
        "advisor",
        "accountant",
        "solicitor",
        "lawyer",
    ],
    PaymentTypeClassification.DEBT: [
        "loan",
        "credit",
        "repayment",
        "instalment",
        "payment plan",
        "finance",
        "borrowing",
        "debt",
        "klarna",
        "clearpay",
        "afterpay",
        "paypal credit",
        "credit card",
        "minimum payment",
    ],
    PaymentTypeClassification.SAVINGS: [
        "savings",
        "save",
        "investment",
        "invest",
        "isa",
        "pension",
        "retirement",
        "fund",
        "transfer to savings",
        "regular saver",
        "standing order",
        "vanguard",
        "fidelity",
        "hargreaves",
    ],
    PaymentTypeClassification.TRANSFER: [
        "transfer",
        "payment to",
        "sent to",
        "family",
        "gift",
        "allowance",
        "pocket money",
        "support",
        "maintenance",
    ],
}


class StatementAIService:
    """AI-powered service for analyzing bank statements.

    Uses Claude AI combined with rule-based analysis to detect
    recurring payment patterns in bank statement transactions.
    """

    # Minimum transactions to consider a pattern
    MIN_TRANSACTIONS_FOR_PATTERN = 2

    # Maximum days between transactions for each frequency
    FREQUENCY_DAY_RANGES = {
        FrequencyType.WEEKLY: (5, 9),
        FrequencyType.BIWEEKLY: (12, 18),
        FrequencyType.MONTHLY: (25, 35),
        FrequencyType.QUARTERLY: (85, 100),
        FrequencyType.YEARLY: (350, 380),
    }

    def __init__(self, anthropic_client: Anthropic | None = None) -> None:
        """Initialize the statement AI service.

        Args:
            anthropic_client: Optional Anthropic client for AI analysis
        """
        self.client = anthropic_client or Anthropic(api_key=settings.anthropic_api_key)

    async def analyze_statement(
        self,
        statement: StatementData,
        min_confidence: float = 0.5,
        use_ai: bool = True,
    ) -> list[DetectedPattern]:
        """Analyze a bank statement for recurring patterns.

        Args:
            statement: Parsed statement data with transactions
            min_confidence: Minimum confidence score to include (0.0-1.0)
            use_ai: Whether to use AI for enhanced analysis

        Returns:
            List of detected recurring payment patterns
        """
        if not statement.transactions:
            return []

        # Step 1: Group transactions by normalized merchant name
        grouped = self._group_transactions(statement.transactions)

        # Step 2: Detect patterns in each group
        patterns: list[DetectedPattern] = []
        for merchant, transactions in grouped.items():
            if len(transactions) >= self.MIN_TRANSACTIONS_FOR_PATTERN:
                pattern = self._analyze_group(merchant, transactions)
                if pattern and pattern.confidence >= min_confidence:
                    patterns.append(pattern)

        # Step 3: Use AI for enhanced classification if enabled
        if use_ai and patterns:
            patterns = await self._enhance_with_ai(patterns, statement.currency)

        # Sort by confidence (highest first)
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns

    def _group_transactions(self, transactions: list[Transaction]) -> dict[str, list[Transaction]]:
        """Group transactions by normalized merchant name.

        Args:
            transactions: List of transactions to group

        Returns:
            Dict mapping normalized names to transaction lists
        """
        groups: dict[str, list[Transaction]] = defaultdict(list)

        for txn in transactions:
            # Only consider debits (outgoing payments)
            if txn.transaction_type == TransactionType.CREDIT:
                continue

            normalized = self._normalize_merchant_name(txn.description)
            if normalized:
                groups[normalized].append(txn)

        return dict(groups)

    def _normalize_merchant_name(self, description: str) -> str:
        """Normalize a transaction description to extract merchant name.

        Args:
            description: Raw transaction description

        Returns:
            Normalized merchant name
        """
        if not description:
            return ""

        # Convert to lowercase
        name = description.lower().strip()

        # Remove common payment prefixes
        prefixes_to_remove = [
            r"^(card payment to |payment to |direct debit to |dd |ddr |standing order to |so |)",
            r"^(purchase |pos |card |debit card |visa |mastercard |)",
            r"^(ref[:\s]*\w+\s+|reference[:\s]*\w+\s+)",
        ]
        for prefix in prefixes_to_remove:
            name = re.sub(prefix, "", name, flags=re.IGNORECASE)

        # Remove trailing reference numbers and dates
        name = re.sub(r"\s+\d{2,}[-/]\d{2,}[-/]?\d{0,4}$", "", name)
        name = re.sub(r"\s+ref[:\s]*\w+$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+\*+\d+$", "", name)
        name = re.sub(r"\s+\d{6,}$", "", name)

        # Remove location info (city, country codes)
        name = re.sub(
            r"\s+(gb|uk|us|eu|london|manchester|birmingham)$", "", name, flags=re.IGNORECASE
        )

        # Clean up whitespace
        name = " ".join(name.split())

        # Keep only first 50 chars to avoid overly long names
        return name[:50].strip()

    def _analyze_group(
        self, merchant: str, transactions: list[Transaction]
    ) -> DetectedPattern | None:
        """Analyze a group of transactions for patterns.

        Args:
            merchant: Normalized merchant name
            transactions: List of transactions for this merchant

        Returns:
            DetectedPattern if a recurring pattern is found, None otherwise
        """
        if len(transactions) < self.MIN_TRANSACTIONS_FOR_PATTERN:
            return None

        # Sort by date
        sorted_txns = sorted(transactions, key=lambda t: t.date)

        # Calculate amount statistics
        amounts = [abs(t.amount) for t in sorted_txns]
        avg_amount = Decimal(str(mean([float(a) for a in amounts])))

        # Calculate amount variance
        if len(amounts) > 1:
            try:
                amount_std = stdev([float(a) for a in amounts])
                amount_variance = min(1.0, amount_std / float(avg_amount)) if avg_amount else 1.0
            except Exception:
                amount_variance = 0.5
        else:
            amount_variance = 0.0

        # Calculate days between transactions
        days_between: list[int] = []
        for i in range(1, len(sorted_txns)):
            delta = (sorted_txns[i].date - sorted_txns[i - 1].date).days
            if delta > 0:
                days_between.append(delta)

        if not days_between:
            return None

        avg_days = mean(days_between)

        # Detect frequency
        frequency = self._detect_frequency(avg_days, days_between)

        # Calculate confidence based on consistency
        confidence = self._calculate_confidence(
            transaction_count=len(sorted_txns),
            amount_variance=amount_variance,
            days_between=days_between,
            frequency=frequency,
        )

        # Classify payment type based on keywords
        payment_type = self._classify_payment_type(merchant, sorted_txns)

        # Get original merchant name from first transaction
        original_name = sorted_txns[0].description[:100] if sorted_txns else merchant

        return DetectedPattern(
            merchant_name=original_name,
            normalized_name=merchant,
            amount=avg_amount.quantize(Decimal("0.01")),
            amount_variance=amount_variance,
            frequency=frequency,
            payment_type=payment_type,
            confidence=confidence,
            transaction_count=len(sorted_txns),
            first_seen=sorted_txns[0].date,
            last_seen=sorted_txns[-1].date,
            sample_descriptions=[t.description for t in sorted_txns[:3]],
            avg_days_between=avg_days,
            raw_transactions=sorted_txns,
        )

    def _detect_frequency(self, avg_days: float, days_between: list[int]) -> FrequencyType:
        """Detect the payment frequency from average days between payments.

        Args:
            avg_days: Average days between payments
            days_between: List of actual days between each payment

        Returns:
            Detected frequency type
        """
        for frequency, (min_days, max_days) in self.FREQUENCY_DAY_RANGES.items():
            if min_days <= avg_days <= max_days:
                return frequency

        return FrequencyType.IRREGULAR

    def _calculate_confidence(
        self,
        transaction_count: int,
        amount_variance: float,
        days_between: list[int],
        frequency: FrequencyType,
    ) -> float:
        """Calculate confidence score for a detected pattern.

        Args:
            transaction_count: Number of transactions in pattern
            amount_variance: Variance in payment amounts (0-1)
            days_between: Days between each transaction
            frequency: Detected frequency

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Base confidence from transaction count
        count_score = min(1.0, transaction_count / 6)  # Max at 6 transactions

        # Amount consistency score (inverted variance)
        amount_score = 1.0 - amount_variance

        # Timing consistency score
        if frequency != FrequencyType.IRREGULAR and len(days_between) > 1:
            try:
                timing_std = stdev(days_between)
                avg_days = mean(days_between)
                timing_variance = timing_std / avg_days if avg_days else 1.0
                timing_score = max(0.0, 1.0 - timing_variance)
            except Exception:
                timing_score = 0.5
        else:
            timing_score = 0.3 if frequency == FrequencyType.IRREGULAR else 0.5

        # Frequency bonus (regular frequencies get a boost)
        frequency_bonus = 0.0 if frequency == FrequencyType.IRREGULAR else 0.1

        # Weighted average
        confidence = count_score * 0.3 + amount_score * 0.3 + timing_score * 0.3 + frequency_bonus

        return round(min(1.0, confidence), 2)

    def _classify_payment_type(
        self, merchant: str, transactions: list[Transaction]
    ) -> PaymentTypeClassification:
        """Classify payment type based on merchant name and keywords.

        Args:
            merchant: Normalized merchant name
            transactions: List of transactions

        Returns:
            Classified payment type
        """
        # Combine merchant name with transaction descriptions
        text_to_check = merchant.lower()
        for txn in transactions[:3]:
            text_to_check += " " + txn.description.lower()

        # Check each payment type's keywords
        for payment_type, keywords in PAYMENT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return payment_type

        return PaymentTypeClassification.UNKNOWN

    async def _enhance_with_ai(
        self, patterns: list[DetectedPattern], currency: str
    ) -> list[DetectedPattern]:
        """Use Claude AI to enhance pattern classification.

        Args:
            patterns: Detected patterns to enhance
            currency: Statement currency

        Returns:
            Enhanced patterns with AI classifications
        """
        try:
            # Build prompt for Claude
            prompt = self._build_ai_prompt(patterns, currency)

            response = self.client.messages.create(
                model="claude-haiku-4-5-20250929",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse AI response and update patterns
            ai_text = response.content[0].text if response.content else ""
            patterns = self._parse_ai_response(patterns, ai_text)

        except Exception as e:
            logger.warning(f"AI enhancement failed, using rule-based only: {e}")

        return patterns

    def _build_ai_prompt(self, patterns: list[DetectedPattern], currency: str) -> str:
        """Build prompt for Claude AI analysis.

        Args:
            patterns: Detected patterns
            currency: Statement currency

        Returns:
            Formatted prompt string
        """
        patterns_text = "\n".join(
            [
                f"- {p.normalized_name}: {currency} {p.amount}, {p.frequency.value}, "
                f"{p.transaction_count} transactions, samples: {p.sample_descriptions[:2]}"
                for p in patterns[:20]  # Limit to 20 patterns
            ]
        )

        return f"""Analyze these recurring payment patterns from a bank statement and classify each one.

PATTERNS DETECTED:
{patterns_text}

For each pattern, provide:
1. A clean merchant/service name
2. Payment type (subscription, housing, utility, insurance, professional, debt, savings, transfer, or unknown)
3. Confidence adjustment (-0.2 to +0.2) based on how certain the classification is

Respond in this format for each pattern (one per line):
PATTERN: [normalized_name] | NAME: [clean name] | TYPE: [payment_type] | ADJUST: [confidence adjustment]

Only include patterns you can classify. Focus on accuracy."""

    def _parse_ai_response(
        self, patterns: list[DetectedPattern], ai_response: str
    ) -> list[DetectedPattern]:
        """Parse AI response and update patterns.

        Args:
            patterns: Original patterns
            ai_response: Claude's response text

        Returns:
            Updated patterns
        """
        # Create lookup by normalized name
        pattern_lookup = {p.normalized_name: p for p in patterns}

        # Parse each line of AI response
        for line in ai_response.split("\n"):
            if not line.startswith("PATTERN:"):
                continue

            try:
                parts = line.split("|")
                if len(parts) < 4:
                    continue

                # Extract values
                normalized = parts[0].replace("PATTERN:", "").strip()
                clean_name = parts[1].replace("NAME:", "").strip()
                type_str = parts[2].replace("TYPE:", "").strip().lower()
                adjust_str = parts[3].replace("ADJUST:", "").strip()

                # Find matching pattern
                if normalized in pattern_lookup:
                    pattern = pattern_lookup[normalized]

                    # Update merchant name
                    if clean_name:
                        pattern.merchant_name = clean_name

                    # Update payment type
                    try:
                        pattern.payment_type = PaymentTypeClassification(type_str)
                    except ValueError:
                        pass

                    # Apply confidence adjustment
                    try:
                        adjust = float(adjust_str)
                        pattern.confidence = round(
                            max(0.0, min(1.0, pattern.confidence + adjust)), 2
                        )
                    except ValueError:
                        pass

            except Exception as e:
                logger.debug(f"Failed to parse AI line: {e}")
                continue

        return patterns


def get_statement_ai_service(
    anthropic_client: Anthropic | None = None,
) -> StatementAIService:
    """Factory function for statement AI service.

    Args:
        anthropic_client: Optional Anthropic client

    Returns:
        Configured StatementAIService
    """
    return StatementAIService(anthropic_client)
