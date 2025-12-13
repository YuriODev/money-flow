"""Pydantic schemas for Payment Card.

This module defines Pydantic v2 schemas for request/response validation
of payment card data.

Security:
    - Names are sanitized to prevent XSS
    - URLs are validated for safe schemes (no javascript:, data:)
    - Currency codes are validated against allowed list
    - Notes are checked for dangerous patterns
    - UUIDs are validated for proper format
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.payment_card import CardType
from src.security.validators import (
    sanitize_name,
    validate_currency,
    validate_safe_text,
    validate_safe_url,
    validate_uuid,
)


class PaymentCardBase(BaseModel):
    """Base schema for payment card data.

    Attributes:
        name: Card display name (e.g., "Monzo", "Revolut Platinum").
        card_type: Type of card (debit, credit, prepaid, bank_account).
        last_four: Last 4 digits of card number (optional).
        bank_name: Name of the bank/provider.
        currency: Default currency for this card.
        color: Card color in hex format.
        icon_url: URL to card/bank logo.
        notes: Optional notes.
        sort_order: Display order in lists.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Card display name")
    card_type: CardType = Field(default=CardType.DEBIT, description="Card type")
    last_four: str | None = Field(
        default=None, min_length=4, max_length=4, pattern=r"^\d{4}$", description="Last 4 digits"
    )
    bank_name: str = Field(..., min_length=1, max_length=100, description="Bank/provider name")
    currency: str = Field(default="GBP", min_length=3, max_length=3, description="Default currency")
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="Card color")
    icon_url: str | None = Field(default=None, max_length=500, description="Bank logo URL")
    notes: str | None = Field(default=None, description="Optional notes")
    sort_order: int = Field(default=0, ge=0, description="Display order")
    funding_card_id: str | None = Field(default=None, description="ID of card that funds this card")

    # Validators for security
    @field_validator("name", "bank_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Sanitize name to prevent XSS."""
        return sanitize_name(v)

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate currency against allowed list."""
        return validate_currency(v)

    @field_validator("icon_url")
    @classmethod
    def validate_icon_url(cls, v: str | None) -> str | None:
        """Validate icon URL is safe."""
        return validate_safe_url(v)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate notes don't contain dangerous content."""
        if v is None:
            return v
        return validate_safe_text(v)

    @field_validator("funding_card_id")
    @classmethod
    def validate_funding_card_id(cls, v: str | None) -> str | None:
        """Validate funding_card_id is a valid UUID."""
        return validate_uuid(v)


class PaymentCardCreate(PaymentCardBase):
    """Schema for creating a payment card."""

    pass


class PaymentCardUpdate(BaseModel):
    """Schema for updating a payment card (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    card_type: CardType | None = None
    last_four: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    bank_name: str | None = Field(default=None, min_length=1, max_length=100)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    notes: str | None = None
    sort_order: int | None = Field(default=None, ge=0)
    funding_card_id: str | None = Field(default=None, description="ID of card that funds this card")

    # Validators for security
    @field_validator("name", "bank_name")
    @classmethod
    def validate_names(cls, v: str | None) -> str | None:
        """Sanitize name to prevent XSS."""
        if v is None:
            return v
        return sanitize_name(v)

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str | None) -> str | None:
        """Validate currency against allowed list."""
        if v is None:
            return v
        return validate_currency(v)

    @field_validator("icon_url")
    @classmethod
    def validate_icon_url(cls, v: str | None) -> str | None:
        """Validate icon URL is safe."""
        return validate_safe_url(v)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate notes don't contain dangerous content."""
        if v is None:
            return v
        return validate_safe_text(v)

    @field_validator("funding_card_id")
    @classmethod
    def validate_funding_card_id(cls, v: str | None) -> str | None:
        """Validate funding_card_id is a valid UUID."""
        return validate_uuid(v)


class FundingCardInfo(BaseModel):
    """Brief info about a funding card."""

    id: str = Field(..., description="Card UUID")
    name: str = Field(..., description="Card name")
    color: str = Field(..., description="Card color")
    icon_url: str | None = Field(default=None, description="Card icon URL")


class PaymentCardResponse(PaymentCardBase):
    """Schema for payment card response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Card UUID")
    is_active: bool = Field(..., description="Active status")
    funding_card: FundingCardInfo | None = Field(
        default=None, description="Card that funds this one"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CardBalanceSummary(BaseModel):
    """Summary of required balance for a payment card.

    Attributes:
        card_id: Card UUID.
        card_name: Card display name.
        bank_name: Bank/provider name.
        color: Card color.
        icon_url: Bank logo URL.
        currency: Card currency.
        total_this_month: Total payments due this month.
        paid_this_month: Amount already paid this month.
        remaining_this_month: Remaining amount to pay this month.
        total_next_month: Total payments due next month.
        subscription_count: Number of subscriptions using this card.
        subscriptions: List of subscription names on this card.
    """

    card_id: str = Field(..., description="Card UUID")
    card_name: str = Field(..., description="Card display name")
    bank_name: str = Field(..., description="Bank name")
    color: str = Field(..., description="Card color")
    icon_url: str | None = Field(default=None, description="Bank logo")
    currency: str = Field(..., description="Card currency")
    total_this_month: Decimal = Field(..., description="Due this month (direct)")
    funded_this_month: Decimal = Field(
        default=Decimal("0"), description="Due this month (from funded cards)"
    )
    paid_this_month: Decimal = Field(default=Decimal("0"), description="Paid this month")
    remaining_this_month: Decimal = Field(default=Decimal("0"), description="Remaining this month")
    total_next_month: Decimal = Field(..., description="Due next month (direct)")
    funded_next_month: Decimal = Field(
        default=Decimal("0"), description="Due next month (from funded cards)"
    )
    subscription_count: int = Field(..., description="Number of direct subscriptions")
    funded_subscription_count: int = Field(
        default=0, description="Number of subscriptions from funded cards"
    )
    subscriptions: list[str] = Field(..., description="Subscription names")
    funded_subscriptions: list[str] = Field(
        default_factory=list, description="Subscriptions from funded cards"
    )


class AllCardsBalanceSummary(BaseModel):
    """Summary of all cards with their required balances.

    Attributes:
        cards: List of card balance summaries.
        total_all_cards_this_month: Total across all cards this month.
        total_paid_this_month: Total paid across all cards this month.
        total_remaining_this_month: Total remaining across all cards this month.
        total_all_cards_next_month: Total across all cards next month.
        unassigned_count: Subscriptions without a card assigned.
        unassigned_total: Total for unassigned subscriptions.
    """

    cards: list[CardBalanceSummary] = Field(..., description="Per-card summaries")
    total_all_cards_this_month: Decimal = Field(..., description="Total this month")
    total_paid_this_month: Decimal = Field(
        default=Decimal("0"), description="Total paid this month"
    )
    total_remaining_this_month: Decimal = Field(
        default=Decimal("0"), description="Total remaining this month"
    )
    total_all_cards_next_month: Decimal = Field(..., description="Total next month")
    unassigned_count: int = Field(default=0, description="Unassigned subscription count")
    unassigned_total: Decimal = Field(default=Decimal("0"), description="Unassigned total")
