"""Unit tests for Sprint 5.5 - Statement Import features.

This module contains comprehensive tests for:
- Statement parser base classes and utilities
- CSV statement parser
- StatementAIService for AI pattern detection
- DuplicateDetector for fuzzy matching
- Statement import schemas
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.subscription import Frequency, Subscription
from src.schemas.statement import (
    BulkUpdateDetectedRequest,
    ConfirmImportRequest,
    DetectedSubscriptionUpdate,
    DuplicateCheckRequest,
    DuplicateMatch,
    ImportJobCreate,
    ImportJobResponse,
    ImportPreviewSummary,
    ResolveDuplicateRequest,
    StatementUploadResponse,
)
from src.services.duplicate_detector import DuplicateDetector
from src.services.duplicate_detector import DuplicateMatch as DuplicateMatchResult
from src.services.parsers.base import (
    EmptyStatementError,
    ParseError,
    ParserError,
    StatementData,
    StatementFormat,
    Transaction,
    TransactionType,
    UnsupportedFormatError,
    detect_format,
)
from src.services.statement_ai_service import (
    PAYMENT_TYPE_KEYWORDS,
    DetectedPattern,
    FrequencyType,
    PaymentTypeClassification,
    StatementAIService,
)

# =============================================================================
# Transaction Tests
# =============================================================================


class TestTransaction:
    """Tests for Transaction dataclass."""

    def test_transaction_creation_basic(self) -> None:
        """Test basic transaction creation."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Netflix Subscription",
        )
        assert txn.date == date(2024, 1, 15)
        assert txn.amount == Decimal("-50.00")
        assert txn.description == "Netflix Subscription"
        assert txn.transaction_type == TransactionType.DEBIT

    def test_transaction_auto_type_inference_debit(self) -> None:
        """Test automatic transaction type inference for debit."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-100.00"),
            description="Payment",
        )
        assert txn.transaction_type == TransactionType.DEBIT
        assert txn.is_debit is True
        assert txn.is_credit is False

    def test_transaction_auto_type_inference_credit(self) -> None:
        """Test automatic transaction type inference for credit."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("500.00"),
            description="Salary",
        )
        assert txn.transaction_type == TransactionType.CREDIT
        assert txn.is_credit is True
        assert txn.is_debit is False

    def test_transaction_abs_amount(self) -> None:
        """Test absolute amount property."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-75.50"),
            description="Test",
        )
        assert txn.abs_amount == Decimal("75.50")

    def test_transaction_amount_conversion(self) -> None:
        """Test amount is converted to Decimal."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=50.00,  # Float instead of Decimal
            description="Test",
        )
        assert isinstance(txn.amount, Decimal)
        assert txn.amount == Decimal("50.0")

    def test_transaction_balance_conversion(self) -> None:
        """Test balance is converted to Decimal."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Test",
            balance=1000.00,  # Float
        )
        assert isinstance(txn.balance, Decimal)

    def test_transaction_description_stripped(self) -> None:
        """Test description is stripped of whitespace."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="  Netflix Payment  ",
        )
        assert txn.description == "Netflix Payment"

    def test_transaction_with_all_fields(self) -> None:
        """Test transaction with all optional fields."""
        txn = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-99.99"),
            description="Annual Subscription",
            transaction_type=TransactionType.DEBIT,
            balance=Decimal("1500.00"),
            reference="REF123456",
            category="Entertainment",
            raw_data={"row": ["2024-01-15", "-99.99", "Annual Subscription"]},
        )
        assert txn.balance == Decimal("1500.00")
        assert txn.reference == "REF123456"
        assert txn.category == "Entertainment"
        assert "row" in txn.raw_data


# =============================================================================
# StatementData Tests
# =============================================================================


