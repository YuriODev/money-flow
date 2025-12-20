"""Pydantic schemas for bank profile API.

This module provides request/response schemas for:
- Bank profile CRUD operations
- Bank search and filtering
- Bank detection requests
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field


def uuid_to_str(v: Any) -> str:
    """Convert UUID to string."""
    if isinstance(v, UUID):
        return str(v)
    return str(v) if v else ""


UUIDStr = Annotated[str, BeforeValidator(uuid_to_str)]


class CSVMappingSchema(BaseModel):
    """Schema for CSV column mappings."""

    date_columns: list[str] = Field(default_factory=lambda: ["Date"])
    amount_columns: list[str] = Field(default_factory=lambda: ["Amount"])
    description_columns: list[str] = Field(default_factory=lambda: ["Description"])
    balance_columns: list[str] = Field(default_factory=list)
    debit_columns: list[str] = Field(default_factory=list)
    credit_columns: list[str] = Field(default_factory=list)
    reference_columns: list[str] = Field(default_factory=list)
    category_columns: list[str] = Field(default_factory=list)
    date_format: str = Field(default="%Y-%m-%d")
    delimiter: str = Field(default=",")
    encoding: str = Field(default="utf-8")
    skip_rows: int = Field(default=0)
    header_row: int = Field(default=0)


class DetectionPatternsSchema(BaseModel):
    """Schema for bank detection patterns."""

    header_keywords: list[str] = Field(default_factory=list)
    filename_patterns: list[str] = Field(default_factory=list)
    content_patterns: list[str] = Field(default_factory=list)


class BankProfileCreate(BaseModel):
    """Schema for creating a bank profile."""

    name: str = Field(..., min_length=1, max_length=255, description="Bank name")
    slug: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$", description="URL-friendly slug"
    )
    country_code: str = Field(
        ..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="ISO country code"
    )
    currency: str = Field(
        default="GBP", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$", description="ISO currency"
    )
    logo_url: str | None = Field(default=None, description="Bank logo URL")
    website: str | None = Field(default=None, description="Bank website URL")
    csv_mapping: dict[str, Any] = Field(default_factory=dict, description="CSV column mappings")
    detection_patterns: dict[str, Any] = Field(
        default_factory=dict, description="Bank detection patterns"
    )

    model_config = {"json_schema_extra": {"example": {"name": "Example Bank", "slug": "example-bank", "country_code": "GB", "currency": "GBP", "csv_mapping": {"date_columns": ["Date"], "amount_columns": ["Amount"], "description_columns": ["Description"], "date_format": "%d/%m/%Y"}, "detection_patterns": {"header_keywords": ["Example Bank"], "filename_patterns": ["example*.csv"]}}}}


class BankProfileUpdate(BaseModel):
    """Schema for updating a bank profile."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    country_code: str | None = Field(default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    logo_url: str | None = Field(default=None)
    website: str | None = Field(default=None)
    csv_mapping: dict[str, Any] | None = Field(default=None)
    pdf_patterns: dict[str, Any] | None = Field(default=None)
    detection_patterns: dict[str, Any] | None = Field(default=None)
    is_verified: bool | None = Field(default=None)


class BankProfileResponse(BaseModel):
    """Schema for bank profile response."""

    id: UUIDStr
    name: str
    slug: str
    country_code: str
    currency: str
    logo_url: str | None = None
    website: str | None = None
    csv_mapping: dict[str, Any]
    pdf_patterns: dict[str, Any]
    detection_patterns: dict[str, Any]
    is_verified: bool
    usage_count: int
    last_verified: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BankProfileListResponse(BaseModel):
    """Schema for paginated bank list response."""

    banks: list[BankProfileResponse]
    total: int
    limit: int
    offset: int


class BankSearchRequest(BaseModel):
    """Schema for bank search request."""

    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)


class BankDetectRequest(BaseModel):
    """Schema for bank detection request."""

    filename: str | None = Field(default=None, description="Original filename")
    headers: list[str] | None = Field(default=None, description="CSV header row")
    content_sample: str | None = Field(
        default=None, max_length=10000, description="First 10KB of file content"
    )


class BankDetectResponse(BaseModel):
    """Schema for bank detection response."""

    detected: bool
    bank: BankProfileResponse | None = None
    confidence: str = Field(
        default="medium", description="Detection confidence: low, medium, high"
    )


class CountryBanksResponse(BaseModel):
    """Schema for country banks count."""

    country_code: str
    count: int


class BankSeedResponse(BaseModel):
    """Schema for bank seeding response."""

    seeded: int
    message: str


class BankSuggestRequest(BaseModel):
    """Schema for user-suggested bank format."""

    name: str = Field(..., min_length=1, max_length=255)
    country_code: str = Field(..., min_length=2, max_length=2)
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    website: str | None = None
    csv_sample_headers: list[str] | None = None
    notes: str | None = Field(default=None, max_length=1000)
