"""Category ORM model for organizing subscriptions.

This module defines the SQLAlchemy ORM model for user-defined categories,
allowing users to organize subscriptions with custom colors, icons, and budgets.

The model uses async-compatible SQLAlchemy 2.0 patterns and follows
the existing codebase conventions for Money Flow.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Category(Base):
    """Category model for organizing subscriptions.

    Represents a user-defined category with custom styling and optional
    budget tracking. Categories can be used to group subscriptions
    for better organization and spending analysis.

    Attributes:
        id: UUID primary key (auto-generated).
        name: Category display name (e.g., "Entertainment", "Utilities").
        description: Optional description of the category.
        color: Category color in hex format for UI display.
        icon: Icon name or emoji for the category.
        budget_amount: Optional monthly budget limit for this category.
        budget_currency: Currency for the budget (default: GBP).
        is_active: Whether category is currently active.
        sort_order: Display order in lists.
        user_id: Foreign key to owning user.
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.
        subscriptions: Relationship to subscriptions in this category.

    Example:
        >>> category = Category(
        ...     name="Entertainment",
        ...     color="#8B5CF6",
        ...     icon="🎬",
        ...     budget_amount=Decimal("50.00"),
        ...     user_id="user-uuid",
        ... )
        >>> category.name
        'Entertainment'

    Notes:
        - Categories are user-scoped (each user has their own categories)
        - Budget tracking is optional but useful for spending alerts
        - System categories (like "Uncategorized") can be created with is_system=True
    """

    __tablename__ = "categories"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6366F1")  # Default indigo
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Emoji or icon name

    # Budget settings (optional)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(3), default="GBP")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # System categories can't be deleted
    sort_order: Mapped[int] = mapped_column(default=0)

    # User ownership
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="categories", lazy="selectin"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="category_rel", lazy="selectin"
    )

    def __repr__(self) -> str:
        """Return string representation of category.

        Returns:
            Debug-friendly string with name and color.

        Example:
            >>> str(category)
            "<Category(name='Entertainment', color='#8B5CF6')>"
        """
        return f"<Category(name='{self.name}', color='{self.color}')>"

    @property
    def is_over_budget(self) -> bool | None:
        """Check if category spending exceeds budget.

        Note: This property requires the subscriptions relationship to be loaded
        and should be used with care due to potential N+1 queries.

        Returns:
            True if over budget, False if under, None if no budget set.
        """
        if self.budget_amount is None:
            return None
        # Calculate total from active subscriptions
        # This is a simplified check - actual implementation would need
        # to convert currencies and calculate monthly equivalents
        return False  # Placeholder - actual logic in service layer
