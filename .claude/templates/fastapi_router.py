"""[Resource] API endpoints.

This module defines REST API endpoints for [resource] operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
)
from src.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/[resources]", tags=["[resources]"])


@router.get("/", response_model=List[SubscriptionResponse])
async def list_[resources](
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all [resources] with optional filters.

    Args:
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        is_active: Filter by active status if provided.
        db: Database session dependency.

    Returns:
        List of [resources].
    """
    service = SubscriptionService(db)
    [resources] = await service.list(skip=skip, limit=limit, is_active=is_active)
    return [resources]


@router.get("/{[resource]_id}", response_model=SubscriptionResponse)
async def get_[resource](
    [resource]_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single [resource] by ID.

    Args:
        [resource]_id: Unique identifier.
        db: Database session dependency.

    Returns:
        [Resource] details.

    Raises:
        HTTPException: 404 if [resource] not found.
    """
    service = SubscriptionService(db)
    [resource] = await service.get_by_id([resource]_id)

    if not [resource]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"[Resource] with id {[resource]_id} not found",
        )

    return [resource]


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_[resource](
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new [resource].

    Args:
        data: [Resource] creation data.
        db: Database session dependency.

    Returns:
        Created [resource].

    Raises:
        HTTPException: 400 if validation fails.
    """
    service = SubscriptionService(db)
    [resource] = await service.create(data)
    return [resource]


@router.put("/{[resource]_id}", response_model=SubscriptionResponse)
async def update_[resource](
    [resource]_id: str,
    data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing [resource].

    Args:
        [resource]_id: Unique identifier.
        data: Update data.
        db: Database session dependency.

    Returns:
        Updated [resource].

    Raises:
        HTTPException: 404 if [resource] not found.
    """
    service = SubscriptionService(db)
    [resource] = await service.update([resource]_id, data)

    if not [resource]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"[Resource] with id {[resource]_id} not found",
        )

    return [resource]


@router.delete("/{[resource]_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_[resource](
    [resource]_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a [resource].

    Args:
        [resource]_id: Unique identifier.
        db: Database session dependency.

    Raises:
        HTTPException: 404 if [resource] not found.
    """
    service = SubscriptionService(db)
    deleted = await service.delete([resource]_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"[Resource] with id {[resource]_id} not found",
        )