class TestStatementData:
    """Tests for StatementData dataclass."""

    def test_statement_data_empty(self) -> None:
        """Test empty statement data."""
        stmt = StatementData()
        assert stmt.transaction_count == 0
        assert stmt.total_debits == 0
        assert stmt.total_credits == 0
        assert stmt.net_change == 0

    def test_statement_data_with_transactions(self) -> None:
        """Test statement data with transactions."""
        txns = [
            Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Debit 1"),
            Transaction(date=date(2024, 1, 2), amount=Decimal("-30.00"), description="Debit 2"),
            Transaction(date=date(2024, 1, 3), amount=Decimal("100.00"), description="Credit 1"),
        ]
        stmt = StatementData(transactions=txns)

        assert stmt.transaction_count == 3
        assert stmt.total_debits == Decimal("80.00")
        assert stmt.total_credits == Decimal("100.00")
        assert stmt.net_change == Decimal("20.00")

    def test_statement_data_filter_debits(self) -> None:
        """Test filtering debit transactions."""
        txns = [
            Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Debit"),
            Transaction(date=date(2024, 1, 2), amount=Decimal("100.00"), description="Credit"),
        ]
        stmt = StatementData(transactions=txns)

        debits = stmt.filter_debits()
        assert len(debits) == 1
        assert debits[0].description == "Debit"

    def test_statement_data_filter_credits(self) -> None:
        """Test filtering credit transactions."""
        txns = [
            Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Debit"),
            Transaction(date=date(2024, 1, 2), amount=Decimal("100.00"), description="Credit"),
        ]
        stmt = StatementData(transactions=txns)

        credits = stmt.filter_credits()
        assert len(credits) == 1
        assert credits[0].description == "Credit"

    def test_statement_data_filter_by_amount(self) -> None:
        """Test filtering by amount range."""
        txns = [
            Transaction(date=date(2024, 1, 1), amount=Decimal("-10.00"), description="Small"),
            Transaction(date=date(2024, 1, 2), amount=Decimal("-50.00"), description="Medium"),
            Transaction(date=date(2024, 1, 3), amount=Decimal("-100.00"), description="Large"),
        ]
        stmt = StatementData(transactions=txns)

        filtered = stmt.filter_by_amount(
            min_amount=Decimal("20.00"),
            max_amount=Decimal("80.00"),
        )
        assert len(filtered) == 1
        assert filtered[0].description == "Medium"

    def test_statement_data_filter_by_date(self) -> None:
        """Test filtering by date range."""
        txns = [
            Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Jan 1"),
            Transaction(date=date(2024, 1, 15), amount=Decimal("-50.00"), description="Jan 15"),
            Transaction(date=date(2024, 1, 31), amount=Decimal("-50.00"), description="Jan 31"),
        ]
        stmt = StatementData(transactions=txns)

        filtered = stmt.filter_by_date(
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 20),
        )
        assert len(filtered) == 1
        assert filtered[0].description == "Jan 15"

    def test_statement_data_search_description(self) -> None:
        """Test searching by description keyword."""
        txns = [
            Transaction(
                date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix Monthly"
            ),
            Transaction(
                date=date(2024, 1, 2), amount=Decimal("-9.99"), description="Spotify Premium"
            ),
            Transaction(
                date=date(2024, 1, 3), amount=Decimal("-50.00"), description="Netflix Annual"
            ),
        ]
        stmt = StatementData(transactions=txns)

        results = stmt.search_description("netflix")
        assert len(results) == 2
        assert all("netflix" in r.description.lower() for r in results)


# =============================================================================
# Format Detection Tests
# =============================================================================


class TestFormatDetection:
    """Tests for statement format detection."""

    def test_detect_format_by_extension_pdf(self, tmp_path) -> None:
        """Test PDF format detection by extension."""
        pdf_file = tmp_path / "statement.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        assert detect_format(pdf_file) == StatementFormat.PDF

    def test_detect_format_by_extension_csv(self, tmp_path) -> None:
        """Test CSV format detection by extension."""
        csv_file = tmp_path / "statement.csv"
        csv_file.write_text("date,amount,description\n2024-01-01,-50.00,Test")

        assert detect_format(csv_file) == StatementFormat.CSV

    def test_detect_format_by_extension_ofx(self, tmp_path) -> None:
        """Test OFX format detection by extension."""
        ofx_file = tmp_path / "statement.ofx"
        ofx_file.write_text("OFXHEADER:100")

        assert detect_format(ofx_file) == StatementFormat.OFX

    def test_detect_format_by_extension_qfx(self, tmp_path) -> None:
        """Test QFX format detection by extension (OFX variant)."""
        qfx_file = tmp_path / "statement.qfx"
        qfx_file.write_text("<OFX>")

        assert detect_format(qfx_file) == StatementFormat.OFX

    def test_detect_format_by_extension_qif(self, tmp_path) -> None:
        """Test QIF format detection by extension."""
        qif_file = tmp_path / "statement.qif"
        qif_file.write_text("!Type:Bank")

        assert detect_format(qif_file) == StatementFormat.QIF

    def test_detect_format_by_content_pdf(self, tmp_path) -> None:
        """Test PDF format detection by content."""
        pdf_file = tmp_path / "unknown"
        pdf_file.write_bytes(b"%PDF-1.7 some content")

        assert detect_format(pdf_file) == StatementFormat.PDF

    def test_detect_format_by_content_ofx(self, tmp_path) -> None:
        """Test OFX format detection by content."""
        ofx_file = tmp_path / "unknown"
        ofx_file.write_text("OFXHEADER:100\n<OFX>")

        assert detect_format(ofx_file) == StatementFormat.OFX

    def test_detect_format_by_content_qif(self, tmp_path) -> None:
        """Test QIF format detection by content."""
        qif_file = tmp_path / "unknown"
        qif_file.write_text("!Type:CCard\nD01/15/2024")

        assert detect_format(qif_file) == StatementFormat.QIF

    def test_detect_format_by_content_csv(self, tmp_path) -> None:
        """Test CSV format detection by content."""
        csv_file = tmp_path / "unknown"
        csv_file.write_text("date,amount,description\n2024-01-01,-50.00,Test")

        assert detect_format(csv_file) == StatementFormat.CSV

    def test_detect_format_unknown(self, tmp_path) -> None:
        """Test unknown format detection."""
        unknown_file = tmp_path / "unknown.xyz"
        unknown_file.write_bytes(b"random binary data")

        assert detect_format(unknown_file) == StatementFormat.UNKNOWN


