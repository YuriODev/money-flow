"""Pydantic schemas for Subscription and Payment.

This module defines Pydantic v2 schemas for request/response validation
of subscription and payment data. Schemas enforce data types, constraints,
and provide automatic JSON serialization.

Schemas:
    SubscriptionBase: Base fields shared by all schemas.
    SubscriptionCreate: For creating new subscriptions.
    SubscriptionUpdate: For partial updates (all fields optional).
    SubscriptionResponse: For API responses with computed fields.
    SubscriptionSummary: For spending analytics responses.
    PaymentHistoryResponse: For payment history records.
    CalendarEvent: For calendar view payment events.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models.subscription import Frequency, PaymentStatus, PaymentType


class SubscriptionBase(BaseModel):
    """Base schema for subscription/payment data (Money Flow).

    Contains common fields used for both creation and response.
    All derived schemas inherit these fields.

    Attributes:
        name: Payment name (1-255 characters).
        amount: Payment amount (must be positive, 2 decimal places).
        currency: ISO 4217 currency code (3 characters).
        frequency: Payment frequency from Frequency enum.
        frequency_interval: Multiplier for frequency (minimum 1).
        start_date: When the payment started.
        payment_type: Top-level classification (subscription, debt, savings, etc.).
        category: Subcategory for grouping (e.g., Entertainment, Electric).
        notes: Optional freeform notes.
        payment_method: Payment method (card, bank, paypal, etc.).
        reminder_days: Days before payment to send reminder.
        icon_url: URL to service icon.
        color: Brand color in hex format.
        auto_renew: Whether payment auto-renews.
        is_installment: Whether this is an installment plan.
        total_installments: Total payments for installment plans.
        total_owed: Original debt amount (for debt payment type).
        remaining_balance: What's left to pay (for debt payment type).
        creditor: Who you owe (for debt payment type).
        target_amount: Savings goal amount (for savings payment type).
        current_saved: Progress toward goal (for savings payment type).
        recipient: Who receives the transfer (for savings/transfer types).

    Example:
        >>> base = SubscriptionBase(
        ...     name="Netflix",
        ...     amount=Decimal("15.99"),
        ...     payment_type=PaymentType.SUBSCRIPTION,
        ...     start_date=date.today()
        ... )
    """

    name: str = Field(..., min_length=1, max_length=255, description="Payment name")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount")
    currency: str = Field(default="GBP", min_length=3, max_length=3, description="Currency code")
    frequency: Frequency = Field(default=Frequency.MONTHLY, description="Payment frequency")
    frequency_interval: int = Field(default=1, ge=1, description="Frequency multiplier")
    start_date: date = Field(..., description="Payment start date")
    end_date: date | None = Field(default=None, description="Payment end date (optional)")

    # Payment type classification (Money Flow)
    payment_type: PaymentType = Field(
        default=PaymentType.SUBSCRIPTION, description="Payment type classification"
    )

    category: str | None = Field(default=None, max_length=100, description="Subcategory name")
    notes: str | None = Field(default=None, description="Optional notes")

    # Payment tracking fields
    payment_method: str | None = Field(default=None, max_length=50, description="Payment method")
    reminder_days: int = Field(default=3, ge=0, le=30, description="Reminder days before payment")
    icon_url: str | None = Field(default=None, max_length=500, description="Service icon URL")
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="Brand color")
    auto_renew: bool = Field(default=True, description="Auto-renew status")

    # Installment fields
    is_installment: bool = Field(default=False, description="Is installment plan")
    total_installments: int | None = Field(default=None, ge=1, description="Total installments")

    # Debt-specific fields (for PaymentType.DEBT)
    total_owed: Decimal | None = Field(default=None, ge=0, description="Original debt amount")
    remaining_balance: Decimal | None = Field(default=None, ge=0, description="Remaining balance")
    creditor: str | None = Field(default=None, max_length=255, description="Who you owe")

    # Savings-specific fields (for PaymentType.SAVINGS and PaymentType.TRANSFER)
    target_amount: Decimal | None = Field(default=None, ge=0, description="Savings goal amount")
    current_saved: Decimal | None = Field(default=None, ge=0, description="Current amount saved")
    recipient: str | None = Field(default=None, max_length=255, description="Who receives transfer")

    # Payment card link
    card_id: str | None = Field(default=None, description="Payment card UUID")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription.

    Inherits all fields from SubscriptionBase. Used for POST requests.

    Example:
        >>> create_data = SubscriptionCreate(
        ...     name="Spotify",
        ...     amount=Decimal("9.99"),
        ...     currency="GBP",
        ...     frequency=Frequency.MONTHLY,
        ...     start_date=date(2025, 1, 1),
        ... )
    """

    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription/payment (all fields optional).

    Used for PATCH/PUT requests where only specified fields are updated.
    Unset fields are excluded from the update.

    Attributes:
        name: New payment name.
        amount: New payment amount.
        currency: New currency code.
        frequency: New payment frequency.
        frequency_interval: New frequency multiplier.
        start_date: New start date.
        payment_type: New payment type classification.
        category: New subcategory.
        is_active: Active status toggle.
        notes: New notes.
        payment_method: New payment method.
        reminder_days: New reminder days setting.
        icon_url: New icon URL.
        color: New brand color.
        auto_renew: New auto-renew status.
        is_installment: Convert to/from installment plan.
        total_installments: New total installments count.
        total_owed: New total debt amount.
        remaining_balance: Updated remaining balance.
        creditor: New creditor name.
        target_amount: New savings goal.
        current_saved: Updated savings progress.
        recipient: New recipient name.

    Example:
        >>> update_data = SubscriptionUpdate(amount=Decimal("19.99"))
        >>> update_data.model_dump(exclude_unset=True)
        {'amount': Decimal('19.99')}
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    frequency: Frequency | None = None
    frequency_interval: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None

    # Payment type classification (Money Flow)
    payment_type: PaymentType | None = None

    category: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    notes: str | None = None

    # Payment tracking fields
    payment_method: str | None = Field(default=None, max_length=50)
    reminder_days: int | None = Field(default=None, ge=0, le=30)
    icon_url: str | None = Field(default=None, max_length=500)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    auto_renew: bool | None = None

    # Installment fields
    is_installment: bool | None = None
    total_installments: int | None = Field(default=None, ge=1)

    # Debt-specific fields (for PaymentType.DEBT)
    total_owed: Decimal | None = Field(default=None, ge=0)
    remaining_balance: Decimal | None = Field(default=None, ge=0)
    creditor: str | None = Field(default=None, max_length=255)

    # Savings-specific fields (for PaymentType.SAVINGS and PaymentType.TRANSFER)
    target_amount: Decimal | None = Field(default=None, ge=0)
    current_saved: Decimal | None = Field(default=None, ge=0)
    recipient: str | None = Field(default=None, max_length=255)

    # Payment card link
    card_id: str | None = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription/payment response (Money Flow).

    Includes all base fields plus computed and system fields.
    Configured for ORM model compatibility.

    Attributes:
        id: UUID string identifier.
        next_payment_date: Calculated next payment date.
        last_payment_date: Date of most recent payment.
        is_active: Current active status.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
        completed_installments: Number of completed installment payments.
        installment_start_date: When installment plan started.
        installment_end_date: When installment plan ends.
        days_until_payment: Days until next payment (computed).
        payment_status_label: Status label: overdue, due_soon, upcoming (computed).
        installments_remaining: Remaining installment payments (computed).
        debt_paid_percentage: Percentage of debt paid off (computed for debts).
        savings_progress_percentage: Percentage toward savings goal (computed for savings).

    Example:
        >>> response = SubscriptionResponse.model_validate(subscription_orm)
        >>> response.id
        'uuid-string'
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Payment UUID")
    end_date: date | None = Field(default=None, description="Payment end date")
    next_payment_date: date = Field(..., description="Next payment date")
    last_payment_date: date | None = Field(default=None, description="Last payment date")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Installment tracking
    completed_installments: int = Field(default=0, description="Completed installments")
    installment_start_date: date | None = Field(default=None, description="Installment start")
    installment_end_date: date | None = Field(default=None, description="Installment end")

    # Computed properties from ORM model
    days_until_payment: int = Field(default=0, description="Days until next payment")
    payment_status_label: str = Field(default="upcoming", description="Payment status label")
    installments_remaining: int | None = Field(default=None, description="Remaining installments")

    # Computed progress fields (Money Flow)
    debt_paid_percentage: float | None = Field(
        default=None, description="Percentage of debt paid (for debt type)"
    )
    savings_progress_percentage: float | None = Field(
        default=None, description="Percentage toward savings goal (for savings type)"
    )


