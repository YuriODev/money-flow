"""OFX/QIF bank statement parser.

This module parses OFX (Open Financial Exchange) and QIF (Quicken Interchange Format)
bank statements using the ofxparse library.

Supported formats:
- OFX 1.x (SGML-based)
- OFX 2.x (XML-based)
- QFX (Quicken OFX variant)
- QIF (legacy Quicken format)
"""

from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

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


class OFXStatementParser(StatementParser):
    """Parser for OFX and QIF bank statements.

    Uses ofxparse library for OFX/QFX files.
    Has custom parser for QIF files.
    """

    # OFX transaction type mapping
    OFX_TYPE_MAP = {
        "credit": TransactionType.CREDIT,
        "debit": TransactionType.DEBIT,
        "int": TransactionType.CREDIT,  # Interest
        "div": TransactionType.CREDIT,  # Dividend
        "fee": TransactionType.DEBIT,  # Fee
        "srvchg": TransactionType.DEBIT,  # Service charge
        "dep": TransactionType.CREDIT,  # Deposit
        "atm": TransactionType.DEBIT,  # ATM withdrawal
        "pos": TransactionType.DEBIT,  # Point of sale
        "xfer": TransactionType.UNKNOWN,  # Transfer
        "check": TransactionType.DEBIT,  # Check
        "payment": TransactionType.DEBIT,  # Payment
        "cash": TransactionType.UNKNOWN,  # Cash
        "directdep": TransactionType.CREDIT,  # Direct deposit
        "directdebit": TransactionType.DEBIT,  # Direct debit
        "repeatpmt": TransactionType.DEBIT,  # Repeating payment
        "other": TransactionType.UNKNOWN,
    }

    # QIF transaction type mapping
    QIF_TYPE_MAP = {
        "D": "date",
        "T": "amount",
        "U": "amount",  # Amount in US dollars
        "P": "payee",
        "M": "memo",
        "N": "number",  # Check number
        "C": "cleared",
        "L": "category",
        "S": "split_category",
        "$": "split_amount",
        "E": "split_memo",
        "A": "address",
    }

    def __init__(
        self,
        bank_name: str | None = None,
        currency: str = "GBP",
    ) -> None:
        """Initialize OFX/QIF parser.

        Args:
            bank_name: Optional bank name override
            currency: Default currency if not in file
        """
        super().__init__(bank_name, currency)

    def parse(self, file: BinaryIO | Path | str) -> StatementData:
        """Parse an OFX or QIF bank statement.

        Args:
            file: OFX/QIF file to parse

        Returns:
            StatementData with extracted transactions

        Raises:
            ParseError: If parsing fails
            EmptyStatementError: If no transactions found
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Determine format and parse
            format_type = self._detect_format(content, filename)

            if format_type == StatementFormat.QIF:
                return self._parse_qif(content, filename)
            else:
                return self._parse_ofx(content, filename)

        except EmptyStatementError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse OFX/QIF: {e}")
            raise ParseError(f"Failed to parse OFX/QIF: {e}") from e

    def can_parse(self, file: BinaryIO | Path | str) -> bool:
        """Check if file is OFX or QIF format.

        Args:
            file: File to check

        Returns:
            True if file is OFX/QIF format
        """
        try:
            content = self._read_file(file)
            filename = self._get_filename(file)

            # Check by extension
            if filename:
                lower_name = filename.lower()
                if lower_name.endswith((".ofx", ".qfx", ".qif")):
                    return True

            # Check by content
            text = content.decode("utf-8", errors="ignore")[:1000]

            # OFX signatures
            if "OFXHEADER" in text or "<OFX>" in text or "<?OFX" in text:
                return True

            # QIF signature
            if text.strip().startswith("!Type:"):
                return True

            return False

        except Exception:
            return False

    def _detect_format(self, content: bytes, filename: str | None) -> StatementFormat:
        """Detect whether file is OFX or QIF format.

        Args:
            content: File content
            filename: Original filename

        Returns:
            StatementFormat.OFX or StatementFormat.QIF
        """
        # Check extension
        if filename:
            if filename.lower().endswith(".qif"):
                return StatementFormat.QIF

        # Check content
        text = content.decode("utf-8", errors="ignore")[:500]

        if text.strip().startswith("!Type:"):
            return StatementFormat.QIF

        return StatementFormat.OFX

    def _parse_ofx(self, content: bytes, filename: str | None) -> StatementData:
        """Parse OFX/QFX format.

        Args:
            content: File content
            filename: Original filename

        Returns:
            StatementData
        """
        try:
            import ofxparse
        except ImportError:
            raise ParseError("ofxparse library not installed. Run: pip install ofxparse")

        # Parse OFX
        ofx = ofxparse.OfxParser.parse(io.BytesIO(content))

        transactions: list[Transaction] = []
        bank_name = self.bank_name
        currency = self.currency

        # Process accounts
        for account in ofx.accounts if hasattr(ofx, "accounts") else [ofx.account]:
            if not account:
                continue

            # Get account info
            if hasattr(account, "institution"):
                if account.institution and hasattr(account.institution, "organization"):
                    bank_name = account.institution.organization or bank_name

            if hasattr(account, "statement"):
                stmt = account.statement
                if hasattr(stmt, "currency") and stmt.currency:
                    currency = stmt.currency

                # Process transactions
                if hasattr(stmt, "transactions"):
                    for txn in stmt.transactions:
                        try:
                            parsed_txn = self._parse_ofx_transaction(txn)
                            if parsed_txn:
                                transactions.append(parsed_txn)
                        except Exception as e:
                            logger.debug(f"Skipping OFX transaction: {e}")
                            continue

        if not transactions:
            raise EmptyStatementError("No transactions found in OFX file")

        # Sort by date
        transactions.sort(key=lambda t: t.date)

        return StatementData(
            transactions=transactions,
            bank_name=bank_name,
            currency=currency,
            format=StatementFormat.OFX,
            filename=filename,
            period_start=transactions[0].date if transactions else None,
            period_end=transactions[-1].date if transactions else None,
        )

    def _parse_ofx_transaction(self, txn) -> Transaction | None:
        """Parse a single OFX transaction.

        Args:
            txn: OFX transaction object

        Returns:
            Transaction or None
        """
        # Get date
        txn_date = getattr(txn, "date", None)
        if not txn_date:
            return None

        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        elif not isinstance(txn_date, date):
            return None

        # Get amount
        amount = getattr(txn, "amount", None)
        if amount is None:
            return None

        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except Exception:
                return None

        # Get description
        description = ""
        for attr in ["payee", "memo", "name"]:
            val = getattr(txn, attr, None)
            if val:
                description = str(val).strip()
                break

        if not description:
            description = "Unknown transaction"

        # Get transaction type
        txn_type_str = str(getattr(txn, "type", "other")).lower()
        transaction_type = self.OFX_TYPE_MAP.get(txn_type_str, TransactionType.UNKNOWN)

        # Override based on amount if type is unknown
        if transaction_type == TransactionType.UNKNOWN:
            transaction_type = TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT

        # Get reference/check number
        reference = None
        for attr in ["id", "checknum", "refnum"]:
            val = getattr(txn, attr, None)
            if val:
                reference = str(val)
                break

        return Transaction(
            date=txn_date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            reference=reference,
            raw_data={"ofx_type": txn_type_str},
        )

    def _parse_qif(self, content: bytes, filename: str | None) -> StatementData:
        """Parse QIF format.

        Args:
            content: File content
            filename: Original filename

        Returns:
            StatementData
        """
        text = content.decode("utf-8", errors="ignore")
        lines = text.split("\n")

        transactions: list[Transaction] = []
        current_txn: dict = {}
        account_type = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Account type header
            if line.startswith("!Type:"):
                account_type = line[6:].strip()
                continue

            # End of transaction
            if line == "^":
                if current_txn:
                    parsed = self._parse_qif_transaction(current_txn)
                    if parsed:
                        transactions.append(parsed)
                current_txn = {}
                continue

            # Parse field
            if len(line) >= 2:
                field_type = line[0]
                field_value = line[1:].strip()

                field_name = self.QIF_TYPE_MAP.get(field_type)
                if field_name:
                    if field_name in current_txn and field_name != "memo":
                        # Handle multiple memos by appending
                        current_txn[field_name] += " " + field_value
                    else:
                        current_txn[field_name] = field_value

        # Handle last transaction
        if current_txn:
            parsed = self._parse_qif_transaction(current_txn)
            if parsed:
                transactions.append(parsed)

        if not transactions:
            raise EmptyStatementError("No transactions found in QIF file")

        # Sort by date
        transactions.sort(key=lambda t: t.date)

        return StatementData(
            transactions=transactions,
            bank_name=self.bank_name,
            currency=self.currency,
            format=StatementFormat.QIF,
            filename=filename,
            period_start=transactions[0].date if transactions else None,
            period_end=transactions[-1].date if transactions else None,
            raw_text=text[:10000],
        )

    def _parse_qif_transaction(self, txn_data: dict) -> Transaction | None:
        """Parse a QIF transaction record.

        Args:
            txn_data: Dict of QIF fields

        Returns:
            Transaction or None
        """
        # Parse date
        date_str = txn_data.get("date")
        if not date_str:
            return None

        parsed_date = self._parse_qif_date(date_str)
        if not parsed_date:
            return None

        # Parse amount
        amount_str = txn_data.get("amount", "0")
        amount = self._parse_amount(amount_str)
        if amount is None:
            return None

        # Get description
        description = txn_data.get("payee", "") or txn_data.get("memo", "")
        if not description:
            description = txn_data.get("category", "Unknown")

        # Determine type
        transaction_type = TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT

        return Transaction(
            date=parsed_date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            reference=txn_data.get("number"),
            category=txn_data.get("category"),
            raw_data=txn_data,
        )

    def _parse_qif_date(self, date_str: str) -> date | None:
        """Parse QIF date format.

        QIF uses MM/DD/YY or MM/DD/YYYY format.
        Some files use MM-DD-YYYY.

        Args:
            date_str: Date string

        Returns:
            Parsed date or None
        """
        # Normalize separators
        date_str = date_str.replace("-", "/").replace("'", "/")

        # QIF date patterns
        patterns = [
            (r"(\d{1,2})/(\d{1,2})/(\d{2,4})", "%m/%d/%Y"),  # MM/DD/YYYY
            (r"(\d{1,2})/(\d{1,2})'(\d{2})", "%m/%d/%y"),  # MM/DD'YY (old format)
        ]

        for pattern, fmt in patterns:
            match = re.match(pattern, date_str)
            if match:
                try:
                    # Normalize the date string
                    parts = match.groups()
                    if len(parts) == 3:
                        month, day, year = parts
                        if len(year) == 2:
                            year = "20" + year if int(year) < 50 else "19" + year
                        normalized = f"{month.zfill(2)}/{day.zfill(2)}/{year}"
                        return datetime.strptime(normalized, "%m/%d/%Y").date()
                except ValueError:
                    continue

        # Try generic parsing
        return self._parse_date(date_str)