# =============================================================================
# Parser Error Tests
# =============================================================================


class TestParserErrors:
    """Tests for parser error classes."""

    def test_parser_error_base(self) -> None:
        """Test base ParserError."""
        with pytest.raises(ParserError):
            raise ParserError("General error")

    def test_unsupported_format_error(self) -> None:
        """Test UnsupportedFormatError."""
        with pytest.raises(UnsupportedFormatError):
            raise UnsupportedFormatError("Format not supported")

    def test_parse_error(self) -> None:
        """Test ParseError."""
        with pytest.raises(ParseError):
            raise ParseError("Parsing failed")

    def test_empty_statement_error(self) -> None:
        """Test EmptyStatementError."""
        with pytest.raises(EmptyStatementError):
            raise EmptyStatementError("No transactions")

    def test_error_inheritance(self) -> None:
        """Test error class inheritance."""
        assert issubclass(UnsupportedFormatError, ParserError)
        assert issubclass(ParseError, ParserError)
        assert issubclass(EmptyStatementError, ParserError)


# =============================================================================
# StatementAIService Tests
# =============================================================================


class TestStatementAIService:
    """Tests for StatementAIService."""

    def test_service_initialization_default(self) -> None:
        """Test service initialization with default client."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()
            assert service.client is not None

    def test_service_initialization_custom_client(self) -> None:
        """Test service initialization with custom client."""
        mock_client = MagicMock()
        service = StatementAIService(anthropic_client=mock_client)
        assert service.client == mock_client

    def test_normalize_merchant_name_basic(self) -> None:
        """Test basic merchant name normalization."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._normalize_merchant_name("NETFLIX.COM")
            assert result == "netflix.com"

    def test_normalize_merchant_name_with_prefixes(self) -> None:
        """Test merchant name normalization with payment prefixes."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._normalize_merchant_name("CARD PAYMENT TO SPOTIFY")
            assert "spotify" in result.lower()

    def test_normalize_merchant_name_with_reference(self) -> None:
        """Test merchant name normalization with reference numbers."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._normalize_merchant_name("Netflix ref: 12345678")
            assert "12345678" not in result

    def test_normalize_merchant_name_empty(self) -> None:
        """Test empty merchant name normalization."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._normalize_merchant_name("")
            assert result == ""

    def test_normalize_merchant_name_truncation(self) -> None:
        """Test long merchant name truncation."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            long_name = "A" * 100
            result = service._normalize_merchant_name(long_name)
            assert len(result) <= 50

    def test_group_transactions(self) -> None:
        """Test transaction grouping by normalized name."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(
                    date=date(2024, 1, 15), amount=Decimal("-15.99"), description="Netflix"
                ),
                Transaction(date=date(2024, 1, 5), amount=Decimal("-9.99"), description="Spotify"),
            ]

            groups = service._group_transactions(txns)
            assert len(groups) == 2
            assert "netflix" in groups
            assert "spotify" in groups
            assert len(groups["netflix"]) == 2

    def test_group_transactions_skip_credits(self) -> None:
        """Test that credits are skipped during grouping."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(
                    date=date(2024, 1, 5), amount=Decimal("100.00"), description="Refund Netflix"
                ),
            ]

            groups = service._group_transactions(txns)
            # Only the debit should be included
            assert len(groups) == 1

    def test_detect_frequency_weekly(self) -> None:
        """Test weekly frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(7, [7, 7, 7])
            assert result == FrequencyType.WEEKLY

    def test_detect_frequency_biweekly(self) -> None:
        """Test biweekly frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(14, [14, 14])
            assert result == FrequencyType.BIWEEKLY

    def test_detect_frequency_monthly(self) -> None:
        """Test monthly frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(30, [30, 31, 29])
            assert result == FrequencyType.MONTHLY

    def test_detect_frequency_quarterly(self) -> None:
        """Test quarterly frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(90, [90, 91])
            assert result == FrequencyType.QUARTERLY

    def test_detect_frequency_yearly(self) -> None:
        """Test yearly frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(365, [365])
            assert result == FrequencyType.YEARLY

    def test_detect_frequency_irregular(self) -> None:
        """Test irregular frequency detection."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            result = service._detect_frequency(45, [45, 50, 40])
            assert result == FrequencyType.IRREGULAR

    def test_classify_payment_type_subscription(self) -> None:
        """Test subscription payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix")
            ]
            result = service._classify_payment_type("netflix", txns)
            assert result == PaymentTypeClassification.SUBSCRIPTION

    def test_classify_payment_type_housing(self) -> None:
        """Test housing payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-1500.00"), description="Rent Payment"
                )
            ]
            result = service._classify_payment_type("rent payment", txns)
            assert result == PaymentTypeClassification.HOUSING

    def test_classify_payment_type_utility(self) -> None:
        """Test utility payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-100.00"), description="British Gas"
                )
            ]
            result = service._classify_payment_type("british gas", txns)
            assert result == PaymentTypeClassification.UTILITY

    def test_classify_payment_type_insurance(self) -> None:
        """Test insurance payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Car Insurance"
                )
            ]
            result = service._classify_payment_type("car insurance", txns)
            assert result == PaymentTypeClassification.INSURANCE

    def test_classify_payment_type_debt(self) -> None:
        """Test debt payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-200.00"), description="Loan Repayment"
                )
            ]
            result = service._classify_payment_type("loan repayment", txns)
            assert result == PaymentTypeClassification.DEBT

    def test_classify_payment_type_savings(self) -> None:
        """Test savings payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-500.00"), description="ISA Transfer"
                )
            ]
            result = service._classify_payment_type("isa transfer", txns)
            assert result == PaymentTypeClassification.SAVINGS

    def test_classify_payment_type_unknown(self) -> None:
        """Test unknown payment type classification."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(
                    date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Random Store"
                )
            ]
            result = service._classify_payment_type("random store", txns)
            assert result == PaymentTypeClassification.UNKNOWN

    def test_calculate_confidence_high(self) -> None:
        """Test high confidence calculation."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            confidence = service._calculate_confidence(
                transaction_count=6,
                amount_variance=0.0,
                days_between=[30, 30, 30, 30, 30],
                frequency=FrequencyType.MONTHLY,
            )
            assert confidence >= 0.8

    def test_calculate_confidence_low(self) -> None:
        """Test low confidence calculation."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            confidence = service._calculate_confidence(
                transaction_count=2,
                amount_variance=0.5,
                days_between=[45, 60],
                frequency=FrequencyType.IRREGULAR,
            )
            assert confidence < 0.6

    def test_analyze_group_minimum_transactions(self) -> None:
        """Test that groups with too few transactions are rejected."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Test")
            ]
            result = service._analyze_group("test", txns)
            assert result is None

    def test_analyze_group_valid_pattern(self) -> None:
        """Test pattern detection from valid transaction group."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(date=date(2024, 2, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(date=date(2024, 3, 1), amount=Decimal("-15.99"), description="Netflix"),
            ]

            result = service._analyze_group("netflix", txns)
            assert result is not None
            assert result.normalized_name == "netflix"
            assert result.amount == Decimal("15.99")
            assert result.transaction_count == 3

    @pytest.mark.asyncio
    async def test_analyze_statement_empty(self) -> None:
        """Test analyzing empty statement."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            stmt = StatementData()
            patterns = await service.analyze_statement(stmt)
            assert patterns == []

    @pytest.mark.asyncio
    async def test_analyze_statement_no_patterns(self) -> None:
        """Test analyzing statement with no recurring patterns."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-50.00"), description="Store A"),
                Transaction(date=date(2024, 1, 5), amount=Decimal("-30.00"), description="Store B"),
                Transaction(
                    date=date(2024, 1, 10), amount=Decimal("-25.00"), description="Store C"
                ),
            ]
            stmt = StatementData(transactions=txns)

            patterns = await service.analyze_statement(stmt, use_ai=False)
            assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_analyze_statement_with_patterns(self) -> None:
        """Test analyzing statement with recurring patterns."""
        with patch("src.services.statement_ai_service.Anthropic"):
            service = StatementAIService()

            txns = [
                Transaction(date=date(2024, 1, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(date=date(2024, 2, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(date=date(2024, 3, 1), amount=Decimal("-15.99"), description="Netflix"),
                Transaction(date=date(2024, 1, 5), amount=Decimal("-9.99"), description="Spotify"),
                Transaction(date=date(2024, 2, 5), amount=Decimal("-9.99"), description="Spotify"),
            ]
            stmt = StatementData(transactions=txns)

            patterns = await service.analyze_statement(stmt, use_ai=False)
            assert len(patterns) == 2
            # Should be sorted by confidence
            assert patterns[0].confidence >= patterns[1].confidence


class TestDetectedPattern:
    """Tests for DetectedPattern dataclass."""

    def test_detected_pattern_to_dict(self) -> None:
        """Test DetectedPattern to_dict conversion."""
        pattern = DetectedPattern(
            merchant_name="Netflix",
            normalized_name="netflix",
            amount=Decimal("15.99"),
            amount_variance=0.0,
            frequency=FrequencyType.MONTHLY,
            payment_type=PaymentTypeClassification.SUBSCRIPTION,
            confidence=0.95,
            transaction_count=12,
            first_seen=date(2024, 1, 1),
            last_seen=date(2024, 12, 1),
            sample_descriptions=["Netflix Monthly", "Netflix Sub", "Netflix Premium"],
            avg_days_between=30.5,
        )

        result = pattern.to_dict()

        assert result["merchant_name"] == "Netflix"
        assert result["normalized_name"] == "netflix"
        assert result["amount"] == 15.99
        assert result["frequency"] == "monthly"
        assert result["payment_type"] == "subscription"
        assert result["confidence"] == 0.95
        assert result["transaction_count"] == 12
        assert result["first_seen"] == "2024-01-01"
        assert result["last_seen"] == "2024-12-01"
        assert len(result["sample_descriptions"]) <= 3


class TestPaymentTypeKeywords:
    """Tests for payment type keyword mappings."""

    def test_subscription_keywords_exist(self) -> None:
        """Test subscription keywords exist."""
        keywords = PAYMENT_TYPE_KEYWORDS[PaymentTypeClassification.SUBSCRIPTION]
        assert "netflix" in keywords
        assert "spotify" in keywords
        assert "claude" in keywords

    def test_housing_keywords_exist(self) -> None:
        """Test housing keywords exist."""
        keywords = PAYMENT_TYPE_KEYWORDS[PaymentTypeClassification.HOUSING]
        assert "rent" in keywords
        assert "mortgage" in keywords

    def test_utility_keywords_exist(self) -> None:
        """Test utility keywords exist."""
        keywords = PAYMENT_TYPE_KEYWORDS[PaymentTypeClassification.UTILITY]
        assert "electric" in keywords
        assert "internet" in keywords

    def test_all_payment_types_have_keywords(self) -> None:
        """Test all payment types have keyword mappings."""
        for payment_type in PaymentTypeClassification:
            if payment_type != PaymentTypeClassification.UNKNOWN:
                assert payment_type in PAYMENT_TYPE_KEYWORDS
                assert len(PAYMENT_TYPE_KEYWORDS[payment_type]) > 0


# =============================================================================
# DuplicateDetector Tests
# =============================================================================


class TestDuplicateDetector:
    """Tests for DuplicateDetector service."""

    def test_detector_initialization(self) -> None:
        """Test detector initialization."""
        detector = DuplicateDetector()
        assert detector is not None

    def test_normalize_name_basic(self) -> None:
        """Test basic name normalization."""
        detector = DuplicateDetector()

        result = detector._normalize_name("Netflix Ltd")
        assert result == "netflix"

    def test_normalize_name_with_suffixes(self) -> None:
        """Test name normalization with company suffixes."""
        detector = DuplicateDetector()

        assert detector._normalize_name("Spotify Inc.") == "spotify"
        assert detector._normalize_name("Amazon LLC") == "amazon"
        assert detector._normalize_name("BBC PLC") == "bbc"

    def test_normalize_name_special_chars(self) -> None:
        """Test name normalization with special characters."""
        detector = DuplicateDetector()

        result = detector._normalize_name("Netflix!@#$%")
        assert result == "netflix"

    def test_normalize_name_empty(self) -> None:
        """Test empty name normalization."""
        detector = DuplicateDetector()

        assert detector._normalize_name("") == ""
        assert detector._normalize_name("   ") == ""

    def test_calculate_name_similarity_exact(self) -> None:
        """Test exact name match similarity."""
        detector = DuplicateDetector()

        score = detector._calculate_name_similarity("netflix", "netflix")
        assert score == 1.0

    def test_calculate_name_similarity_substring(self) -> None:
        """Test substring match similarity."""
        detector = DuplicateDetector()

        score = detector._calculate_name_similarity("netflix", "netflix premium")
        assert score >= 0.9

    def test_calculate_name_similarity_partial(self) -> None:
        """Test partial match similarity."""
        detector = DuplicateDetector()

        score = detector._calculate_name_similarity("netflix", "netflx")  # Typo
        assert 0.5 < score < 1.0

    def test_calculate_name_similarity_different(self) -> None:
        """Test different names similarity."""
        detector = DuplicateDetector()

        score = detector._calculate_name_similarity("netflix", "spotify")
        assert score < 0.5

    def test_calculate_amount_similarity_exact(self) -> None:
        """Test exact amount match."""
        detector = DuplicateDetector()

        score = detector._calculate_amount_similarity(Decimal("15.99"), Decimal("15.99"))
        assert score == 1.0

    def test_calculate_amount_similarity_close(self) -> None:
        """Test close amount match."""
        detector = DuplicateDetector()

        score = detector._calculate_amount_similarity(Decimal("15.99"), Decimal("16.00"))
        assert score > 0.9

    def test_calculate_amount_similarity_different(self) -> None:
        """Test different amounts."""
        detector = DuplicateDetector()

        score = detector._calculate_amount_similarity(Decimal("15.99"), Decimal("100.00"))
        assert score < 0.5

    def test_calculate_amount_similarity_zero(self) -> None:
        """Test zero amount handling."""
        detector = DuplicateDetector()

        score = detector._calculate_amount_similarity(Decimal("0"), Decimal("15.99"))
        assert score == 0.0

    def test_calculate_frequency_similarity_same(self) -> None:
        """Test same frequency match."""
        detector = DuplicateDetector()

        score = detector._calculate_frequency_similarity("monthly", "monthly")
        assert score == 1.0

    def test_calculate_frequency_similarity_equivalent(self) -> None:
        """Test equivalent frequency match."""
        detector = DuplicateDetector()

        score = detector._calculate_frequency_similarity("yearly", "annually")
        assert score == 1.0

    def test_calculate_frequency_similarity_irregular(self) -> None:
        """Test irregular frequency match."""
        detector = DuplicateDetector()

        score = detector._calculate_frequency_similarity("irregular", "monthly")
        assert score < 0.5

    def test_find_duplicates_no_matches(self) -> None:
        """Test finding duplicates with no matches."""
        detector = DuplicateDetector()

        patterns = [
            DetectedPattern(
                merchant_name="Netflix",
                normalized_name="netflix",
                amount=Decimal("15.99"),
                amount_variance=0.0,
                frequency=FrequencyType.MONTHLY,
                payment_type=PaymentTypeClassification.SUBSCRIPTION,
                confidence=0.9,
                transaction_count=3,
                first_seen=date(2024, 1, 1),
                last_seen=date(2024, 3, 1),
            )
        ]

        # Create a mock subscription with different name
        mock_sub = MagicMock(spec=Subscription)
        mock_sub.id = "sub-123"
        mock_sub.name = "Completely Different"
        mock_sub.amount = Decimal("99.99")
        mock_sub.frequency = Frequency.YEARLY

        matches = detector.find_duplicates(patterns, [mock_sub])
        assert len(matches) == 0

    def test_find_duplicates_with_match(self) -> None:
        """Test finding duplicates with a match."""
        detector = DuplicateDetector()

        patterns = [
            DetectedPattern(
                merchant_name="Netflix",
                normalized_name="netflix",
                amount=Decimal("15.99"),
                amount_variance=0.0,
                frequency=FrequencyType.MONTHLY,
                payment_type=PaymentTypeClassification.SUBSCRIPTION,
                confidence=0.9,
                transaction_count=3,
                first_seen=date(2024, 1, 1),
                last_seen=date(2024, 3, 1),
            )
        ]

        # Create a mock subscription with matching name
        mock_sub = MagicMock(spec=Subscription)
        mock_sub.id = "sub-123"
        mock_sub.name = "Netflix"
        mock_sub.amount = Decimal("15.99")
        mock_sub.frequency = Frequency.MONTHLY

        matches = detector.find_duplicates(patterns, [mock_sub])
        assert len(matches) == 1
        assert matches[0].similarity_score > 0.8

    def test_find_best_match(self) -> None:
        """Test finding best match among multiple."""
        detector = DuplicateDetector()

        pattern = DetectedPattern(
            merchant_name="Spotify Premium",
            normalized_name="spotify premium",
            amount=Decimal("9.99"),
            amount_variance=0.0,
            frequency=FrequencyType.MONTHLY,
            payment_type=PaymentTypeClassification.SUBSCRIPTION,
            confidence=0.9,
            transaction_count=3,
            first_seen=date(2024, 1, 1),
            last_seen=date(2024, 3, 1),
        )

        # Create mock subscriptions - one is clearly better match
        mock_sub1 = MagicMock(spec=Subscription)
        mock_sub1.id = "sub-1"
        mock_sub1.name = "Netflix"  # Different service
        mock_sub1.amount = Decimal("15.99")  # Different amount
        mock_sub1.frequency = Frequency.MONTHLY

        mock_sub2 = MagicMock(spec=Subscription)
        mock_sub2.id = "sub-2"
        mock_sub2.name = "Spotify Premium"  # Exact match
        mock_sub2.amount = Decimal("9.99")  # Same amount
        mock_sub2.frequency = Frequency.MONTHLY

        best_match = detector.find_best_match(pattern, [mock_sub1, mock_sub2])
        assert best_match is not None
        assert best_match.existing_subscription.name == "Spotify Premium"


class TestDuplicateMatchResult:
    """Tests for DuplicateMatch result dataclass."""

    def test_duplicate_match_to_dict(self) -> None:
        """Test DuplicateMatch to_dict conversion."""
        pattern = DetectedPattern(
            merchant_name="Netflix",
            normalized_name="netflix",
            amount=Decimal("15.99"),
            amount_variance=0.0,
            frequency=FrequencyType.MONTHLY,
            payment_type=PaymentTypeClassification.SUBSCRIPTION,
            confidence=0.9,
            transaction_count=3,
            first_seen=date(2024, 1, 1),
            last_seen=date(2024, 3, 1),
        )

        mock_sub = MagicMock(spec=Subscription)
        mock_sub.id = "sub-123"
        mock_sub.name = "Netflix"
        mock_sub.amount = Decimal("15.99")

        match = DuplicateMatchResult(
            detected_pattern=pattern,
            existing_subscription=mock_sub,
            similarity_score=0.95,
            match_reasons=["Name match: 100%", "Amount match: 100%"],
        )

        result = match.to_dict()

        assert result["detected_name"] == "netflix"
        assert result["detected_amount"] == 15.99
        assert result["existing_id"] == "sub-123"
        assert result["existing_name"] == "Netflix"
        assert result["similarity_score"] == 0.95
        assert len(result["match_reasons"]) == 2


# =============================================================================
# Statement Import Schema Tests
# =============================================================================


class TestImportJobSchemas:
    """Tests for ImportJob schemas."""

    def test_import_job_create(self) -> None:
        """Test ImportJobCreate schema."""
        job = ImportJobCreate(
            filename="statement.pdf",
            file_type="pdf",
            file_size=1024,
            bank_name="Monzo",
            currency="GBP",
        )
        assert job.filename == "statement.pdf"
        assert job.file_type == "pdf"
        assert job.currency == "GBP"

    def test_import_job_create_minimal(self) -> None:
        """Test ImportJobCreate with minimal fields."""
        job = ImportJobCreate(
            filename="statement.csv",
            file_type="csv",
        )
        assert job.filename == "statement.csv"
        assert job.currency == "GBP"  # Default

    def test_import_job_response(self) -> None:
        """Test ImportJobResponse schema."""
        from datetime import datetime

        job = ImportJobResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            filename="statement.pdf",
            file_type="pdf",
            file_size=1024,
            bank_name="Monzo",
            currency="GBP",
            status="processing",
            total_transactions=50,
            detected_count=5,
            imported_count=0,
            skipped_count=0,
            duplicate_count=0,
            created_at=datetime.now(),
        )
        assert job.status == "processing"
        assert job.detected_count == 5


class TestDetectedSubscriptionSchemas:
    """Tests for DetectedSubscription schemas."""

    def test_detected_subscription_update(self) -> None:
        """Test DetectedSubscriptionUpdate schema."""
        update = DetectedSubscriptionUpdate(
            is_selected=True,
            name="Netflix Premium",
            amount=Decimal("17.99"),
        )
        assert update.is_selected is True
        assert update.name == "Netflix Premium"
        assert update.amount == Decimal("17.99")

    def test_detected_subscription_update_partial(self) -> None:
        """Test partial DetectedSubscriptionUpdate."""
        update = DetectedSubscriptionUpdate(is_selected=False)
        assert update.is_selected is False
        assert update.name is None
        assert update.amount is None

    def test_bulk_update_request(self) -> None:
        """Test BulkUpdateDetectedRequest schema."""
        request = BulkUpdateDetectedRequest(
            subscription_ids=["id1", "id2", "id3"],
            is_selected=True,
        )
        assert len(request.subscription_ids) == 3
        assert request.is_selected is True


class TestConfirmImportSchemas:
    """Tests for ConfirmImport schemas."""

    def test_confirm_import_request(self) -> None:
        """Test ConfirmImportRequest schema."""
        request = ConfirmImportRequest(
            subscription_ids=["id1", "id2"],
            card_id="card-123",
            category_id="cat-456",
        )
        assert len(request.subscription_ids) == 2
        assert request.card_id == "card-123"
        assert request.category_id == "cat-456"

    def test_confirm_import_request_empty_ids(self) -> None:
        """Test ConfirmImportRequest with empty ids (import all selected)."""
        request = ConfirmImportRequest()
        assert request.subscription_ids == []
        assert request.card_id is None


class TestDuplicateSchemas:
    """Tests for Duplicate schemas."""

    def test_duplicate_check_request(self) -> None:
        """Test DuplicateCheckRequest schema."""
        request = DuplicateCheckRequest(
            job_id="job-123",
            detected_subscription_id="det-456",
        )
        assert request.job_id == "job-123"

    def test_duplicate_match(self) -> None:
        """Test DuplicateMatch schema."""
        match = DuplicateMatch(
            detected_id="det-123",
            detected_name="Netflix",
            existing_id="sub-456",
            existing_name="Netflix Premium",
            similarity=0.92,
            match_reasons=["Name match: 90%", "Amount match: 100%"],
        )
        assert match.similarity == 0.92
        assert len(match.match_reasons) == 2

    def test_resolve_duplicate_request_skip(self) -> None:
        """Test ResolveDuplicateRequest with skip action."""
        request = ResolveDuplicateRequest(
            detected_id="det-123",
            action="skip",
        )
        assert request.action == "skip"
        assert request.merge_with_id is None

    def test_resolve_duplicate_request_merge(self) -> None:
        """Test ResolveDuplicateRequest with merge action."""
        request = ResolveDuplicateRequest(
            detected_id="det-123",
            action="merge",
            merge_with_id="sub-456",
        )
        assert request.action == "merge"
        assert request.merge_with_id == "sub-456"

    def test_resolve_duplicate_request_invalid_action(self) -> None:
        """Test ResolveDuplicateRequest with invalid action."""
        with pytest.raises(ValueError):
            ResolveDuplicateRequest(
                detected_id="det-123",
                action="invalid",
            )


class TestImportPreviewSummary:
    """Tests for ImportPreviewSummary schema."""

    def test_import_preview_summary(self) -> None:
        """Test ImportPreviewSummary schema."""
        summary = ImportPreviewSummary(
            total_detected=10,
            selected_count=8,
            duplicate_count=2,
            high_confidence_count=6,
            low_confidence_count=2,
            total_monthly_amount=Decimal("150.00"),
            currencies=["GBP", "USD"],
            payment_types={"subscription": 5, "utility": 3},
            frequencies={"monthly": 7, "yearly": 1},
        )
        assert summary.total_detected == 10
        assert summary.selected_count == 8
        assert len(summary.currencies) == 2
        assert summary.payment_types["subscription"] == 5


class TestStatementUploadResponse:
    """Tests for StatementUploadResponse schema."""

    def test_statement_upload_response(self) -> None:
        """Test StatementUploadResponse schema."""
        response = StatementUploadResponse(
            job_id="123e4567-e89b-12d3-a456-426614174000",
            filename="statement.pdf",
            file_type="pdf",
            status="pending",
            message="Statement uploaded successfully",
        )
        assert response.job_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.status == "pending"
        assert "successfully" in response.message


# =============================================================================
# Frequency and Payment Type Enum Tests
# =============================================================================


class TestFrequencyType:
    """Tests for FrequencyType enum."""

    def test_frequency_values(self) -> None:
        """Test all frequency values."""
        assert FrequencyType.WEEKLY.value == "weekly"
        assert FrequencyType.BIWEEKLY.value == "biweekly"
        assert FrequencyType.MONTHLY.value == "monthly"
        assert FrequencyType.QUARTERLY.value == "quarterly"
        assert FrequencyType.YEARLY.value == "yearly"
        assert FrequencyType.IRREGULAR.value == "irregular"


class TestPaymentTypeClassification:
    """Tests for PaymentTypeClassification enum."""

    def test_payment_type_values(self) -> None:
        """Test all payment type values."""
        assert PaymentTypeClassification.SUBSCRIPTION.value == "subscription"
        assert PaymentTypeClassification.HOUSING.value == "housing"
        assert PaymentTypeClassification.UTILITY.value == "utility"
        assert PaymentTypeClassification.INSURANCE.value == "insurance"
        assert PaymentTypeClassification.PROFESSIONAL.value == "professional"
        assert PaymentTypeClassification.DEBT.value == "debt"
        assert PaymentTypeClassification.SAVINGS.value == "savings"
        assert PaymentTypeClassification.TRANSFER.value == "transfer"
        assert PaymentTypeClassification.UNKNOWN.value == "unknown"


# =============================================================================
# CSV Parser Tests (Synchronous)
# =============================================================================


class TestCSVParser:
    """Tests for CSV statement parser."""

    def test_can_parse_csv_by_extension(self, tmp_path) -> None:
        """Test CSV detection by file extension."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        csv_file = tmp_path / "statement.csv"
        csv_file.write_text("date,amount,description\n2024-01-01,-50.00,Test")

        assert parser.can_parse(csv_file) is True

    def test_can_parse_non_csv(self, tmp_path) -> None:
        """Test non-CSV file detection."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        pdf_file = tmp_path / "statement.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        assert parser.can_parse(pdf_file) is False

    def test_parse_simple_csv(self, tmp_path) -> None:
        """Test parsing simple CSV statement."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        csv_content = """date,amount,description
