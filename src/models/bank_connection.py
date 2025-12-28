"""Bank connection models for Open Banking integration.

This module defines SQLAlchemy ORM models for Open Banking connections,
supporting both Plaid and TrueLayer providers for automatic transaction
import and recurring payment detection.

Sprint 5.7 - Open Banking Integration

Security Notes:
    - Access tokens are encrypted at rest using Fernet
    - Refresh tokens are stored securely for token renewal
    - Consent status is tracked for PSD2 compliance
    - All sensitive data is excluded from JSON serialization
"""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class BankProvider(str, enum.Enum):
    """Open Banking API provider.

    Attributes:
        PLAID: Plaid (US-focused, broad data aggregation).
        TRUELAYER: TrueLayer (UK/EU-focused, PSD2 compliant).
    """

    PLAID = "plaid"
    TRUELAYER = "truelayer"


class ConnectionStatus(str, enum.Enum):
    """Status of the bank connection.

    Attributes:
        PENDING: Initial state, awaiting user authorization.
        ACTIVE: Connected and syncing transactions.
        EXPIRED: Access token expired, needs refresh.
        REVOKED: User revoked consent.
        ERROR: Connection error, needs user action.
        DISCONNECTED: User manually disconnected.
    """

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ConsentStatus(str, enum.Enum):
    """PSD2 consent status for Open Banking.

    Attributes:
        PENDING: Consent flow initiated but not completed.
        AUTHORIZED: User granted consent.
        REJECTED: User rejected consent.
        EXPIRED: Consent expired (typically 90 days for PSD2).
        REVOKED: User revoked previously granted consent.
    """

    PENDING = "pending"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class BankConnection(Base):
    """Open Banking connection model.

    Represents a connection to a user's bank account via Plaid or TrueLayer.
    Stores encrypted access tokens and tracks sync state.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this connection.
        provider: Banking API provider (Plaid or TrueLayer).
        institution_id: Bank's unique identifier from provider.
        institution_name: Human-readable bank name.
        institution_logo_url: URL to bank's logo image.
        access_token_encrypted: Encrypted access token for API calls.
        refresh_token_encrypted: Encrypted refresh token for renewal.
        item_id: Plaid's Item ID or TrueLayer's credentials_id.
        status: Current connection status.
        consent_status: PSD2 consent status.
        consent_expires_at: When the consent expires (90 days for PSD2).
        last_sync_at: When transactions were last synced.
        sync_cursor: Cursor for incremental transaction sync.
        error_code: Last error code if status is ERROR.
        error_message: Human-readable error message.
        accounts_count: Number of linked accounts.
        is_auto_sync_enabled: Whether automatic daily sync is enabled.
        created_at: When the connection was created.
        updated_at: When the connection was last updated.

    Example:
        >>> connection = BankConnection(
        ...     user_id="user-uuid",
        ...     provider=BankProvider.TRUELAYER,
        ...     institution_id="ob-monzo",
        ...     institution_name="Monzo",
        ... )
    """

    __tablename__ = "bank_connections"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Provider and institution
    provider: Mapped[BankProvider] = mapped_column(Enum(BankProvider), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Encrypted credentials (using Fernet symmetric encryption)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Status tracking
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False, index=True
    )
    consent_status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus), default=ConsentStatus.PENDING, nullable=False
    )
    consent_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Sync state
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_cursor: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error tracking
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Account info
    accounts_count: Mapped[int] = mapped_column(Integer, default=0)
    is_auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bank_connections")
    accounts: Mapped[list["BankAccount"]] = relationship(
        "BankAccount",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    transactions: Mapped[list["BankTransaction"]] = relationship(
        "BankTransaction",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<BankConnection(institution='{self.institution_name}', provider={self.provider.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Check if connection is active and syncing."""
        return self.status == ConnectionStatus.ACTIVE

    @property
    def needs_reauthorization(self) -> bool:
        """Check if connection needs user reauthorization."""
        return self.status in (
            ConnectionStatus.EXPIRED,
            ConnectionStatus.REVOKED,
            ConnectionStatus.ERROR,
        )

    @property
    def consent_is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.consent_status != ConsentStatus.AUTHORIZED:
            return False
        if self.consent_expires_at and datetime.utcnow() > self.consent_expires_at:
            return False
        return True

    def mark_synced(self, cursor: str | None = None) -> None:
        """Record successful sync."""
        self.last_sync_at = datetime.utcnow()
        if cursor:
            self.sync_cursor = cursor
        self.error_code = None
        self.error_message = None

    def mark_error(self, code: str, message: str) -> None:
        """Record sync error."""
        self.status = ConnectionStatus.ERROR
        self.error_code = code
        self.error_message = message[:500] if message else None

    def disconnect(self) -> None:
        """Mark connection as disconnected."""
        self.status = ConnectionStatus.DISCONNECTED
        self.consent_status = ConsentStatus.REVOKED


class AccountType(str, enum.Enum):
    """Type of bank account.

    Attributes:
        CHECKING: Current/checking account.
        SAVINGS: Savings account.
        CREDIT: Credit card account.
        LOAN: Loan account.
        INVESTMENT: Investment/brokerage account.
        OTHER: Other account type.
    """

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class BankAccount(Base):
    """Bank account model.

    Represents an individual account within a bank connection.
    A single connection can have multiple accounts (e.g., checking + savings).

    Attributes:
        id: UUID primary key.
        connection_id: Foreign key to parent bank connection.
        account_id_external: Account ID from provider (Plaid/TrueLayer).
        name: Account name (e.g., "Main Checking").
        official_name: Official account name from bank.
        account_type: Type of account.
        subtype: Account subtype (provider-specific).
        currency: ISO 4217 currency code.
        current_balance: Current balance (as of last sync).
        available_balance: Available balance (may differ due to holds).
        credit_limit: Credit limit for credit accounts.
        mask: Last 4 digits of account number.
        is_syncing: Whether this account is included in sync.
        created_at: When the account was added.
        updated_at: When the account was last updated.

    Example:
        >>> account = BankAccount(
        ...     connection_id="conn-uuid",
        ...     account_id_external="acc_123",
        ...     name="Main Checking",
        ...     account_type=AccountType.CHECKING,
        ...     currency="GBP",
        ... )
    """

    __tablename__ = "bank_accounts"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Connection relationship
    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bank_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # External identifiers
    account_id_external: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Account details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), default=AccountType.CHECKING, nullable=False
    )
    subtype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)

    # Balances
    current_balance: Mapped[float | None] = mapped_column(nullable=True)
    available_balance: Mapped[float | None] = mapped_column(nullable=True)
    credit_limit: Mapped[float | None] = mapped_column(nullable=True)

    # Display info
    mask: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_syncing: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connection: Mapped["BankConnection"] = relationship("BankConnection", back_populates="accounts")
    transactions: Mapped[list["BankTransaction"]] = relationship(
        "BankTransaction",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<BankAccount(name='{self.name}', type={self.account_type.value}, currency={self.currency})>"

    @property
    def display_name(self) -> str:
        """Get display name with mask."""
        if self.mask:
            return f"{self.name} (****{self.mask})"
        return self.name


class TransactionCategory(str, enum.Enum):
    """Transaction category from Open Banking provider.

    Categories are normalized from Plaid/TrueLayer categories.

    Attributes:
        SUBSCRIPTION: Recurring subscription payment.
        UTILITIES: Utility bills.
        RENT: Rent/housing payments.
        INSURANCE: Insurance premiums.
        LOAN: Loan payments.
        TRANSFER: Bank transfers.
        INCOME: Income/salary.
        SHOPPING: Shopping/retail.
        FOOD: Food and dining.
        TRANSPORT: Transportation.
        ENTERTAINMENT: Entertainment.
        HEALTH: Healthcare.
        OTHER: Uncategorized.
    """

    SUBSCRIPTION = "subscription"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    LOAN = "loan"
    TRANSFER = "transfer"
    INCOME = "income"
    SHOPPING = "shopping"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    OTHER = "other"


class BankTransaction(Base):
    """Bank transaction model.

    Represents a transaction imported from Open Banking.
    Used for recurring payment detection and subscription matching.

    Attributes:
        id: UUID primary key.
        connection_id: Foreign key to bank connection.
        account_id: Foreign key to bank account.
        transaction_id_external: Transaction ID from provider.
        amount: Transaction amount (negative for debits).
        currency: ISO 4217 currency code.
        description: Transaction description.
        merchant_name: Cleaned merchant name.
        category: Transaction category.
        category_raw: Raw category from provider.
        date: Transaction date.
        pending: Whether transaction is pending.
        is_recurring: Whether detected as recurring.
        recurring_stream_id: ID for grouping recurring transactions.
        matched_subscription_id: Matched subscription if any.
        created_at: When imported.

    Example:
        >>> txn = BankTransaction(
        ...     connection_id="conn-uuid",
        ...     account_id="acc-uuid",
        ...     transaction_id_external="txn_123",
        ...     amount=-15.99,
        ...     description="NETFLIX.COM",
        ...     merchant_name="Netflix",
        ... )
    """

    __tablename__ = "bank_transactions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relationships
    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bank_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # External identifier
    transaction_id_external: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Transaction details
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Categorization
    category: Mapped[TransactionCategory] = mapped_column(
        Enum(TransactionCategory), default=TransactionCategory.OTHER, nullable=False, index=True
    )
    category_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Date and status
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=False)

    # Recurring detection
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    recurring_stream_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    matched_subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    connection: Mapped["BankConnection"] = relationship(
        "BankConnection", back_populates="transactions"
    )
    account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="transactions")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<BankTransaction(merchant='{self.merchant_name}', amount={self.amount}, date={self.date.date()})>"

    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit (outgoing)."""
        return self.amount < 0

    @property
    def absolute_amount(self) -> float:
        """Get absolute transaction amount."""
        return abs(self.amount)
