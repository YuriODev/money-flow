"""Pydantic schemas for export history.

This module defines request/response schemas for export history and audit log endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExportHistoryResponse(BaseModel):
    """Schema for export history response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    export_type: str
    export_format: str
    filename: str | None = None
    file_size: int | None = None
    record_count: int | None = None
    status: str
    error_message: str | None = None
    ip_address: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None


class ExportHistoryListResponse(BaseModel):
    """Schema for paginated export history list."""

    items: list[ExportHistoryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ExportStatsResponse(BaseModel):
    """Schema for export statistics."""

    total_exports: int
    completed_exports: int
    failed_exports: int
    total_bytes_exported: int
    total_records_exported: int
    exports_by_type: dict[str, int]
    exports_by_format: dict[str, int]


def history_to_response(history) -> dict:
    """Convert ExportHistory model to response dict.

    Args:
        history: ExportHistory model instance.

    Returns:
        Dict suitable for ExportHistoryResponse.
    """
    return {
        "id": history.id,
        "user_id": history.user_id,
        "export_type": history.export_type,
        "export_format": history.export_format,
        "filename": history.filename,
        "file_size": history.file_size,
        "record_count": history.record_count,
        "status": history.status,
        "error_message": history.error_message,
        "ip_address": history.ip_address,
        "created_at": history.created_at,
        "completed_at": history.completed_at,
        "duration_seconds": history.duration_seconds,
    }
