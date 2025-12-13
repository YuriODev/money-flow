"""Payment Card ORM model.

This module defines the SQLAlchemy ORM model for payment cards/accounts,
allowing users to track which card is used for each subscription and
calculate how much money needs to be on each card.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class CardType(str, enum.Enum):
    """Card type enumeration.

    Attributes:
        DEBIT: Debit card linked to bank account.
        CREDIT: Credit card with credit limit.
        PREPAID: Prepaid/virtual card.
        BANK_ACCOUNT: Direct bank account (for direct debits).
    """

    DEBIT = "debit"
    CREDIT = "credit"
    PREPAID = "prepaid"
    BANK_ACCOUNT = "bank_account"


class PaymentCard(Base):
    """Payment card/account model for tracking payment methods.

    Represents a payment card or bank account that can be linked to
    subscriptions. Tracks card details and calculates required balances.

    Attributes:
        id: UUID primary key (auto-generated).
        name: Card display name (e.g., "Monzo", "Revolut Platinum").
        card_type: Type of card (debit, credit, prepaid, bank_account).
        last_four: Last 4 digits of card number (optional).
        bank_name: Name of the bank/provider.
        currency: Default currency for this card.
        color: Card color for UI display (hex format).
        icon_url: URL to card/bank logo.
        is_active: Whether card is currently active.
        notes: Optional notes about the card.
        sort_order: Order for display in lists.
        funding_card_id: ID of card that funds this card (e.g., PayPal funded by Monzo).
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.
        subscriptions: Relationship to subscriptions using this card.
        funding_card: Relationship to the card that funds this one.

    Example:
        >>> card = PaymentCard(
        ...     name="Monzo",
        ...     card_type=CardType.DEBIT,
        ...     last_four="1234",
        ...     bank_name="Monzo Bank",
        ...     currency="GBP",
        ...     color="#FF5A5F",
        ... )
    """

    __tablename__ = "payment_cards"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    card_type: Mapped[CardType] = mapped_column(
        Enum(CardType), nullable=False, default=CardType.DEBIT
    )
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    funding_card_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("payment_cards.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships - will be populated when subscription has card_id
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="payment_card", lazy="selectin"
    )
    funding_card: Mapped["PaymentCard | None"] = relationship(
        "PaymentCard", remote_side=[id], lazy="selectin"
    )

    def __repr__(self) -> str:
        """Return string representation of card."""
        return f"<PaymentCard(name='{self.name}', bank='{self.bank_name}')>"
