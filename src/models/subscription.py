"""Subscription and Payment ORM models.

This module defines the SQLAlchemy ORM models for subscriptions and payment history,
including the Frequency enum for payment schedules and PaymentStatus enum for tracking.

The models use async-compatible SQLAlchemy 2.0 patterns.
"""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class PaymentType(str, enum.Enum):
    """Payment type enumeration for Money Flow.

    Top-level classification of recurring payments to support different
    financial tracking needs beyond just subscriptions.

    Attributes:
        SUBSCRIPTION: Digital services, streaming (Netflix, Spotify, etc.).
        HOUSING: Rent, mortgage payments.
        UTILITY: Electric, gas, water, internet, council tax.
        PROFESSIONAL_SERVICE: Therapist, coach, trainer, tutor, barrister, lawyer.
        INSURANCE: Health, device (AppleCare), vehicle, life.
        DEBT: Credit cards, loans, personal debts to friends/family.
        SAVINGS: Regular savings transfers, goals with targets.
        TRANSFER: Family support, recurring gifts, partner transfers.
        ONE_TIME: One-time payments that won't recur (legal fees, one-off services).

    Example:
        >>> PaymentType.SUBSCRIPTION.value
        'subscription'
        >>> PaymentType("debt")
        <PaymentType.DEBT: 'debt'>
    """

    SUBSCRIPTION = "subscription"
    HOUSING = "housing"
    UTILITY = "utility"
    PROFESSIONAL_SERVICE = "professional_service"
    INSURANCE = "insurance"
    DEBT = "debt"
    SAVINGS = "savings"
    TRANSFER = "transfer"
    ONE_TIME = "one_time"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration.

    Defines the possible states for a payment record.

    Attributes:
        COMPLETED: Payment was successful.
        PENDING: Payment is scheduled but not yet processed.
        FAILED: Payment attempt failed.
        CANCELLED: Payment was cancelled.
    """

    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Frequency(str, enum.Enum):
    """Payment frequency enumeration.

    Defines the supported billing frequencies for subscriptions.
    Inherits from str for JSON serialization compatibility.

    Attributes:
        DAILY: Daily billing (every day).
        WEEKLY: Weekly billing (every 7 days).
        BIWEEKLY: Bi-weekly billing (every 14 days).
        MONTHLY: Monthly billing (same day each month).
        QUARTERLY: Quarterly billing (every 3 months).
        YEARLY: Annual billing (once per year).
        CUSTOM: Custom interval using frequency_interval field.

    Example:
        >>> Frequency.MONTHLY.value
        'monthly'
        >>> Frequency("yearly")
        <Frequency.YEARLY: 'yearly'>
    """

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Subscription(Base):
    """Subscription model for tracking recurring payments (Money Flow).

    Represents a payment record with payment details, scheduling,
    and categorization. Supports subscriptions, debts, savings, utilities,
    housing, professional services, insurance, and transfers.
    Automatically tracks creation and update times.

    Attributes:
        id: UUID primary key (auto-generated).
        name: Payment name (e.g., "Netflix", "Rent"). Indexed for search.
        amount: Payment amount with 2 decimal precision.
        currency: ISO 4217 currency code (default: "GBP").
        frequency: Payment frequency from Frequency enum.
        frequency_interval: Multiplier for frequency (e.g., 2 = every 2 weeks).
        start_date: When the payment started.
        end_date: When the payment ends (optional, for fixed-term subscriptions/installments).
        next_payment_date: Calculated next payment date.
        last_payment_date: When the last payment was made.
        payment_type: Top-level payment classification (subscription, debt, etc.).
        category: Subcategory for grouping (e.g., "Entertainment", "Electric").
        is_active: Whether payment is currently active.
        notes: Optional freeform notes.
        payment_method: Payment method (card, bank, paypal, etc.).
        reminder_days: Days before payment to send reminder (default: 3).
        icon_url: URL to service icon/logo.
        color: Brand color for UI display (hex format).
        auto_renew: Whether payment auto-renews.
        is_installment: Whether this is an installment payment plan.
        total_installments: Total number of payments for installments.
        completed_installments: Number of installments already paid.
        installment_start_date: When installment plan started.
        installment_end_date: When installment plan ends.
        total_owed: Original debt amount (for debt payment type).
        remaining_balance: What's left to pay (for debt payment type).
        creditor: Who you owe - bank, friend name, etc. (for debt payment type).
        target_amount: Savings goal amount (for savings payment type).
        current_saved: Progress toward savings goal (for savings payment type).
        recipient: Who receives the transfer (for savings/transfer types).
        user_id: Foreign key to owning user (for multi-user support).
        created_at: Record creation timestamp.
        updated_at: Last modification timestamp.
        payment_history: Relationship to payment history records.
        user: Relationship to owning user.

    Example:
        >>> subscription = Subscription(
        ...     name="Netflix",
        ...     amount=Decimal("15.99"),
        ...     currency="GBP",
        ...     frequency=Frequency.MONTHLY,
        ...     payment_type=PaymentType.SUBSCRIPTION,
        ...     start_date=date.today(),
        ...     next_payment_date=date.today(),
        ... )
        >>> subscription.name
        'Netflix'

        >>> debt = Subscription(
        ...     name="Credit Card",
        ...     amount=Decimal("100.00"),
        ...     payment_type=PaymentType.DEBT,
        ...     total_owed=Decimal("5000.00"),
        ...     remaining_balance=Decimal("3500.00"),
        ...     creditor="Barclays",
        ...     ...
        ... )
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")

    frequency: Mapped[Frequency] = mapped_column(
        Enum(Frequency), nullable=False, default=Frequency.MONTHLY
    )
    frequency_interval: Mapped[int] = mapped_column(Integer, default=1)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Payment type classification (Money Flow)
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType), nullable=False, default=PaymentType.SUBSCRIPTION, index=True
    )

    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment tracking fields
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reminder_days: Mapped[int] = mapped_column(Integer, default=3)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    # Installment payment fields
    is_installment: Mapped[bool] = mapped_column(Boolean, default=False)
    total_installments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_installments: Mapped[int] = mapped_column(Integer, default=0)
    installment_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    installment_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Debt-specific fields (for PaymentType.DEBT)
    total_owed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    remaining_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    creditor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Savings-specific fields (for PaymentType.SAVINGS and PaymentType.TRANSFER)
    target_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    current_saved: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Payment card link (which card pays for this subscription)
    card_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("payment_cards.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # User ownership (for multi-user support)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    payment_history: Mapped[list["PaymentHistory"]] = relationship(
        "PaymentHistory", back_populates="subscription", cascade="all, delete-orphan"
    )
    payment_card: Mapped["PaymentCard | None"] = relationship(  # noqa: F821
        "PaymentCard", back_populates="subscriptions", lazy="selectin"
    )
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="subscriptions", lazy="selectin"
    )

    def __repr__(self) -> str:
        """Return string representation of subscription.

        Returns:
            Debug-friendly string with name, amount, and frequency.

        Example:
            >>> str(subscription)
            "<Subscription(name='Netflix', amount=15.99, frequency=monthly)>"
        """
        return (
            f"<Subscription(name='{self.name}', "
            f"amount={self.amount}, frequency={self.frequency.value})>"
        )

    @property
    def days_until_payment(self) -> int:
        """Calculate days until next payment.

        Returns:
            Number of days until next payment. Negative if overdue.
        """
        return (self.next_payment_date - date.today()).days

    @property
    def payment_status(self) -> str:
        """Determine current payment status.

        Returns:
            Status string: 'overdue', 'due_soon', or 'upcoming'.
        """
        days = self.days_until_payment
        if days < 0:
            return "overdue"
        elif days <= self.reminder_days:
            return "due_soon"
        return "upcoming"

    @property
    def installments_remaining(self) -> int | None:
        """Calculate remaining installments.

        Returns:
            Number of remaining installments, or None if not an installment plan.
        """
        if not self.is_installment or self.total_installments is None:
            return None
        return self.total_installments - self.completed_installments

    @property
    def debt_paid_percentage(self) -> float | None:
        """Calculate percentage of debt paid off.

        Returns:
            Percentage paid (0-100), or None if not a debt or missing data.
        """
        if self.payment_type != PaymentType.DEBT:
            return None
        if self.total_owed is None or self.total_owed <= 0:
            return None
        if self.remaining_balance is None:
            return None
        paid = float(self.total_owed - self.remaining_balance)
        return round((paid / float(self.total_owed)) * 100, 1)

    @property
    def savings_progress_percentage(self) -> float | None:
        """Calculate percentage progress toward savings goal.

        Returns:
            Percentage saved (0-100+), or None if not savings or missing data.
        """
        if self.payment_type != PaymentType.SAVINGS:
            return None
        if self.target_amount is None or self.target_amount <= 0:
            return None
        if self.current_saved is None:
            return 0.0
        return round((float(self.current_saved) / float(self.target_amount)) * 100, 1)


class PaymentHistory(Base):
    """Payment history model for tracking individual payments.

    Records each payment made for a subscription, including installment
    payments with their sequence number.

    Attributes:
        id: UUID primary key (auto-generated).
        subscription_id: Foreign key to subscription.
        payment_date: When the payment was made.
        amount: Payment amount.
        currency: Currency code.
        status: Payment status (completed, pending, failed, cancelled).
        payment_method: How the payment was made.
        installment_number: Sequence number for installment payments.
        notes: Optional payment notes.
        created_at: Record creation timestamp.
        subscription: Relationship to parent subscription.

    Example:
        >>> payment = PaymentHistory(
        ...     subscription_id="uuid-string",
        ...     payment_date=date.today(),
        ...     amount=Decimal("15.99"),
        ...     status=PaymentStatus.COMPLETED,
        ... )
    """

    __tablename__ = "payment_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.COMPLETED, index=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="payment_history"
    )

    def __repr__(self) -> str:
        """Return string representation of payment.

        Returns:
            Debug-friendly string with subscription_id, amount, and date.
        """
        return (
            f"<PaymentHistory(subscription_id='{self.subscription_id}', "
            f"amount={self.amount}, date={self.payment_date})>"
        )