class SubscriptionSummary(BaseModel):
    """Schema for subscription/payment spending summary (Money Flow).

    Aggregated analytics for dashboard display including totals,
    category/type breakdown, and upcoming payments.

    Attributes:
        total_monthly: Sum of all monthly-normalized payment costs.
        total_yearly: Projected annual spending (monthly * 12).
        active_count: Number of active payments.
        by_category: Monthly spending by subcategory name.
        by_payment_type: Monthly spending by payment type.
        upcoming_week: Payments due in next 7 days.
        currency: Currency code for the totals (e.g., 'GBP').
        total_debt: Sum of all remaining debt balances.
        total_savings_target: Sum of all savings goals.
        total_current_saved: Sum of all current savings.

    Example:
        >>> summary.total_monthly
        Decimal('125.99')
        >>> summary.by_payment_type
        {'subscription': Decimal('45.99'), 'utility': Decimal('80.00')}
    """

    total_monthly: Decimal = Field(..., description="Total monthly spending")
    total_yearly: Decimal = Field(..., description="Total yearly spending")
    active_count: int = Field(..., description="Active payment count")
    by_category: dict[str, Decimal] = Field(..., description="Spending by subcategory")
    by_payment_type: dict[str, Decimal] = Field(
        default_factory=dict, description="Spending by payment type"
    )
    upcoming_week: list[SubscriptionResponse] = Field(..., description="Due in 7 days")
    currency: str = Field(default="GBP", description="Currency code for totals")

    # Debt and savings totals (Money Flow)
    total_debt: Decimal = Field(default=Decimal("0"), description="Total remaining debt")
    total_savings_target: Decimal = Field(default=Decimal("0"), description="Total savings goals")
    total_current_saved: Decimal = Field(default=Decimal("0"), description="Total current savings")


