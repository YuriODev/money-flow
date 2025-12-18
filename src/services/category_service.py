"""Category service for managing user-defined categories.

This module provides business logic for category CRUD operations,
budget tracking, and subscription categorization.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.subscription import Subscription
from src.schemas.category import CategoryCreate, CategoryUpdate, CategoryWithStats
from src.services.currency_service import CurrencyService


class CategoryService:
    """Service for managing categories.

    Provides CRUD operations for categories with user ownership,
    budget tracking, and subscription statistics.

    Attributes:
        db: Async database session.
        user_id: ID of the user who owns the categories.
        currency_service: Service for currency conversion (optional).

    Example:
        >>> service = CategoryService(db, user_id="user-uuid")
        >>> categories = await service.get_all()
        >>> category = await service.create(CategoryCreate(name="Entertainment"))
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: str,
        currency_service: CurrencyService | None = None,
    ) -> None:
        """Initialize category service.

        Args:
            db: Async database session.
            user_id: ID of the user who owns the categories.
            currency_service: Optional currency conversion service.
        """
        self.db = db
        self.user_id = user_id
        self.currency_service = currency_service or CurrencyService()

    async def get_all(self, include_inactive: bool = False) -> Sequence[Category]:
        """Get all categories for the user.

        Args:
            include_inactive: Whether to include inactive categories.

        Returns:
            List of categories ordered by sort_order.
        """
        query = select(Category).where(Category.user_id == self.user_id)

        if not include_inactive:
            query = query.where(Category.is_active == True)  # noqa: E712

        query = query.order_by(Category.sort_order, Category.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, category_id: str) -> Category | None:
        """Get a category by ID.

        Args:
            category_id: Category UUID.

        Returns:
            Category if found and owned by user, None otherwise.
        """
        query = select(Category).where(
            Category.id == category_id,
            Category.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        """Get a category by name.

        Args:
            name: Category name (case-insensitive).

        Returns:
            Category if found, None otherwise.
        """
        query = select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: CategoryCreate) -> Category:
        """Create a new category.

        Args:
            data: Category creation data.

        Returns:
            Created category.
        """
        category = Category(
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            budget_amount=data.budget_amount,
            budget_currency=data.budget_currency,
            sort_order=data.sort_order,
            user_id=self.user_id,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: str, data: CategoryUpdate) -> Category | None:
        """Update a category.

        Args:
            category_id: Category UUID.
            data: Update data (partial).

        Returns:
            Updated category, or None if not found.
        """
        category = await self.get_by_id(category_id)
        if not category:
            return None

        # Prevent editing system categories
        if category.is_system:
            # Allow only color and icon changes for system categories
            update_data = data.model_dump(exclude_unset=True)
            allowed_fields = {"color", "icon"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        else:
            update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(category, key, value)

        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: str) -> bool:
        """Delete a category.

        Subscriptions in this category will have their category_id set to NULL.

        Args:
            category_id: Category UUID.

        Returns:
            True if deleted, False if not found or is system category.
        """
        category = await self.get_by_id(category_id)
        if not category:
            return False

        # Prevent deleting system categories
        if category.is_system:
            return False

        # Unassign subscriptions from this category
        await self.db.execute(
            update(Subscription)
            .where(Subscription.category_id == category_id)
            .values(category_id=None)
        )

        await self.db.delete(category)
        await self.db.flush()
        return True

    async def get_with_stats(
        self,
        target_currency: str = "GBP",
        include_inactive: bool = False,
    ) -> list[CategoryWithStats]:
        """Get all categories with spending statistics.

        Args:
            target_currency: Currency for totals.
            include_inactive: Whether to include inactive categories.

        Returns:
            List of categories with subscription counts and spending totals.
        """
        categories = await self.get_all(include_inactive=include_inactive)
        result = []

        for category in categories:
            # Get subscription stats for this category
            query = select(
                func.count(Subscription.id).label("count"),
                func.coalesce(func.sum(Subscription.amount), 0).label("total"),
            ).where(
                Subscription.category_id == category.id,
                Subscription.is_active == True,  # noqa: E712
                Subscription.user_id == self.user_id,
            )
            result_row = await self.db.execute(query)
            stats = result_row.first()

            subscription_count = stats.count if stats else 0
            total_amount = Decimal(str(stats.total)) if stats else Decimal("0")

            # Convert to target currency if needed
            # Note: This is simplified - actual implementation would need
            # to sum per-subscription with their individual currencies
            total_monthly = total_amount

            # Calculate budget stats
            budget_used_percentage = None
            is_over_budget = None
            if category.budget_amount and category.budget_amount > 0:
                budget_used_percentage = float((total_monthly / category.budget_amount) * 100)
                is_over_budget = total_monthly > category.budget_amount

            result.append(
                CategoryWithStats(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    color=category.color,
                    icon=category.icon,
                    budget_amount=category.budget_amount,
                    budget_currency=category.budget_currency,
                    sort_order=category.sort_order,
                    is_active=category.is_active,
                    is_system=category.is_system,
                    user_id=category.user_id,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                    subscription_count=subscription_count,
                    total_monthly=total_monthly,
                    budget_used_percentage=budget_used_percentage,
                    is_over_budget=is_over_budget,
                )
            )

        return result

    async def assign_subscription(
        self,
        subscription_id: str,
        category_id: str | None,
    ) -> bool:
        """Assign a subscription to a category.

        Args:
            subscription_id: Subscription UUID.
            category_id: Category UUID (None to unassign).

        Returns:
            True if assignment successful, False if subscription not found.
        """
        # Verify the subscription belongs to the user
        query = select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return False

        # Verify category belongs to user (if assigning)
        if category_id:
            category = await self.get_by_id(category_id)
            if not category:
                return False

        subscription.category_id = category_id
        await self.db.flush()
        return True

    async def bulk_assign_subscriptions(
        self,
        subscription_ids: list[str],
        category_id: str | None,
    ) -> int:
        """Assign multiple subscriptions to a category.

        Args:
            subscription_ids: List of subscription UUIDs.
            category_id: Category UUID (None to unassign).

        Returns:
            Number of subscriptions updated.
        """
        # Verify category belongs to user (if assigning)
        if category_id:
            category = await self.get_by_id(category_id)
            if not category:
                return 0

        # Update only subscriptions owned by the user
        result = await self.db.execute(
            update(Subscription)
            .where(
                Subscription.id.in_(subscription_ids),
                Subscription.user_id == self.user_id,
            )
            .values(category_id=category_id)
        )
        await self.db.flush()
        return result.rowcount

    async def create_default_categories(self) -> list[Category]:
        """Create default categories for a new user.

        Creates a set of common categories to help users get started.

        Returns:
            List of created categories.
        """
        default_categories = [
            {"name": "Entertainment", "color": "#8B5CF6", "icon": "🎬"},
            {"name": "Utilities", "color": "#F59E0B", "icon": "⚡"},
            {"name": "Housing", "color": "#10B981", "icon": "🏠"},
            {"name": "Transportation", "color": "#3B82F6", "icon": "🚗"},
            {"name": "Health & Fitness", "color": "#EF4444", "icon": "💪"},
            {"name": "Food & Dining", "color": "#EC4899", "icon": "🍔"},
            {"name": "Shopping", "color": "#06B6D4", "icon": "🛍️"},
            {"name": "Education", "color": "#6366F1", "icon": "📚"},
        ]

        created = []
        for i, cat_data in enumerate(default_categories):
            category = Category(
                name=cat_data["name"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                sort_order=i,
                user_id=self.user_id,
            )
            self.db.add(category)
            created.append(category)

        await self.db.flush()
        return created
