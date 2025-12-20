"""Pydantic schemas for statement import API.

This module provides request/response schemas for:
- Statement file upload
- Import job status and management
- Detected subscription review and confirmation
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field


def uuid_to_str(v: Any) -> str:
    """Convert UUID to string."""
    if isinstance(v, UUID):
        return str(v)
    return str(v) if v else ""


UUIDStr = Annotated[str, BeforeValidator(uuid_to_str)]


# ============================================================================
# Import Job Schemas
# ============================================================================


class ImportJobCreate(BaseModel):
    """Schema for creating an import job (internal use)."""

    filename: str
    file_type: str
    file_size: int | None = None
    bank_id: str | None = None
    bank_name: str | None = None
    currency: str = "GBP"


class ImportJobResponse(BaseModel):
    """Schema for import job response."""

    id: UUIDStr
    filename: str
    file_type: str
    file_size: int | None = None
    bank_id: UUIDStr | None = None
    bank_name: str | None = None
    currency: str

    status: str
    error_message: str | None = None

    total_transactions: int
    detected_count: int
    imported_count: int
    skipped_count: int
    duplicate_count: int

    period_start: datetime | None = None
    period_end: datetime | None = None

    created_at: datetime
    processing_started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ImportJobListResponse(BaseModel):
    """Schema for paginated import job list."""

    jobs: list[ImportJobResponse]
    total: int
    limit: int
    offset: int


class ImportJobStatusResponse(BaseModel):
    """Schema for import job status check."""

    id: UUIDStr
    status: str
    detected_count: int
    error_message: str | None = None
    is_ready: bool = False


# ============================================================================
# Detected Subscription Schemas
# ============================================================================


class DetectedSubscriptionResponse(BaseModel):
    """Schema for detected subscription response."""

    id: UUIDStr
    job_id: UUIDStr

    name: str
    normalized_name: str
    amount: Decimal
    currency: str

    frequency: str
    payment_type: str

    confidence: float
    amount_variance: float
    transaction_count: int

    first_seen: datetime | None = None
    last_seen: datetime | None = None

    status: str
    is_selected: bool

    duplicate_of_id: UUIDStr | None = None
    duplicate_similarity: float | None = None

    sample_descriptions: list[str] | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class DetectedSubscriptionUpdate(BaseModel):
    """Schema for updating detected subscription status."""

    is_selected: bool | None = None
    status: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = None
    payment_type: str | None = None


class BulkUpdateDetectedRequest(BaseModel):
    """Schema for bulk updating detected subscriptions."""

    subscription_ids: list[str]
    is_selected: bool | None = None
    status: str | None = None


class BulkUpdateDetectedResponse(BaseModel):
    """Response for bulk update operation."""

    updated_count: int
    subscription_ids: list[str]


# ============================================================================
# Import Confirmation Schemas
# ============================================================================


class ConfirmImportRequest(BaseModel):
    """Schema for confirming subscription import."""

    subscription_ids: list[str] = Field(
        default_factory=list,
        description="IDs of detected subscriptions to import. Empty means import all selected.",
    )
    card_id: str | None = Field(
        default=None,
        description="Payment card to assign to imported subscriptions",
    )
    category_id: str | None = Field(
        default=None,
        description="Category to assign to imported subscriptions",
    )


class ConfirmImportResponse(BaseModel):
    """Response for import confirmation."""

    job_id: UUIDStr
    imported_count: int
    skipped_count: int
    duplicate_count: int
    created_subscription_ids: list[str]


# ============================================================================
# Statement Upload Schemas
# ============================================================================


class StatementUploadResponse(BaseModel):
    """Response for statement file upload."""

    job_id: UUIDStr
    filename: str
    file_type: str
    status: str
    message: str


class StatementAnalysisRequest(BaseModel):
    """Request to analyze an already uploaded statement."""

    job_id: str
    bank_id: str | None = None
    use_ai: bool = True
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# ============================================================================
# Preview Schemas
# ============================================================================


class ImportPreviewResponse(BaseModel):
    """Preview of what will be imported."""

    job: ImportJobResponse
    detected_subscriptions: list[DetectedSubscriptionResponse]
    summary: ImportPreviewSummary


class ImportPreviewSummary(BaseModel):
    """Summary statistics for import preview."""

    total_detected: int
    selected_count: int
    duplicate_count: int
    high_confidence_count: int
    low_confidence_count: int
    total_monthly_amount: Decimal
    currencies: list[str]
    payment_types: dict[str, int]
    frequencies: dict[str, int]


# ============================================================================
# Duplicate Detection Schemas
# ============================================================================


class DuplicateCheckRequest(BaseModel):
    """Request to check for duplicates."""

    job_id: str
    detected_subscription_id: str | None = None


class DuplicateMatch(BaseModel):
    """A potential duplicate match."""

    detected_id: UUIDStr
    detected_name: str
    existing_id: UUIDStr
    existing_name: str
    similarity: float
    match_reasons: list[str]


class DuplicateCheckResponse(BaseModel):
    """Response for duplicate check."""

    duplicates: list[DuplicateMatch]
    total_matches: int


class ResolveDuplicateRequest(BaseModel):
    """Request to resolve a duplicate."""

    detected_id: str
    action: str = Field(
        ...,
        pattern="^(skip|import_new|merge)$",
        description="Action: skip, import_new, or merge",
    )
    merge_with_id: str | None = Field(
        default=None,
        description="Existing subscription ID to merge with (required for merge action)",
    )


class ResolveDuplicateResponse(BaseModel):
    """Response for duplicate resolution."""

    detected_id: UUIDStr
    action: str
    result: str
    subscription_id: UUIDStr | None = None
