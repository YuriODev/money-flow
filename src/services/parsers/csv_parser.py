"""CSV bank statement parser with dynamic bank profile lookup.

This module parses CSV bank statements using:
1. Dynamic bank profile database for column mappings
2. Auto-detection of bank from filename/headers
3. Flexible column mapping for different bank formats
"""

from __future__ import annotations

import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from src.models.bank_profile import BankProfile
from src.services.parsers.base import (
    EmptyStatementError,
    ParseError,
    StatementData,
    StatementFormat,
    StatementParser,
    Transaction,
    TransactionType,
)

if TYPE_CHECKING:
    from src.services.bank_service import BankService

logger = logging.getLogger(__name__)


class CSVStatementParser(StatementParser):
    """Parser for CSV bank statements.

    Uses dynamic bank profiles from database for column mappings.
    Supports auto-detection of bank format from filename and headers.
    """

    def __init__(
        self,
        bank_service: BankService | None = None,
        bank_profile: BankProfile | None = None,
        bank_name: str | None = None,
        currency: str = "GBP",
    ) -> None:
        """Initialize CSV parser.

        Args:
            bank_service: Service for bank profile lookup
            bank_profile: Pre-loaded bank profile (skip auto-detection)
            bank_name: Optional bank name override
            currency: Default currency if not detected
        """
        super().__init__(bank_name, currency)
        self.bank_service = bank_service
        self.bank_profile = bank_profile

    async def parse_async(self, file: BinaryIO | Path | str) -> StatementData:
        """Parse a CSV bank statement asynchronously.

        Uses bank service for profile lookup.

        Args:
            file: CSV file to parse

        Returns:
            StatementData with extracted transactions

        Raises:
            ParseError: If CSV parsing fails
            EmptyStatementError: If no transactions found
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Try to decode as text
            text = self._decode_content(content)

            # Parse CSV to get headers and rows
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if not rows:
                raise EmptyStatementError("CSV file is empty")

            # Get bank profile
            bank_profile = await self._get_bank_profile(filename, rows)
            mapping = bank_profile.csv_mapping if bank_profile else {}

            # Skip header rows
            skip_rows = mapping.get("skip_rows", 0)
            header_row = mapping.get("header_row", 0)

            # Get headers
            if len(rows) <= header_row:
                raise ParseError(f"Not enough rows for header at row {header_row}")

            headers = rows[skip_rows + header_row]
            data_rows = rows[skip_rows + header_row + 1 :]

            # Find column indexes
            col_map = self._map_columns(headers, mapping)

            # Parse transactions
            transactions = self._parse_rows(data_rows, col_map, mapping)

            if not transactions:
                raise EmptyStatementError("No transactions found in CSV")

            # Sort by date
            transactions.sort(key=lambda t: t.date)

            return StatementData(
                transactions=transactions,
                bank_name=bank_profile.name if bank_profile else self.bank_name,
                currency=bank_profile.currency if bank_profile else self.currency,
                format=StatementFormat.CSV,
                filename=filename,
                raw_text=text[:10000],
                period_start=transactions[0].date if transactions else None,
                period_end=transactions[-1].date if transactions else None,
            )

        except EmptyStatementError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise ParseError(f"Failed to parse CSV: {e}") from e

    def parse(self, file: BinaryIO | Path | str) -> StatementData:
        """Parse a CSV bank statement (synchronous fallback).

        For synchronous parsing without bank service lookup.

        Args:
            file: CSV file to parse

        Returns:
            StatementData with extracted transactions
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Try to decode as text
            text = self._decode_content(content)

            # Parse CSV
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if not rows:
                raise EmptyStatementError("CSV file is empty")

            # Use provided bank profile or default mapping
            mapping = self.bank_profile.csv_mapping if self.bank_profile else {}

            # Skip header rows
            skip_rows = mapping.get("skip_rows", 0)
            header_row = mapping.get("header_row", 0)

            if len(rows) <= header_row:
                raise ParseError(f"Not enough rows for header at row {header_row}")

            headers = rows[skip_rows + header_row]
            data_rows = rows[skip_rows + header_row + 1 :]

            # Find column indexes
            col_map = self._map_columns(headers, mapping)

            # Parse transactions
            transactions = self._parse_rows(data_rows, col_map, mapping)

            if not transactions:
                raise EmptyStatementError("No transactions found in CSV")

            transactions.sort(key=lambda t: t.date)

            return StatementData(
                transactions=transactions,
                bank_name=self.bank_profile.name if self.bank_profile else self.bank_name,
                currency=self.bank_profile.currency if self.bank_profile else self.currency,
                format=StatementFormat.CSV,
                filename=filename,
                raw_text=text[:10000],
                period_start=transactions[0].date if transactions else None,
                period_end=transactions[-1].date if transactions else None,
            )

        except EmptyStatementError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise ParseError(f"Failed to parse CSV: {e}") from e

    def can_parse(self, file: BinaryIO | Path | str) -> bool:
        """Check if file is a CSV.

        Args:
            file: File to check

        Returns:
            True if file appears to be CSV
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Check extension
            if filename and filename.lower().endswith(".csv"):
                return True

            # Try to decode and parse as CSV
            text = self._decode_content(content)
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            # Basic CSV validation - at least 2 rows, consistent columns
            if len(rows) < 2:
                return False

            first_row_cols = len(rows[0])
            for row in rows[1:5]:  # Check first few rows
                if len(row) != first_row_cols:
                    return False

            return True

        except Exception:
            return False

    async def _get_bank_profile(
        self, filename: str | None, rows: list[list[str]]
    ) -> BankProfile | None:
        """Get bank profile from provided profile or auto-detect.

        Args:
            filename: Original filename
            rows: CSV rows

        Returns:
            Bank profile or None
        """
        # Use provided profile
        if self.bank_profile:
            return self.bank_profile

        # Try auto-detection with bank service
        if self.bank_service:
            headers = rows[0] if rows else None
            content = "\n".join([",".join(row) for row in rows[:5]])

            detected = await self.bank_service.detect_bank(
                filename=filename,
                headers=headers,
                content=content,
            )

            if detected:
                logger.info(f"Auto-detected bank: {detected.slug}")
                return detected

        return None

    def _decode_content(self, content: bytes) -> str:
        """Decode binary content to text.

        Tries multiple encodings.

        Args:
            content: Binary content

        Returns:
            Decoded text

        Raises:
            ParseError: If decoding fails
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        raise ParseError("Failed to decode CSV content")

    def _map_columns(
        self, headers: list[str], mapping: dict
    ) -> dict[str, int | None]:
        """Map column names to indexes.

        Args:
            headers: Header row
            mapping: Column mapping from bank profile

        Returns:
            Dict of column name to index
        """
        col_map: dict[str, int | None] = {
            "date": None,
            "description": None,
            "amount": None,
            "debit": None,
            "credit": None,
            "balance": None,
            "reference": None,
            "category": None,
        }

        # Normalize headers for matching
        normalized_headers = [h.lower().strip() for h in headers]

        # Map using bank profile columns
        column_defs = {
            "date": mapping.get("date_columns", ["date", "transaction date"]),
            "description": mapping.get(
                "description_columns", ["description", "details", "memo", "payee", "name"]
            ),
            "amount": mapping.get("amount_columns", ["amount", "value", "sum"]),
            "debit": mapping.get("debit_columns", ["debit", "money out", "paid out", "withdrawal"]),
            "credit": mapping.get(
                "credit_columns", ["credit", "money in", "paid in", "deposit"]
            ),
            "balance": mapping.get("balance_columns", ["balance", "running balance"]),
            "reference": mapping.get("reference_columns", ["reference", "ref", "transaction id"]),
            "category": mapping.get("category_columns", ["category", "type"]),
        }

        for col_name, keywords in column_defs.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for i, header in enumerate(normalized_headers):
                    if keyword_lower in header or header == keyword_lower:
                        col_map[col_name] = i
                        break
                if col_map[col_name] is not None:
                    break

        logger.debug(f"Column mapping: {col_map}")
        return col_map

    def _parse_rows(
        self,
        rows: list[list[str]],
        col_map: dict[str, int | None],
        mapping: dict,
    ) -> list[Transaction]:
        """Parse data rows into transactions.

        Args:
            rows: Data rows
            col_map: Column mapping
            mapping: Bank profile mapping

        Returns:
            List of transactions
        """
        transactions: list[Transaction] = []
        date_format = mapping.get("date_format")

        for row in rows:
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip empty rows

            try:
                # Extract date
                date_col = col_map["date"]
                if date_col is None or len(row) <= date_col:
                    continue

                date_str = row[date_col].strip()
                parsed_date = self._parse_date(date_str, date_format)
                if not parsed_date:
                    continue

                # Extract description
                desc_col = col_map["description"]
                description = ""
                if desc_col is not None and len(row) > desc_col:
                    description = row[desc_col].strip()

                if not description:
                    # Try to build description from other columns
                    for key in ["reference", "category"]:
                        idx = col_map.get(key)
                        if idx is not None and len(row) > idx and row[idx].strip():
                            description = row[idx].strip()
                            break

                if not description or len(description) < 2:
                    continue

                # Extract amount
                amount: Decimal | None = None
                transaction_type = TransactionType.UNKNOWN

                # Try single amount column
                amount_col = col_map["amount"]
                if amount_col is not None and len(row) > amount_col:
                    amount = self._parse_amount(row[amount_col])
                    if amount:
                        transaction_type = (
                            TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT
                        )

                # Try separate debit/credit columns
                if amount is None:
                    debit_col = col_map["debit"]
                    credit_col = col_map["credit"]

                    if debit_col is not None and len(row) > debit_col:
                        debit = self._parse_amount(row[debit_col])
                        if debit and debit != Decimal("0"):
                            amount = -abs(debit)
                            transaction_type = TransactionType.DEBIT

                    if credit_col is not None and len(row) > credit_col:
                        credit = self._parse_amount(row[credit_col])
                        if credit and credit != Decimal("0"):
                            amount = abs(credit)
                            transaction_type = TransactionType.CREDIT

                if amount is None:
                    continue

                # Extract balance
                balance: Decimal | None = None
                balance_col = col_map["balance"]
                if balance_col is not None and len(row) > balance_col:
                    balance = self._parse_amount(row[balance_col])

                # Extract reference
                reference: str | None = None
                ref_col = col_map["reference"]
                if ref_col is not None and len(row) > ref_col:
                    reference = row[ref_col].strip() or None

                # Extract category
                category: str | None = None
                cat_col = col_map["category"]
                if cat_col is not None and len(row) > cat_col:
                    category = row[cat_col].strip() or None

                transactions.append(
                    Transaction(
                        date=parsed_date,
                        amount=amount,
                        description=description,
                        transaction_type=transaction_type,
                        balance=balance,
                        reference=reference,
                        category=category,
                        raw_data={"row": row},
                    )
                )

            except Exception as e:
                logger.debug(f"Skipping row due to parse error: {e}")
                continue

        return transactions

    def _parse_amount(self, amount_str: str) -> Decimal | None:
        """Parse amount string to Decimal.

        Handles various formats:
        - 1,234.56 or 1.234,56
        - (1234.56) accounting format
        - -1234.56 negative
        - £$€ currency symbols

        Args:
            amount_str: Amount string

        Returns:
            Decimal amount or None
        """
        if not amount_str:
            return None

        amount_str = amount_str.strip()
        if not amount_str:
            return None

        # Check for accounting negative format (parentheses)
        is_negative = False
        if amount_str.startswith("(") and amount_str.endswith(")"):
            amount_str = amount_str[1:-1]
            is_negative = True

        # Remove currency symbols
        amount_str = amount_str.replace("£", "").replace("$", "").replace("€", "").replace("R$", "")
        amount_str = amount_str.replace("UAH", "").replace("₴", "")
        amount_str = amount_str.strip()

        # Handle explicit negative
        if amount_str.startswith("-"):
            is_negative = True
            amount_str = amount_str[1:]

        # Remove spaces and handle thousands separators
        amount_str = amount_str.replace(" ", "")

        # Determine decimal separator (last . or , before 2-3 digits at end)
        if "." in amount_str and "," in amount_str:
            # Both present - the last one is decimal separator
            last_dot = amount_str.rfind(".")
            last_comma = amount_str.rfind(",")

            if last_dot > last_comma:
                # Dot is decimal: 1,234.56
                amount_str = amount_str.replace(",", "")
            else:
                # Comma is decimal: 1.234,56
                amount_str = amount_str.replace(".", "").replace(",", ".")
        elif "," in amount_str:
            # Only comma - check if it's decimal separator
            parts = amount_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Comma is decimal: 1234,56
                amount_str = amount_str.replace(",", ".")
            else:
                # Comma is thousands: 1,234
                amount_str = amount_str.replace(",", "")

        try:
            amount = Decimal(amount_str)
            if is_negative:
                amount = -abs(amount)
            return amount
        except InvalidOperation:
            return None