2024-01-01,-50.00,Netflix
2024-01-05,-30.00,Spotify
2024-01-10,100.00,Refund"""

        csv_file = tmp_path / "statement.csv"
        csv_file.write_text(csv_content)

        result = parser.parse(csv_file)

        assert len(result.transactions) == 3
        assert result.format == StatementFormat.CSV

    def test_parse_csv_with_debit_credit_columns(self, tmp_path) -> None:
        """Test parsing CSV with separate debit/credit columns."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        csv_content = """date,description,debit,credit,balance
2024-01-01,Netflix,50.00,,950.00
2024-01-05,Salary,,1000.00,1950.00
2024-01-10,Rent,500.00,,1450.00"""

        csv_file = tmp_path / "statement.csv"
        csv_file.write_text(csv_content)

        result = parser.parse(csv_file)

        assert len(result.transactions) == 3

        # Check types are correct
        netflix = next(t for t in result.transactions if "Netflix" in t.description)
        assert netflix.is_debit

        salary = next(t for t in result.transactions if "Salary" in t.description)
        assert salary.is_credit

    def test_parse_csv_empty_file(self, tmp_path) -> None:
        """Test parsing empty CSV file."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises(EmptyStatementError):
            parser.parse(csv_file)

    def test_parse_csv_header_only(self, tmp_path) -> None:
        """Test parsing CSV with header only."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("date,amount,description\n")

        with pytest.raises(EmptyStatementError):
            parser.parse(csv_file)


class TestCSVParserAmountParsing:
    """Tests for CSV parser amount parsing."""

    def test_parse_amount_us_format(self) -> None:
        """Test US/UK amount format (1,234.56)."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        assert parser._parse_amount("1,234.56") == Decimal("1234.56")
        assert parser._parse_amount("1,000,000.00") == Decimal("1000000.00")

    def test_parse_amount_eu_format(self) -> None:
        """Test EU amount format (1.234,56)."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        assert parser._parse_amount("1.234,56") == Decimal("1234.56")

    def test_parse_amount_negative(self) -> None:
        """Test negative amount formats."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        assert parser._parse_amount("-50.00") == Decimal("-50.00")
        assert parser._parse_amount("(50.00)") == Decimal("-50.00")

    def test_parse_amount_with_currency(self) -> None:
        """Test amount with currency symbols."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        assert parser._parse_amount("£50.00") == Decimal("50.00")
        assert parser._parse_amount("$100.00") == Decimal("100.00")
        assert parser._parse_amount("€75.50") == Decimal("75.50")

    def test_parse_amount_empty(self) -> None:
        """Test empty amount string."""
        from src.services.parsers.csv_parser import CSVStatementParser

        parser = CSVStatementParser()

        assert parser._parse_amount("") is None
        assert parser._parse_amount("   ") is None
