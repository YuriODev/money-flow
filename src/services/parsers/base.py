"""Base classes and dataclasses for bank statement parsing.

This module provides the foundation for all statement parsers:
- StatementParser: Abstract base class for parsers
- StatementData: Container for parsed statement data
- Transaction: Individual transaction record
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Type of transaction."""

    DEBIT = "debit"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class StatementFormat(str, Enum):
    """Supported statement formats."""

    PDF = "pdf"
    CSV = "csv"
    OFX = "ofx"
    QIF = "qif"
    UNKNOWN = "unknown"


class ParserError(Exception):
    """Base exception for parser errors."""

    pass


class UnsupportedFormatError(ParserError):
    """Raised when the file format is not supported."""

    pass


class ParseError(ParserError):
    """Raised when parsing fails."""

    pass


class EmptyStatementError(ParserError):
    """Raised when the statement contains no transactions."""

    pass


@dataclass
class Transaction:
    """Individual transaction from a bank statement.

    Attributes:
        date: Transaction date
        amount: Transaction amount (positive for credits, negative for debits)
        description: Transaction description/memo
        transaction_type: Debit or credit
        balance: Running balance after transaction (if available)
        reference: Bank reference number (if available)
        category: Transaction category (if available)
        raw_data: Original raw data from the statement
    """

    date: date
    amount: Decimal
    description: str
    transaction_type: TransactionType = TransactionType.UNKNOWN
    balance: Decimal | None = None
    reference: str | None = None
    category: str | None = None
    raw_data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize transaction data."""
        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

        # Ensure balance is Decimal if present
        if self.balance is not None and not isinstance(self.balance, Decimal):
            self.balance = Decimal(str(self.balance))

        # Normalize description
        self.description = self.description.strip()

        # Infer transaction type from amount if unknown
        if self.transaction_type == TransactionType.UNKNOWN:
            if self.amount < 0:
                self.transaction_type = TransactionType.DEBIT
            elif self.amount > 0:
                self.transaction_type = TransactionType.CREDIT

    @property
    def abs_amount(self) -> Decimal:
        """Return absolute value of amount."""
        return abs(self.amount)

    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit."""
        return self.transaction_type == TransactionType.DEBIT or self.amount < 0

    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit."""
        return self.transaction_type == TransactionType.CREDIT or self.amount > 0


@dataclass
class StatementData:
    """Parsed bank statement data.

    Attributes:
        transactions: List of parsed transactions
        bank_name: Detected or specified bank name
        account_number: Account number (masked if present)
        currency: Statement currency (ISO code)
        statement_date: Statement generation date
        period_start: Statement period start date
        period_end: Statement period end date
        opening_balance: Opening balance (if available)
        closing_balance: Closing balance (if available)
        format: Source format (PDF, CSV, OFX, etc.)
        filename: Original filename
        raw_text: Raw text content (for debugging)
        metadata: Additional metadata from the statement
    """

    transactions: list[Transaction] = field(default_factory=list)
    bank_name: str | None = None
    account_number: str | None = None
    currency: str = "GBP"
    statement_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    opening_balance: Decimal | None = None
    closing_balance: Decimal | None = None
    format: StatementFormat = StatementFormat.UNKNOWN
    filename: str | None = None
    raw_text: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def transaction_count(self) -> int:
        """Return number of transactions."""
        return len(self.transactions)

    @property
    def total_debits(self) -> Decimal:
        """Sum of all debit transactions."""
        return sum(t.abs_amount for t in self.transactions if t.is_debit)

    @property
    def total_credits(self) -> Decimal:
        """Sum of all credit transactions."""
        return sum(t.abs_amount for t in self.transactions if t.is_credit)

    @property
    def net_change(self) -> Decimal:
        """Net change (credits - debits)."""
        return self.total_credits - self.total_debits

    def filter_debits(self) -> list[Transaction]:
        """Return only debit transactions."""
        return [t for t in self.transactions if t.is_debit]

    def filter_credits(self) -> list[Transaction]:
        """Return only credit transactions."""
        return [t for t in self.transactions if t.is_credit]

    def filter_by_amount(
        self, min_amount: Decimal | None = None, max_amount: Decimal | None = None
    ) -> list[Transaction]:
        """Filter transactions by amount range."""
        result = self.transactions
        if min_amount is not None:
            result = [t for t in result if t.abs_amount >= min_amount]
        if max_amount is not None:
            result = [t for t in result if t.abs_amount <= max_amount]
        return result

    def filter_by_date(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> list[Transaction]:
        """Filter transactions by date range."""
        result = self.transactions
        if start_date is not None:
            result = [t for t in result if t.date >= start_date]
        if end_date is not None:
            result = [t for t in result if t.date <= end_date]
        return result

    def search_description(self, keyword: str) -> list[Transaction]:
        """Search transactions by description keyword."""
        keyword_lower = keyword.lower()
        return [t for t in self.transactions if keyword_lower in t.description.lower()]


class StatementParser(ABC):
    """Abstract base class for bank statement parsers.

    Subclasses must implement the parse() method to handle specific formats.
    """

    def __init__(self, bank_name: str | None = None, currency: str = "GBP") -> None:
        """Initialize parser.

        Args:
            bank_name: Optional bank name for the statement
            currency: Default currency if not detected
        """
        self.bank_name = bank_name
        self.default_currency = currency

    @abstractmethod
    def parse(self, file: BinaryIO | Path | str) -> StatementData:
        """Parse a bank statement file.

        Args:
            file: File object, path, or filename to parse

        Returns:
            StatementData containing parsed transactions

        Raises:
            ParserError: If parsing fails
            UnsupportedFormatError: If format is not supported
        """
        pass

    @abstractmethod
    def can_parse(self, file: BinaryIO | Path | str) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file: File to check

        Returns:
            True if parser can handle this file
        """
        pass

    def _read_file(self, file: BinaryIO | Path | str) -> bytes:
        """Read file content.

        Args:
            file: File object, path, or filename

        Returns:
            File content as bytes
        """
        if isinstance(file, (str, Path)):
            path = Path(file)
            if not path.exists():
                raise ParserError(f"File not found: {path}")
            return path.read_bytes()
        else:
            return file.read()

    def _get_filename(self, file: BinaryIO | Path | str) -> str | None:
        """Extract filename from file object or path."""
        if isinstance(file, (str, Path)):
            return Path(file).name
        elif hasattr(file, "name"):
            return Path(file.name).name
        return None

    def _parse_date(self, date_str: str, formats: list[str] | None = None) -> date | None:
        """Parse date string using multiple formats.

        Args:
            date_str: Date string to parse
            formats: List of date formats to try

        Returns:
            Parsed date or None if parsing fails
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        if formats is None:
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%d %b %Y",
                "%d %B %Y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%Y%m%d",
            ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _parse_amount(self, amount_str: str) -> Decimal | None:
        """Parse amount string to Decimal.

        Handles various formats:
        - 1,234.56 (US/UK)
        - 1.234,56 (EU)
        - -1234.56 (negative)
        - (1234.56) (accounting negative)

        Args:
            amount_str: Amount string to parse

        Returns:
            Parsed Decimal or None if parsing fails
        """
        if not amount_str:
            return None

        amount_str = amount_str.strip()

        # Handle accounting format negative (1234.56)
        is_negative = False
        if amount_str.startswith("(") and amount_str.endswith(")"):
            is_negative = True
            amount_str = amount_str[1:-1]

        # Handle explicit negative sign
        if amount_str.startswith("-"):
            is_negative = True
            amount_str = amount_str[1:]

        # Remove currency symbols and spaces
        amount_str = amount_str.replace("£", "").replace("$", "").replace("€", "")
        amount_str = amount_str.replace(" ", "")

        # Detect format (US/UK vs EU)
        # EU format: 1.234,56 (period as thousands, comma as decimal)
        # US/UK format: 1,234.56 (comma as thousands, period as decimal)

        if "," in amount_str and "." in amount_str:
            # Both present - determine which is decimal separator
            comma_pos = amount_str.rfind(",")
            period_pos = amount_str.rfind(".")

            if comma_pos > period_pos:
                # EU format: 1.234,56
                amount_str = amount_str.replace(".", "").replace(",", ".")
            else:
                # US/UK format: 1,234.56
                amount_str = amount_str.replace(",", "")
        elif "," in amount_str:
            # Only comma - could be decimal or thousands
            # If there are exactly 2 digits after comma, treat as decimal
            parts = amount_str.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                amount_str = amount_str.replace(",", ".")
            else:
                amount_str = amount_str.replace(",", "")
        # If only period, keep as-is (standard decimal)

        try:
            result = Decimal(amount_str)
            if is_negative:
                result = -result
            return result
        except Exception as e:
            logger.warning(f"Could not parse amount '{amount_str}': {e}")
            return None

    def _detect_currency(self, text: str) -> str:
        """Detect currency from text.

        Args:
            text: Text to search for currency indicators

        Returns:
            ISO currency code
        """
        text_upper = text.upper()

        currency_patterns = {
            "GBP": ["£", "GBP", "POUND", "STERLING"],
            "USD": ["$", "USD", "DOLLAR", "US$"],
            "EUR": ["€", "EUR", "EURO"],
            "BRL": ["R$", "BRL", "REAL", "REAIS"],
            "UAH": ["₴", "UAH", "HRYVNIA"],
        }

        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                if pattern in text_upper:
                    return currency

        return self.default_currency


def detect_format(file: BinaryIO | Path | str) -> StatementFormat:
    """Detect the format of a statement file.

    Args:
        file: File to check

    Returns:
        Detected StatementFormat
    """
    # Get filename for extension check
    if isinstance(file, (str, Path)):
        path = Path(file)
        ext = path.suffix.lower()
    elif hasattr(file, "name"):
        ext = Path(file.name).suffix.lower()
    else:
        ext = ""

    # Check by extension
    ext_map = {
        ".pdf": StatementFormat.PDF,
        ".csv": StatementFormat.CSV,
        ".ofx": StatementFormat.OFX,
        ".qfx": StatementFormat.OFX,  # QFX is OFX variant
        ".qif": StatementFormat.QIF,
    }

    if ext in ext_map:
        return ext_map[ext]

    # Try to detect from content
    try:
        if isinstance(file, (str, Path)):
            content = Path(file).read_bytes()[:1000]
        else:
            pos = file.tell()
            content = file.read(1000)
            file.seek(pos)

        # PDF magic bytes
        if content.startswith(b"%PDF"):
            return StatementFormat.PDF

        # OFX/QFX content
        text_content = content.decode("utf-8", errors="ignore")
        if "<OFX>" in text_content or "OFXHEADER:" in text_content:
            return StatementFormat.OFX

        # QIF content
        if text_content.startswith("!Type:"):
            return StatementFormat.QIF

        # CSV heuristic (comma-separated with header-like first line)
        lines = text_content.split("\n")
        if len(lines) >= 2 and "," in lines[0]:
            return StatementFormat.CSV

    except Exception:
        pass

    return StatementFormat.UNKNOWN