class MonthlyPaymentsSummary(BaseModel):
    """Schema for monthly payments summary.

    Unified endpoint for calculating total payments due for current
    and next month. Used by both Calendar and Cards dashboard for
    consistent totals.

    Attributes:
        current_month_total: Total payments due this month.
        current_month_paid: Amount already paid this month.
        current_month_remaining: Remaining to pay this month.
        next_month_total: Total payments due next month.
        payment_count_this_month: Number of payments this month.
        payment_count_next_month: Number of payments next month.
        currency: Currency code for the totals.

    Example:
        >>> summary.current_month_total
        Decimal('8570.00')
    """

    current_month_total: Decimal = Field(..., description="Total due this month")
    current_month_paid: Decimal = Field(..., description="Amount paid this month")
    current_month_remaining: Decimal = Field(..., description="Remaining this month")
    next_month_total: Decimal = Field(..., description="Total due next month")
    payment_count_this_month: int = Field(..., description="Payment count this month")
    payment_count_next_month: int = Field(..., description="Payment count next month")
    currency: str = Field(default="GBP", description="Currency code for totals")


class PaymentHistoryResponse(BaseModel):
    """Schema for payment history record response.

    Represents a single payment event in the history log.
    Used to display payment history and track installment progress.

    Attributes:
        id: UUID string identifier.
        subscription_id: UUID of associated subscription.
        payment_date: When the payment was made.
        amount: Payment amount.
        currency: ISO 4217 currency code.
        status: Payment status (completed, pending, failed, cancelled).
        payment_method: Payment method used.
        installment_number: For installments, which payment this is.
        notes: Optional notes about this payment.
        created_at: Record creation timestamp.

    Example:
        >>> history = PaymentHistoryResponse.model_validate(payment_orm)
        >>> history.status
        'completed'
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Payment history UUID")
    subscription_id: str = Field(..., description="Associated subscription UUID")
    payment_date: date = Field(..., description="Payment date")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: PaymentStatus = Field(..., description="Payment status")
    payment_method: str | None = Field(default=None, description="Payment method")
    installment_number: int | None = Field(default=None, description="Installment number")
    notes: str | None = Field(default=None, description="Payment notes")
    created_at: datetime = Field(..., description="Record creation timestamp")


class CalendarEvent(BaseModel):
    """Schema for calendar view payment event (Money Flow).

    Represents a payment event for calendar display.
    Includes payment details for rich calendar UI.

    Attributes:
        id: Payment UUID.
        name: Payment name for display.
        amount: Payment amount.
        currency: ISO 4217 currency code.
        payment_date: Date of this payment.
        payment_type: Payment type classification.
        color: Brand color for calendar styling.
        icon_url: Service icon URL.
        category: Payment subcategory.
        is_installment: Whether this is an installment payment.
        installment_number: Current installment number.
        total_installments: Total installments in plan.
        status: Payment status for this event.

    Example:
        >>> event = CalendarEvent(
        ...     id="uuid",
        ...     name="Netflix",
        ...     amount=Decimal("15.99"),
        ...     currency="GBP",
        ...     payment_type=PaymentType.SUBSCRIPTION,
        ...     payment_date=date.today(),
        ...     color="#E50914"
        ... )
    """

    id: str = Field(..., description="Payment UUID")
    name: str = Field(..., description="Payment name")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    payment_date: date = Field(..., description="Payment date")
    payment_type: PaymentType = Field(default=PaymentType.SUBSCRIPTION, description="Payment type")
    color: str = Field(default="#3B82F6", description="Brand color")
    icon_url: str | None = Field(default=None, description="Service icon URL")
    category: str | None = Field(default=None, description="Subcategory")
    is_installment: bool = Field(default=False, description="Is installment payment")
    installment_number: int | None = Field(default=None, description="Current installment")
    total_installments: int | None = Field(default=None, description="Total installments")
    status: str = Field(default="upcoming", description="Payment status")
    card_id: str | None = Field(default=None, description="Linked payment card ID")
    is_paid: bool = Field(default=False, description="Whether payment has been recorded")


# ============================================================================
# Import/Export Schemas
# ============================================================================


class SubscriptionExport(BaseModel):
    """Schema for exporting a subscription/payment (Money Flow).

    Contains all data needed to recreate a payment on import.
    Excludes system-generated fields like id and timestamps.

    Attributes:
        name: Payment name.
        amount: Payment amount as string for precision.
        currency: ISO 4217 currency code.
        frequency: Payment frequency.
        frequency_interval: Frequency multiplier.
        start_date: Payment start date.
        next_payment_date: Calculated next payment.
        payment_type: Payment type classification.
        category: Subcategory name.
        notes: Optional notes.
        is_active: Active status.
        payment_method: Payment method.
        reminder_days: Reminder days before payment.
        icon_url: Service icon URL.
        color: Brand color.
        auto_renew: Auto-renew status.
        is_installment: Installment plan flag.
        total_installments: Total installments.
        completed_installments: Completed installments.
        total_owed: Original debt amount (for debt type).
        remaining_balance: Remaining balance (for debt type).
        creditor: Who you owe (for debt type).
        target_amount: Savings goal (for savings type).
        current_saved: Current savings (for savings type).
        recipient: Who receives (for savings/transfer types).
    """

    name: str
    amount: str  # String for precision
    currency: str
    frequency: str
    frequency_interval: int
    start_date: str  # ISO format
    end_date: str | None = None  # ISO format
    next_payment_date: str  # ISO format
    payment_type: str = "subscription"  # Payment type as string for JSON
    category: str | None = None
    notes: str | None = None
    is_active: bool = True
    payment_method: str | None = None
    reminder_days: int = 3
    icon_url: str | None = None
    color: str = "#3B82F6"
    auto_renew: bool = True
    is_installment: bool = False
    total_installments: int | None = None
    completed_installments: int = 0

    # Debt-specific fields (Money Flow)
    total_owed: str | None = None  # String for precision
    remaining_balance: str | None = None  # String for precision
    creditor: str | None = None

    # Savings-specific fields (Money Flow)
    target_amount: str | None = None  # String for precision
    current_saved: str | None = None  # String for precision
    recipient: str | None = None


class ExportData(BaseModel):
    """Schema for full export data (Money Flow).

    Contains metadata and all payments for backup/transfer.

    Attributes:
        version: Export format version.
        exported_at: Export timestamp.
        subscription_count: Number of payments.
        subscriptions: List of payment data.
    """

    version: str = Field(default="2.0", description="Export format version (2.0 for Money Flow)")
    exported_at: datetime = Field(..., description="Export timestamp")
    subscription_count: int = Field(..., description="Number of payments")
    subscriptions: list[SubscriptionExport] = Field(..., description="Payment data")


class ImportResult(BaseModel):
    """Schema for import operation result.

    Reports success/failure counts and any errors encountered.

    Attributes:
        total: Total subscriptions in import file.
        imported: Successfully imported count.
        skipped: Skipped (duplicate) count.
        failed: Failed import count.
        errors: List of error messages.
    """

    total: int = Field(..., description="Total in import file")
    imported: int = Field(..., description="Successfully imported")
    skipped: int = Field(..., description="Skipped (duplicates)")
    failed: int = Field(..., description="Failed imports")
    errors: list[str] = Field(default_factory=list, description="Error messages")
