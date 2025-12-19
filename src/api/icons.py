"""Icon API endpoints for fetching and managing icons.

This module provides endpoints for:
- Fetching icons from external sources
- Searching cached icons
- Bulk icon operations
- Icon cache statistics

Routes:
    GET /api/v1/icons/{service_name} - Get icon for a service
    POST /api/v1/icons/search - Search for icons
    POST /api/v1/icons/bulk - Bulk fetch icons
    GET /api/v1/icons/stats - Get cache statistics
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.user import User
from src.schemas.icon import (
    IconBulkFetchRequest,
    IconBulkResponse,
    IconFetchRequest,
    IconGenerateRequest,
    IconResponse,
    IconSearchRequest,
    IconSearchResponse,
    IconStatsResponse,
)
from src.services.icon_service import IconService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{service_name}", response_model=IconResponse | None)
async def get_icon(
    service_name: str,
    force_refresh: bool = Query(False, description="Force refresh from external source"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconResponse | None:
    """Get icon for a service.

    Checks cache first, then fetches from external sources if needed.

    Args:
        service_name: Service name to get icon for.
        force_refresh: Force refresh from external source.

    Returns:
        IconResponse or None if not found.
    """
    service = IconService(db)
    try:
        icon = await service.get_icon(
            service_name=service_name,
            user_id=current_user.id,
            force_refresh=force_refresh,
        )
        if icon:
            logger.debug(f"Found icon for {service_name}: {icon.source}")
        return icon
    finally:
        await service.close()


@router.post("/fetch", response_model=IconResponse | None)
async def fetch_icon(
    data: IconFetchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconResponse | None:
    """Fetch icon with specific sources.

    Args:
        data: Fetch request with service name and sources to try.

    Returns:
        IconResponse or None if not found.
    """
    service = IconService(db)
    try:
        icon = await service.get_icon(
            service_name=data.service_name,
            user_id=current_user.id,
            force_refresh=data.force_refresh,
        )
        return icon
    finally:
        await service.close()


@router.post("/generate", response_model=IconResponse | None)
async def generate_icon(
    data: IconGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconResponse | None:
    """Generate an icon using AI.

    Uses Claude to generate an SVG icon for a service when no
    external icon source is available.

    Args:
        data: Generation request with service name, style, and color.

    Returns:
        IconResponse with generated icon or None if generation fails.
    """
    service = IconService(db)
    try:
        icon = await service.generate_ai_icon(
            service_name=data.service_name,
            style=data.style,
            primary_color=data.brand_color,
            user_id=current_user.id,
        )
        if icon:
            logger.info(f"Generated AI icon for {data.service_name}")
        else:
            logger.warning(f"Failed to generate icon for {data.service_name}")
        return icon
    finally:
        await service.close()


@router.post("/search", response_model=IconSearchResponse)
async def search_icons(
    data: IconSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconSearchResponse:
    """Search for icons by name.

    Args:
        data: Search request with query and filters.

    Returns:
        IconSearchResponse with matching icons.
    """
    service = IconService(db)
    try:
        return await service.search_icons(
            query=data.query,
            category=data.category,
            include_ai=data.include_ai,
        )
    finally:
        await service.close()


@router.post("/bulk", response_model=IconBulkResponse)
async def bulk_fetch_icons(
    data: IconBulkFetchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconBulkResponse:
    """Fetch icons for multiple services.

    Args:
        data: Bulk fetch request with service names.

    Returns:
        IconBulkResponse with found icons and missing services.
    """
    if len(data.service_names) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 services per bulk request",
        )

    service = IconService(db)
    try:
        return await service.bulk_fetch(
            service_names=data.service_names,
            sources=data.sources,
        )
    finally:
        await service.close()


@router.get("/stats", response_model=IconStatsResponse)
async def get_icon_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IconStatsResponse:
    """Get icon cache statistics.

    Returns:
        IconStatsResponse with cache metrics.
    """
    service = IconService(db)
    try:
        return await service.get_stats()
    finally:
        await service.close()
