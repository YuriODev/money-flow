"""Pydantic schemas for Open Banking integration.

This module defines request/response schemas for the banking API
endpoints, including bank connections, accounts, and transactions.

Sprint 5.7 - Open Banking Integration
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BankProviderEnum(str, Enum):
    """Bank API provider enum for API."""

    PLAID = "plaid"
    TRUELAYER = "truelayer"


class ConnectionStatusEnum(str, Enum):
    """Connection status enum for API."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ConsentStatusEnum(str, Enum):
    """Consent status enum for API."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AccountTypeEnum(str, Enum):
    """Account type enum for API."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class TransactionCategoryEnum(str, Enum):
    """Transaction category enum for API."""

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


# ============================================================================
# Bank Connection Schemas
# ============================================================================


class BankConnectionCreate(BaseModel):
    """Schema for initiating a bank connection.

    Attributes:
        provider: Banking API provider (plaid or truelayer).
        country_code: ISO 3166-1 alpha-2 country code.
        redirect_uri: OAuth redirect URI after authorization.
    """

    provider: BankProviderEnum = BankProviderEnum.TRUELAYER
    country_code: str = Field("GB", min_length=2, max_length=2)
    redirect_uri: HttpUrl | None = None


class BankConnectionLinkResponse(BaseModel):
    """Response with link URL for bank authorization.

    Attributes:
        link_url: URL to redirect user for bank authorization.
        link_token: Token for Plaid Link or TrueLayer auth.
        expiration: When the link expires.
    """

    link_url: str
    link_token: str
    expiration: datetime


class BankConnectionCallback(BaseModel):
    """Schema for OAuth callback from bank authorization.

    Attributes:
        code: Authorization code from OAuth flow.
        state: State parameter for CSRF protection.
    """

    code: str
    state: str


class BankConnectionResponse(BaseModel):
    """Schema for bank connection response.

    Attributes:
        id: Connection UUID.
        provider: Banking API provider.
        institution_id: Bank's provider ID.
        institution_name: Human-readable bank name.
        institution_logo_url: URL to bank logo.
        status: Current connection status.
        consent_status: PSD2 consent status.
        consent_expires_at: When consent expires.
        accounts_count: Number of linked accounts.
        last_sync_at: When last synced.
        is_auto_sync_enabled: Whether auto-sync is on.
        error_message: Error message if status is error.
        created_at: When connected.
        updated_at: When last updated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: BankProviderEnum
    institution_id: str
    institution_name: str
    institution_logo_url: str | None
    status: ConnectionStatusEnum
    consent_status: ConsentStatusEnum
    consent_expires_at: datetime | None
    accounts_count: int
    last_sync_at: datetime | None
    is_auto_sync_enabled: bool
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class BankConnectionListResponse(BaseModel):
    """Schema for list of bank connections.

    Attributes:
        connections: List of connections.
        total: Total count.
    """

    connections: list[BankConnectionResponse]
    total: int


class BankConnectionUpdate(BaseModel):
    """Schema for updating bank connection settings.

    Attributes:
        is_auto_sync_enabled: Enable/disable auto-sync.
    """

    is_auto_sync_enabled: bool | None = None


# ============================================================================
# Bank Account Schemas
# ============================================================================


class BankAccountResponse(BaseModel):
    """Schema for bank account response.

    Attributes:
        id: Account UUID.
        connection_id: Parent connection UUID.
        account_id_external: External account ID.
        name: Account name.
        official_name: Official name from bank.
        account_type: Type of account.
        subtype: Account subtype.
        currency: ISO 4217 currency code.
        current_balance: Current balance.
        available_balance: Available balance.
        credit_limit: Credit limit for credit accounts.
        mask: Last 4 digits.
        is_syncing: Whether account is syncing.
        created_at: When added.
        updated_at: When last updated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    connection_id: str
    account_id_external: str
    name: str
    official_name: str | None
    account_type: AccountTypeEnum
    subtype: str | None
    currency: str
    current_balance: float | None
    available_balance: float | None
    credit_limit: float | None
    mask: str | None
    is_syncing: bool
    created_at: datetime
    updated_at: datetime

    @property
    def display_name(self) -> str:
        """Get display name with mask."""
        if self.mask:
            return f"{self.name} (****{self.mask})"
        return self.name


class BankAccountListResponse(BaseModel):
    """Schema for list of bank accounts.

    Attributes:
        accounts: List of accounts.
        total: Total count.
    """

    accounts: list[BankAccountResponse]
    total: int


class BankAccountUpdate(BaseModel):
    """Schema for updating bank account settings.

    Attributes:
        is_syncing: Enable/disable syncing for this account.
    """

    is_syncing: bool | None = None


# ============================================================================
# Bank Transaction Schemas
# ============================================================================


