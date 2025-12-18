"""Pydantic schemas for Category.

This module defines Pydantic v2 schemas for request/response validation
of category data for organizing subscriptions.

Security:
    - Names are sanitized to prevent XSS
    - Colors are validated for hex format
    - Budget amounts are validated for reasonable ranges
    - UUIDs are validated for proper format
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.security.validators import (
    sanitize_name,
    validate_currency,
    validate_safe_text,
    validate_uuid,
)


class CategoryBase(BaseModel):
    """Base schema for category data.

    Attributes:
        name: Category display name (e.g., "Entertainment", "Utilities").
        description: Optional description of the category.
        color: Category color in hex format for UI display.
        icon: Icon name or emoji for the category.
        budget_amount: Optional monthly budget limit.
        budget_currency: Currency for the budget.
        sort_order: Display order in lists.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(
        default=None, max_length=500, description="Category description"
    )
    color: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color")
    icon: str | None = Field(default=None, max_length=50, description="Icon name or emoji")
    budget_amount: Decimal | None = Field(
        default=None, ge=0, le=1000000, description="Monthly budget"
    )
    budget_currency: str = Field(
        default="GBP", min_length=3, max_length=3, description="Budget currency"
    )
    sort_order: int = Field(default=0, ge=0, description="Display order")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize name to prevent XSS."""
        return sanitize_name(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description doesn't contain dangerous content."""
        if v is None:
            return v
        return validate_safe_text(v)

    @field_validator("budget_currency")
    @classmethod
    def validate_budget_currency(cls, v: str) -> str:
        """Validate currency against allowed list."""
        return validate_currency(v)


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(default=None, max_length=50)
    budget_amount: Decimal | None = Field(default=None, ge=0, le=1000000)
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Sanitize name to prevent XSS."""
        if v is None:
            return v
        return sanitize_name(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description doesn't contain dangerous content."""
        if v is None:
            return v
        return validate_safe_text(v)

    @field_validator("budget_currency")
    @classmethod
    def validate_budget_currency(cls, v: str | None) -> str | None:
        """Validate currency against allowed list."""
        if v is None:
            return v
        return validate_currency(v)


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Category UUID")
    is_active: bool = Field(..., description="Active status")
    is_system: bool = Field(default=False, description="System category flag")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CategoryWithStats(CategoryResponse):
    """Category response with spending statistics.

    Attributes:
        subscription_count: Number of subscriptions in this category.
        total_monthly: Total monthly spending in this category.
        budget_used_percentage: Percentage of budget used (if budget set).
        is_over_budget: Whether spending exceeds budget.
    """

    subscription_count: int = Field(default=0, description="Number of subscriptions")
    total_monthly: Decimal = Field(default=Decimal("0"), description="Total monthly spend")
    budget_used_percentage: float | None = Field(default=None, description="Budget usage %")
    is_over_budget: bool | None = Field(default=None, description="Over budget flag")


class CategoryBudgetSummary(BaseModel):
    """Summary of category budgets and spending.

    Attributes:
        categories: List of categories with stats.
        total_budgeted: Total budget across all categories.
        total_spent: Total spending across all categories.
        categories_over_budget: Number of categories over budget.
    """

    categories: list[CategoryWithStats] = Field(..., description="Category summaries")
    total_budgeted: Decimal = Field(default=Decimal("0"), description="Total budget")
    total_spent: Decimal = Field(default=Decimal("0"), description="Total spending")
    categories_over_budget: int = Field(default=0, description="Count over budget")


class AssignCategoryRequest(BaseModel):
    """Request to assign a category to a subscription."""

    subscription_id: str = Field(..., description="Subscription UUID")
    category_id: str | None = Field(default=None, description="Category UUID (null to unassign)")

    @field_validator("subscription_id")
    @classmethod
    def validate_subscription_id(cls, v: str) -> str:
        """Validate subscription_id is a valid UUID."""
        validated = validate_uuid(v)
        if validated is None:
            raise ValueError("Invalid subscription_id format")
        return validated

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, v: str | None) -> str | None:
        """Validate category_id is a valid UUID."""
        return validate_uuid(v)


class BulkAssignCategoryRequest(BaseModel):
    """Request to assign a category to multiple subscriptions."""

    subscription_ids: list[str] = Field(
        ..., min_length=1, max_length=100, description="Subscription UUIDs"
    )
    category_id: str | None = Field(default=None, description="Category UUID (null to unassign)")

    @field_validator("subscription_ids")
    @classmethod
    def validate_subscription_ids(cls, v: list[str]) -> list[str]:
        """Validate all subscription_ids are valid UUIDs."""
        validated = []
        for sub_id in v:
            result = validate_uuid(sub_id)
            if result is None:
                raise ValueError(f"Invalid subscription_id format: {sub_id}")
            validated.append(result)
        return validated

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, v: str | None) -> str | None:
        """Validate category_id is a valid UUID."""
        return validate_uuid(v)
