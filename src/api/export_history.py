"""Export history API endpoints.

This module provides endpoints for viewing export history/audit logs.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.export_history import ExportHistory
from src.models.user import User
from src.schemas.export import (
    ExportHistoryListResponse,
    ExportHistoryResponse,
    ExportStatsResponse,
    history_to_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/history", response_model=ExportHistoryListResponse)
async def get_export_history(
    page: int = 1,
    page_size: int = 20,
    export_type: str | None = None,
    export_format: str | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportHistoryListResponse:
    """Get user's export history.

    Returns a paginated list of past export operations.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page (max 100).
        export_type: Filter by type (full_backup, subscriptions, report).
        export_format: Filter by format (json, csv, pdf).
        status_filter: Filter by status (pending, completed, failed).

    Returns:
        ExportHistoryListResponse with paginated history.
    """
    # Validate page size
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    # Build query
    query = select(ExportHistory).where(ExportHistory.user_id == current_user.id)

    # Apply filters
    if export_type:
        query = query.where(ExportHistory.export_type == export_type)
    if export_format:
        query = query.where(ExportHistory.export_format == export_format)
    if status_filter:
        query = query.where(ExportHistory.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(
        query.with_only_columns(ExportHistory.id).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(ExportHistory.created_at.desc())
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return ExportHistoryListResponse(
        items=[ExportHistoryResponse(**history_to_response(item)) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.get("/history/stats", response_model=ExportStatsResponse)
async def get_export_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportStatsResponse:
    """Get export statistics for the user.

    Returns:
        ExportStatsResponse with aggregate statistics.
    """
    # Get all exports for the user
    result = await db.execute(select(ExportHistory).where(ExportHistory.user_id == current_user.id))
    exports = list(result.scalars().all())

    # Calculate stats
    total_exports = len(exports)
    completed_exports = sum(1 for e in exports if e.status == "completed")
    failed_exports = sum(1 for e in exports if e.status == "failed")
    total_bytes = sum(e.file_size or 0 for e in exports)
    total_records = sum(e.record_count or 0 for e in exports)

    # Group by type
    exports_by_type: dict[str, int] = {}
    for export in exports:
        exports_by_type[export.export_type] = exports_by_type.get(export.export_type, 0) + 1

    # Group by format
    exports_by_format: dict[str, int] = {}
    for export in exports:
        exports_by_format[export.export_format] = exports_by_format.get(export.export_format, 0) + 1

    return ExportStatsResponse(
        total_exports=total_exports,
        completed_exports=completed_exports,
        failed_exports=failed_exports,
        total_bytes_exported=total_bytes,
        total_records_exported=total_records,
        exports_by_type=exports_by_type,
        exports_by_format=exports_by_format,
    )


@router.get("/history/{export_id}", response_model=ExportHistoryResponse)
async def get_export_detail(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportHistoryResponse:
    """Get a specific export detail.

    Args:
        export_id: The export ID.

    Returns:
        ExportHistoryResponse with export details.

    Raises:
        HTTPException: If export not found.
    """
    result = await db.execute(
        select(ExportHistory).where(
            ExportHistory.id == export_id,
            ExportHistory.user_id == current_user.id,
        )
    )
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    return ExportHistoryResponse(**history_to_response(export))


@router.delete("/history/{export_id}")
async def delete_export_record(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete an export record from history.

    Args:
        export_id: The export ID to delete.

    Returns:
        Success message.

    Raises:
        HTTPException: If export not found.
    """
    result = await db.execute(
        select(ExportHistory).where(
            ExportHistory.id == export_id,
            ExportHistory.user_id == current_user.id,
        )
    )
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    await db.delete(export)
    await db.commit()

    logger.info(f"Deleted export record {export_id} for user {current_user.id}")

    return {"success": True, "message": "Export record deleted"}


@router.delete("/history")
async def clear_export_history(
    export_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Clear export history.

    Optionally filter by type to clear only specific export types.

    Args:
        export_type: Optional type filter (full_backup, subscriptions, report).

    Returns:
        Success message with count of deleted records.
    """
    query = delete(ExportHistory).where(ExportHistory.user_id == current_user.id)

    if export_type:
        query = query.where(ExportHistory.export_type == export_type)

    result = await db.execute(query)
    await db.commit()

    deleted_count = result.rowcount

    logger.info(
        f"Cleared {deleted_count} export records for user {current_user.id}"
        + (f" (type: {export_type})" if export_type else "")
    )

    return {
        "success": True,
        "message": f"Cleared {deleted_count} export record(s)",
        "deleted_count": deleted_count,
    }
