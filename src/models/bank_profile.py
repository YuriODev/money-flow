"""BankProfile model for dynamic bank statement parsing configuration.

This module provides:
- BankProfile: SQLAlchemy model for storing bank CSV/PDF mapping configurations
- Dynamic column mappings stored as JSON for flexibility
- Auto-detection patterns for identifying banks from file content
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class BankProfile(Base):
    """Bank profile with CSV/PDF parsing configuration.

    Stores bank-specific column mappings and detection patterns
    to enable dynamic parsing of bank statements.

    Attributes:
        id: Unique identifier (UUID)
        name: Human-readable bank name (e.g., "Monzo", "Chase Bank")
        slug: URL-friendly identifier (e.g., "monzo", "chase")
        country_code: ISO 3166-1 alpha-2 country code (e.g., "GB", "US", "BR")
        currency: Default currency for this bank (ISO 4217)
        logo_url: URL to bank logo image
        website: Bank website URL
        csv_mapping: JSON with column name mappings for CSV parsing
        pdf_patterns: JSON with patterns for PDF text extraction
        detection_patterns: JSON with patterns to auto-detect this bank
        is_verified: Admin-verified bank profile
        usage_count: Number of times this profile was used
        last_verified: Last admin verification date
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "bank_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")

    # Optional metadata
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # CSV column mappings (JSON)
    # Structure:
    # {
    #   "date_columns": ["Date", "Transaction Date"],
    #   "amount_columns": ["Amount", "Value"],
    #   "description_columns": ["Description", "Memo"],
    #   "balance_columns": ["Balance", "Running Balance"],
    #   "debit_columns": ["Debit", "Money Out"],
    #   "credit_columns": ["Credit", "Money In"],
    #   "reference_columns": ["Reference", "Ref"],
    #   "category_columns": ["Category", "Type"],
    #   "date_format": "%d/%m/%Y",
    #   "delimiter": ",",
    #   "encoding": "utf-8",
    #   "skip_rows": 0,
    #   "header_row": 0
    # }
    csv_mapping: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # PDF extraction patterns (JSON)
    # Structure:
    # {
    #   "table_keywords": ["Date", "Description", "Amount"],
    #   "amount_patterns": ["£[\\d,]+\\.\\d{2}"],
    #   "date_patterns": ["\\d{2}/\\d{2}/\\d{4}"],
    #   "exclude_patterns": ["Page \\d+", "Statement Date"]
    # }
    pdf_patterns: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Detection patterns for auto-identifying bank from file (JSON)
    # Structure:
    # {
    #   "header_keywords": ["Monzo", "Account Statement"],
    #   "filename_patterns": ["monzo_*.csv", "statement_*.csv"],
    #   "content_patterns": ["Account: \\d{8}", "Sort Code: \\d{2}-\\d{2}-\\d{2}"]
    # }
    detection_patterns: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Metadata
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<BankProfile {self.slug} ({self.name}, {self.country_code})>"

    # CSV mapping helper methods

    def get_date_columns(self) -> list[str]:
        """Get possible date column names."""
        return self.csv_mapping.get("date_columns", ["Date"])

    def get_amount_columns(self) -> list[str]:
        """Get possible amount column names."""
        return self.csv_mapping.get("amount_columns", ["Amount"])

    def get_description_columns(self) -> list[str]:
        """Get possible description column names."""
        return self.csv_mapping.get("description_columns", ["Description"])

    def get_balance_columns(self) -> list[str]:
        """Get possible balance column names."""
        return self.csv_mapping.get("balance_columns", [])

    def get_debit_columns(self) -> list[str]:
        """Get possible debit column names."""
        return self.csv_mapping.get("debit_columns", [])

    def get_credit_columns(self) -> list[str]:
        """Get possible credit column names."""
        return self.csv_mapping.get("credit_columns", [])

    def get_date_format(self) -> str:
        """Get expected date format."""
        return self.csv_mapping.get("date_format", "%Y-%m-%d")

    def get_delimiter(self) -> str:
        """Get CSV delimiter."""
        return self.csv_mapping.get("delimiter", ",")

    def get_encoding(self) -> str:
        """Get file encoding."""
        return self.csv_mapping.get("encoding", "utf-8")

    def get_skip_rows(self) -> int:
        """Get number of rows to skip before header."""
        return self.csv_mapping.get("skip_rows", 0)

    def get_header_row(self) -> int:
        """Get header row index (after skip_rows)."""
        return self.csv_mapping.get("header_row", 0)

    # Detection helper methods

    def get_header_keywords(self) -> list[str]:
        """Get keywords to look for in CSV headers."""
        return self.detection_patterns.get("header_keywords", [])

    def get_filename_patterns(self) -> list[str]:
        """Get filename patterns for detection."""
        return self.detection_patterns.get("filename_patterns", [])

    def get_content_patterns(self) -> list[str]:
        """Get content patterns for detection."""
        return self.detection_patterns.get("content_patterns", [])

    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1

    def mark_verified(self) -> None:
        """Mark profile as admin-verified."""
        self.is_verified = True
        self.last_verified = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "country_code": self.country_code,
            "currency": self.currency,
            "logo_url": self.logo_url,
            "website": self.website,
            "csv_mapping": self.csv_mapping,
            "pdf_patterns": self.pdf_patterns,
            "detection_patterns": self.detection_patterns,
            "is_verified": self.is_verified,
            "usage_count": self.usage_count,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Default CSV mapping template for new banks
DEFAULT_CSV_MAPPING: dict[str, Any] = {
    "date_columns": ["Date", "Transaction Date", "Posting Date"],
    "amount_columns": ["Amount", "Value", "Sum"],
    "description_columns": ["Description", "Memo", "Payee", "Details"],
    "balance_columns": ["Balance", "Running Balance"],
    "debit_columns": [],
    "credit_columns": [],
    "reference_columns": ["Reference", "Ref"],
    "category_columns": ["Category", "Type"],
    "date_format": "%Y-%m-%d",
    "delimiter": ",",
    "encoding": "utf-8",
    "skip_rows": 0,
    "header_row": 0,
}

# Default detection patterns template
DEFAULT_DETECTION_PATTERNS: dict[str, Any] = {
    "header_keywords": [],
    "filename_patterns": [],
    "content_patterns": [],
}