class BankTransactionResponse(BaseModel):
    """Schema for bank transaction response.

    Attributes:
        id: Transaction UUID.
        connection_id: Parent connection UUID.
        account_id: Parent account UUID.
        transaction_id_external: External transaction ID.
        amount: Transaction amount.
        currency: ISO 4217 currency code.
        description: Transaction description.
        merchant_name: Cleaned merchant name.
        category: Transaction category.
        category_raw: Raw category from provider.
        date: Transaction date.
        pending: Whether pending.
        is_recurring: Whether detected as recurring.
        recurring_stream_id: Recurring stream ID.
        matched_subscription_id: Matched subscription UUID.
        created_at: When imported.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    connection_id: str
    account_id: str
    transaction_id_external: str
    amount: float
    currency: str
    description: str
    merchant_name: str | None
    category: TransactionCategoryEnum
    category_raw: str | None
    date: datetime
    pending: bool
    is_recurring: bool
    recurring_stream_id: str | None
    matched_subscription_id: str | None
    created_at: datetime


class BankTransactionListResponse(BaseModel):
    """Schema for list of bank transactions.

    Attributes:
        transactions: List of transactions.
        total: Total count.
        has_more: Whether more pages exist.
    """

    transactions: list[BankTransactionResponse]
    total: int
    has_more: bool = False


class BankTransactionFilters(BaseModel):
    """Filters for transaction queries.

    Attributes:
        account_id: Filter by account.
        category: Filter by category.
        is_recurring: Filter recurring only.
        start_date: Start date filter.
        end_date: End date filter.
        min_amount: Minimum amount.
        max_amount: Maximum amount.
        merchant_name: Search by merchant.
    """

    account_id: str | None = None
    category: TransactionCategoryEnum | None = None
    is_recurring: bool | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    merchant_name: str | None = None


# ============================================================================
# Sync Status Schemas
# ============================================================================


class SyncStatusResponse(BaseModel):
    """Schema for sync status response.

    Attributes:
        connection_id: Connection UUID.
        status: Current status.
        last_sync_at: When last synced.
        next_sync_at: When next scheduled sync.
        transactions_synced: Total transactions synced.
        new_transactions: New transactions in last sync.
        error: Error if any.
    """

    connection_id: str
    status: ConnectionStatusEnum
    last_sync_at: datetime | None
    next_sync_at: datetime | None
    transactions_synced: int
    new_transactions: int
    error: str | None = None


class TriggerSyncRequest(BaseModel):
    """Request to trigger manual sync.

    Attributes:
        connection_id: Connection to sync.
        full_refresh: Whether to do full refresh (re-fetch all).
    """

    connection_id: str
    full_refresh: bool = False


class TriggerSyncResponse(BaseModel):
    """Response from triggering sync.

    Attributes:
        success: Whether sync started.
        message: Status message.
        job_id: Background job ID if async.
    """

    success: bool
    message: str
    job_id: str | None = None


# ============================================================================
# Recurring Detection Schemas
# ============================================================================


class RecurringStreamResponse(BaseModel):
    """Schema for detected recurring payment stream.

    Attributes:
        stream_id: Unique stream identifier.
        merchant_name: Merchant name.
        average_amount: Average transaction amount.
        currency: Currency code.
        frequency: Detected frequency.
        transaction_count: Number of transactions.
        first_date: First transaction date.
        last_date: Most recent transaction date.
        next_expected_date: Predicted next date.
        category: Transaction category.
        is_active: Whether stream is active.
        matched_subscription_id: Matched subscription if any.
    """

    stream_id: str
    merchant_name: str
    average_amount: float
    currency: str
    frequency: str
    transaction_count: int
    first_date: datetime
    last_date: datetime
    next_expected_date: datetime | None
    category: TransactionCategoryEnum
    is_active: bool
    matched_subscription_id: str | None = None


class RecurringStreamsResponse(BaseModel):
    """Response with detected recurring streams.

    Attributes:
        streams: List of recurring streams.
        total: Total count.
    """

    streams: list[RecurringStreamResponse]
    total: int


class MatchSubscriptionRequest(BaseModel):
    """Request to match recurring stream to subscription.

    Attributes:
        stream_id: Recurring stream ID.
        subscription_id: Subscription to match.
    """

    stream_id: str
    subscription_id: str


# ============================================================================
# Institution Schemas
# ============================================================================


class InstitutionResponse(BaseModel):
    """Schema for bank institution.

    Attributes:
        institution_id: Provider's institution ID.
        name: Institution name.
        logo_url: Logo URL.
        country_codes: Supported countries.
        products: Supported products (transactions, balances, etc.).
    """

    institution_id: str
    name: str
    logo_url: str | None
    country_codes: list[str]
    products: list[str]


class InstitutionSearchResponse(BaseModel):
    """Response from institution search.

    Attributes:
        institutions: List of matching institutions.
        total: Total matches.
    """

    institutions: list[InstitutionResponse]
    total: int


# ============================================================================
# Statistics Schemas
# ============================================================================


class BankingStatsResponse(BaseModel):
    """Schema for banking statistics.

    Attributes:
        total_connections: Number of bank connections.
        active_connections: Active connections.
        total_accounts: Total linked accounts.
        total_transactions: Total imported transactions.
        recurring_streams_detected: Detected recurring payments.
        matched_subscriptions: Streams matched to subscriptions.
        last_sync_at: Most recent sync time.
    """

    total_connections: int
    active_connections: int
    total_accounts: int
    total_transactions: int
    recurring_streams_detected: int
    matched_subscriptions: int
    last_sync_at: datetime | None
