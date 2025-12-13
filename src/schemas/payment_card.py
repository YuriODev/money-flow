"""Pydantic schemas for Payment Card.

This module defines Pydantic v2 schemas for request/response validation
of payment card data.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models.payment_card import CardType


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
    funding_card: FundingCardInfo | None = Field(default=None, description="Card that funds this one")
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
    funded_this_month: Decimal = Field(default=Decimal("0"), description="Due this month (from funded cards)")
    paid_this_month: Decimal = Field(default=Decimal("0"), description="Paid this month")
    remaining_this_month: Decimal = Field(default=Decimal("0"), description="Remaining this month")
    total_next_month: Decimal = Field(..., description="Due next month (direct)")
    funded_next_month: Decimal = Field(default=Decimal("0"), description="Due next month (from funded cards)")
    subscription_count: int = Field(..., description="Number of direct subscriptions")
    funded_subscription_count: int = Field(default=0, description="Number of subscriptions from funded cards")
    subscriptions: list[str] = Field(..., description="Subscription names")
    funded_subscriptions: list[str] = Field(default_factory=list, description="Subscriptions from funded cards")


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
