"""PDF bank statement parser using pdfplumber.

This module extracts transactions from PDF bank statements by:
1. Extracting text and tables from each page
2. Identifying transaction rows using patterns
3. Parsing date, description, and amount columns
"""

from __future__ import annotations

import io
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

import pdfplumber
from pdfplumber.page import Page

from src.services.parsers.base import (
    EmptyStatementError,
    ParseError,
    StatementData,
    StatementFormat,
    StatementParser,
    Transaction,
    TransactionType,
)

logger = logging.getLogger(__name__)


class PDFStatementParser(StatementParser):
    """Parser for PDF bank statements.

    Uses pdfplumber to extract text and tables from PDFs.
    Handles various bank statement layouts through pattern matching.
    """

    # Common patterns for transaction detection
    DATE_PATTERNS = [
        r"\d{2}/\d{2}/\d{4}",  # DD/MM/YYYY or MM/DD/YYYY
        r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}\s+\w{3}\s+\d{4}",  # DD Mon YYYY
        r"\d{2}\s+\w{3}\s+\d{2}",  # DD Mon YY
        r"\w{3}\s+\d{2},?\s+\d{4}",  # Mon DD, YYYY
    ]

    AMOUNT_PATTERNS = [
        r"[£$€]\s*[\d,]+\.\d{2}",  # £1,234.56
        r"[\d,]+\.\d{2}\s*[£$€]",  # 1,234.56£
        r"-?\s*[\d,]+\.\d{2}",  # 1234.56 or -1234.56
        r"\([\d,]+\.\d{2}\)",  # (1234.56) accounting format
    ]

    # Bank identification patterns
    BANK_PATTERNS = {
        "monzo": [r"monzo", r"monzo\.com"],
        "revolut": [r"revolut", r"revolut\.com"],
        "starling": [r"starling", r"starling bank"],
        "barclays": [r"barclays", r"barclays bank"],
        "hsbc": [r"hsbc", r"hsbc bank", r"hsbc uk"],
        "lloyds": [r"lloyds", r"lloyds bank", r"lloyds tsb"],
        "natwest": [r"natwest", r"national westminster"],
        "santander": [r"santander", r"santander uk"],
        "nationwide": [r"nationwide", r"nationwide building society"],
        "halifax": [r"halifax", r"halifax bank"],
        "chase": [r"chase", r"jpmorgan chase", r"chase bank"],
        "bank_of_america": [r"bank of america", r"bofa"],
        "wells_fargo": [r"wells fargo"],
        "citi": [r"citi", r"citibank"],
        "nubank": [r"nubank", r"nu bank"],
        "itau": [r"itaú", r"itau"],
        "bradesco": [r"bradesco"],
        "n26": [r"n26", r"number26"],
    }

    def __init__(
        self,
        bank_name: str | None = None,
        currency: str = "GBP",
        date_format: str | None = None,
    ) -> None:
        """Initialize PDF parser.

        Args:
            bank_name: Optional bank name (auto-detected if not provided)
            currency: Default currency if not detected
            date_format: Specific date format to use (auto-detected if not provided)
        """
        super().__init__(bank_name, currency)
        self.date_format = date_format

    def parse(self, file: BinaryIO | Path | str) -> StatementData:
        """Parse a PDF bank statement.

        Args:
            file: PDF file to parse

        Returns:
            StatementData with extracted transactions

        Raises:
            ParseError: If PDF parsing fails
            EmptyStatementError: If no transactions found
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Open PDF with pdfplumber
            pdf_file = io.BytesIO(content)
            with pdfplumber.open(pdf_file) as pdf:
                # Extract all text for bank/currency detection
                all_text = ""
                all_transactions: list[Transaction] = []

                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n"

                    # Try table extraction first (more structured)
                    tables = page.extract_tables()
                    if tables:
                        transactions = self._parse_tables(tables, page)
                        all_transactions.extend(transactions)
                    else:
                        # Fall back to text extraction
                        transactions = self._parse_text(page_text)
                        all_transactions.extend(transactions)

                if not all_transactions:
                    raise EmptyStatementError("No transactions found in PDF")

                # Detect bank and currency
                detected_bank = self._detect_bank(all_text)
                detected_currency = self._detect_currency(all_text)

                # Sort transactions by date
                all_transactions.sort(key=lambda t: t.date)

                return StatementData(
                    transactions=all_transactions,
                    bank_name=self.bank_name or detected_bank,
                    currency=detected_currency,
                    format=StatementFormat.PDF,
                    filename=filename,
                    raw_text=all_text[:10000],  # Truncate for storage
                    period_start=all_transactions[0].date if all_transactions else None,
                    period_end=all_transactions[-1].date if all_transactions else None,
                )

        except EmptyStatementError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise ParseError(f"Failed to parse PDF: {e}") from e

    def can_parse(self, file: BinaryIO | Path | str) -> bool:
        """Check if file is a PDF.

        Args:
            file: File to check

        Returns:
            True if file is a PDF
        """
        try:
            content = self._read_file(file)
            return content.startswith(b"%PDF")
        except Exception:
            return False

    def _parse_tables(self, tables: list, page: Page) -> list[Transaction]:
        """Parse transactions from extracted tables.

        Args:
            tables: List of tables from pdfplumber
            page: The page object for context

        Returns:
            List of parsed transactions
        """
        transactions: list[Transaction] = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # First row is likely header
            header = [str(cell).lower() if cell else "" for cell in table[0]]

            # Find relevant columns
            date_col = self._find_column(header, ["date", "datum", "data", "transaction date"])
            desc_col = self._find_column(
                header, ["description", "details", "memo", "payee", "narrative", "reference"]
            )
            amount_col = self._find_column(
                header, ["amount", "value", "sum", "debit", "credit", "money out", "money in"]
            )
            debit_col = self._find_column(header, ["debit", "money out", "paid out", "withdrawal"])
            credit_col = self._find_column(header, ["credit", "money in", "paid in", "deposit"])
            balance_col = self._find_column(header, ["balance", "running balance", "saldo"])

            # Process rows
            for row in table[1:]:
                if not row or len(row) <= max(
                    filter(None, [date_col, desc_col, amount_col, debit_col, credit_col]), default=0
                ):
                    continue

                try:
                    # Extract date
                    date_str = str(row[date_col]) if date_col is not None else ""
                    parsed_date = self._parse_date(date_str)
                    if not parsed_date:
                        continue

                    # Extract description
                    description = str(row[desc_col]).strip() if desc_col is not None else ""
                    if not description:
                        continue

                    # Extract amount
                    amount: Decimal | None = None
                    transaction_type = TransactionType.UNKNOWN

                    if amount_col is not None:
                        amount = self._parse_amount(str(row[amount_col]))
                    elif debit_col is not None and credit_col is not None:
                        # Separate debit/credit columns
                        debit_str = str(row[debit_col]) if row[debit_col] else ""
                        credit_str = str(row[credit_col]) if row[credit_col] else ""

                        debit_amount = self._parse_amount(debit_str)
                        credit_amount = self._parse_amount(credit_str)

                        if debit_amount and debit_amount != Decimal("0"):
                            amount = -abs(debit_amount)
                            transaction_type = TransactionType.DEBIT
                        elif credit_amount and credit_amount != Decimal("0"):
                            amount = abs(credit_amount)
                            transaction_type = TransactionType.CREDIT

                    if amount is None:
                        continue

                    # Extract balance if available
                    balance = None
                    if balance_col is not None and len(row) > balance_col:
                        balance = self._parse_amount(str(row[balance_col]))

                    transactions.append(
                        Transaction(
                            date=parsed_date,
                            amount=amount,
                            description=description,
                            transaction_type=transaction_type,
                            balance=balance,
                            raw_data={"row": row},
                        )
                    )

                except Exception as e:
                    logger.debug(f"Skipping row due to parse error: {e}")
                    continue

        return transactions

    def _parse_text(self, text: str) -> list[Transaction]:
        """Parse transactions from raw text.

        Falls back to pattern matching when table extraction fails.

        Args:
            text: Raw text from PDF page

        Returns:
            List of parsed transactions
        """
        transactions: list[Transaction] = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for lines with date and amount patterns
            date_match = None
            for pattern in self.DATE_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    date_match = match
                    break

            if not date_match:
                continue

            # Found a potential transaction line
            parsed_date = self._parse_date(date_match.group())
            if not parsed_date:
                continue

            # Look for amount
            amount_match = None
            for pattern in self.AMOUNT_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    amount_match = match
                    break

            if not amount_match:
                continue

            amount = self._parse_amount(amount_match.group())
            if amount is None:
                continue

            # Extract description (text between date and amount)
            date_end = date_match.end()
            amount_start = amount_match.start()

            if amount_start > date_end:
                description = line[date_end:amount_start].strip()
            else:
                # Amount before date - try rest of line
                description = line[max(date_match.end(), amount_match.end()) :].strip()

            if not description:
                # Try text after amount
                description = line[amount_match.end() :].strip()

            if not description or len(description) < 3:
                continue

            transactions.append(
                Transaction(
                    date=parsed_date,
                    amount=amount,
                    description=description,
                    raw_data={"line": line},
                )
            )

        return transactions

    def _find_column(self, header: list[str], keywords: list[str]) -> int | None:
        """Find column index matching any keyword.

        Args:
            header: List of header cell values (lowercase)
            keywords: Keywords to search for

        Returns:
            Column index or None if not found
        """
        for i, cell in enumerate(header):
            cell_clean = cell.strip().lower()
            for keyword in keywords:
                if keyword in cell_clean:
                    return i
        return None

    def _detect_bank(self, text: str) -> str | None:
        """Detect bank name from PDF text.

        Args:
            text: Full PDF text content

        Returns:
            Bank slug or None if not detected
        """
        text_lower = text.lower()

        for bank_slug, patterns in self.BANK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Detected bank: {bank_slug}")
                    return bank_slug

        return None
