"""Category API endpoints.

This module provides REST API endpoints for managing user-defined categories
for organizing subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.core.dependencies import get_db
from src.models.user import User
from src.schemas.category import (
    AssignCategoryRequest,
    BulkAssignCategoryRequest,
    CategoryBudgetSummary,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithStats,
)
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def _get_service(db: AsyncSession, user: User) -> CategoryService:
    """Create a CategoryService instance for the current user."""
    return CategoryService(db, user_id=user.id)


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List categories",
    description="Get all categories for the current user.",
)
@limiter.limit(rate_limit_get)
async def list_categories(
    request: Request,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CategoryResponse]:
    """List all categories for the current user."""
    service = _get_service(db, current_user)
    categories = await service.get_all(include_inactive=include_inactive)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get(
    "/with-stats",
    response_model=list[CategoryWithStats],
    summary="List categories with stats",
    description="Get all categories with subscription counts and spending totals.",
)
@limiter.limit(rate_limit_get)
async def list_categories_with_stats(
    request: Request,
    currency: str = "GBP",
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CategoryWithStats]:
    """List categories with spending statistics."""
    service = _get_service(db, current_user)
    return await service.get_with_stats(
        target_currency=currency,
        include_inactive=include_inactive,
    )


@router.get(
    "/budget-summary",
    response_model=CategoryBudgetSummary,
    summary="Get budget summary",
    description="Get summary of all category budgets and spending.",
)
@limiter.limit(rate_limit_get)
async def get_budget_summary(
    request: Request,
    currency: str = "GBP",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CategoryBudgetSummary:
    """Get budget summary across all categories."""
    service = _get_service(db, current_user)
    categories = await service.get_with_stats(target_currency=currency)

    total_budgeted = sum(cat.budget_amount for cat in categories if cat.budget_amount)
    total_spent = sum(cat.total_monthly for cat in categories)
    categories_over_budget = sum(1 for cat in categories if cat.is_over_budget)

    return CategoryBudgetSummary(
        categories=categories,
        total_budgeted=total_budgeted,
        total_spent=total_spent,
        categories_over_budget=categories_over_budget,
    )


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new category.",
)
@limiter.limit(rate_limit_write)
async def create_category(
    request: Request,
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CategoryResponse:
    """Create a new category."""
    service = _get_service(db, current_user)

    # Check for duplicate name
    existing = await service.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{data.name}' already exists",
        )

    category = await service.create(data)
    await db.commit()
    return CategoryResponse.model_validate(category)


@router.post(
    "/defaults",
    response_model=list[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create default categories",
    description="Create a set of default categories for a new user.",
)
@limiter.limit(rate_limit_write)
async def create_default_categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CategoryResponse]:
    """Create default categories."""
    service = _get_service(db, current_user)

    # Check if user already has categories
    existing = await service.get_all(include_inactive=True)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has categories",
        )

    categories = await service.create_default_categories()
    await db.commit()
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category",
    description="Get a category by ID.",
)
@limiter.limit(rate_limit_get)
async def get_category(
    request: Request,
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CategoryResponse:
    """Get a category by ID."""
    service = _get_service(db, current_user)
    category = await service.get_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    return CategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category",
    description="Update a category's details.",
)
@limiter.limit(rate_limit_write)
async def update_category(
    request: Request,
    category_id: str,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CategoryResponse:
    """Update a category."""
    service = _get_service(db, current_user)

    # Check for duplicate name if name is being changed
    if data.name:
        existing = await service.get_by_name(data.name)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{data.name}' already exists",
            )

    category = await service.update(category_id, data)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    await db.commit()
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Delete a category. Subscriptions will be unassigned.",
)
@limiter.limit(rate_limit_write)
async def delete_category(
    request: Request,
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a category."""
    service = _get_service(db, current_user)
    deleted = await service.delete(category_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found or is a system category",
        )

    await db.commit()


@router.post(
    "/assign",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assign category",
    description="Assign a subscription to a category.",
)
@limiter.limit(rate_limit_write)
async def assign_category(
    request: Request,
    data: AssignCategoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Assign a subscription to a category."""
    service = _get_service(db, current_user)
    success = await service.assign_subscription(data.subscription_id, data.category_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription or category not found",
        )

    await db.commit()


@router.post(
    "/bulk-assign",
    summary="Bulk assign category",
    description="Assign multiple subscriptions to a category.",
)
@limiter.limit(rate_limit_write)
async def bulk_assign_category(
    request: Request,
    data: BulkAssignCategoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Bulk assign subscriptions to a category."""
    service = _get_service(db, current_user)
    count = await service.bulk_assign_subscriptions(data.subscription_ids, data.category_id)
    await db.commit()
    return {"updated": count}
