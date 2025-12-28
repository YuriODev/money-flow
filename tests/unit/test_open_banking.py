"""Unit tests for Open Banking integration.

Sprint 5.7 - Open Banking (Plaid/TrueLayer)

Tests cover:
- Bank connection models and enums
- Bank account and transaction models
- Pydantic schemas for API
- Open Banking service logic
- Category mapping
- Encryption helpers
"""

from datetime import datetime, timedelta

import pytest

from src.models.bank_connection import (
    AccountType,
    BankAccount,
    BankConnection,
    BankProvider,
    BankTransaction,
    ConnectionStatus,
    ConsentStatus,
    TransactionCategory,
)
from src.schemas.bank_connection import (
    AccountTypeEnum,
    BankAccountResponse,
    BankAccountUpdate,
    BankConnectionCallback,
    BankConnectionCreate,
    BankConnectionLinkResponse,
    BankConnectionResponse,
    BankConnectionUpdate,
    BankingStatsResponse,
    BankProviderEnum,
    BankTransactionFilters,
    BankTransactionResponse,
    ConnectionStatusEnum,
    ConsentStatusEnum,
    MatchSubscriptionRequest,
    RecurringStreamResponse,
    RecurringStreamsResponse,
    SyncStatusResponse,
    TransactionCategoryEnum,
    TriggerSyncRequest,
    TriggerSyncResponse,
)


# ============================================================================
# Model Tests - Enums
# ============================================================================


class TestBankProviderEnum:
    """Tests for BankProvider enum."""

    def test_plaid_value(self):
        """Test Plaid enum value."""
        assert BankProvider.PLAID.value == "plaid"

    def test_truelayer_value(self):
        """Test TrueLayer enum value."""
        assert BankProvider.TRUELAYER.value == "truelayer"

    def test_provider_is_string(self):
        """Test provider inherits from str."""
        assert isinstance(BankProvider.PLAID, str)
        assert BankProvider.PLAID == "plaid"


class TestConnectionStatusEnum:
    """Tests for ConnectionStatus enum."""

    def test_pending_value(self):
        """Test pending status."""
        assert ConnectionStatus.PENDING.value == "pending"

    def test_active_value(self):
        """Test active status."""
        assert ConnectionStatus.ACTIVE.value == "active"

    def test_expired_value(self):
        """Test expired status."""
        assert ConnectionStatus.EXPIRED.value == "expired"

    def test_revoked_value(self):
        """Test revoked status."""
        assert ConnectionStatus.REVOKED.value == "revoked"

    def test_error_value(self):
        """Test error status."""
        assert ConnectionStatus.ERROR.value == "error"

    def test_disconnected_value(self):
        """Test disconnected status."""
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"


class TestConsentStatusEnum:
    """Tests for ConsentStatus enum."""

    def test_pending_value(self):
        """Test pending consent."""
        assert ConsentStatus.PENDING.value == "pending"

    def test_authorized_value(self):
        """Test authorized consent."""
        assert ConsentStatus.AUTHORIZED.value == "authorized"

    def test_rejected_value(self):
        """Test rejected consent."""
        assert ConsentStatus.REJECTED.value == "rejected"

    def test_expired_value(self):
        """Test expired consent."""
        assert ConsentStatus.EXPIRED.value == "expired"

    def test_revoked_value(self):
        """Test revoked consent."""
        assert ConsentStatus.REVOKED.value == "revoked"


class TestAccountTypeEnum:
    """Tests for AccountType enum."""

    def test_checking_value(self):
        """Test checking account type."""
        assert AccountType.CHECKING.value == "checking"

    def test_savings_value(self):
        """Test savings account type."""
        assert AccountType.SAVINGS.value == "savings"

    def test_credit_value(self):
        """Test credit account type."""
        assert AccountType.CREDIT.value == "credit"

    def test_loan_value(self):
        """Test loan account type."""
        assert AccountType.LOAN.value == "loan"

    def test_investment_value(self):
        """Test investment account type."""
        assert AccountType.INVESTMENT.value == "investment"

    def test_other_value(self):
        """Test other account type."""
        assert AccountType.OTHER.value == "other"


class TestTransactionCategoryEnum:
    """Tests for TransactionCategory enum."""

    def test_subscription_value(self):
        """Test subscription category."""
        assert TransactionCategory.SUBSCRIPTION.value == "subscription"

    def test_utilities_value(self):
        """Test utilities category."""
        assert TransactionCategory.UTILITIES.value == "utilities"

    def test_rent_value(self):
        """Test rent category."""
        assert TransactionCategory.RENT.value == "rent"

    def test_all_categories_exist(self):
        """Test all expected categories exist."""
        categories = [
            "subscription", "utilities", "rent", "insurance", "loan",
            "transfer", "income", "shopping", "food", "transport",
            "entertainment", "health", "other"
        ]
        for cat in categories:
            assert TransactionCategory(cat) is not None


# ============================================================================
# Model Tests - BankConnection
# ============================================================================


class TestBankConnectionModel:
    """Tests for BankConnection model."""

    def test_create_connection(self):
        """Test creating a bank connection."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="ob-monzo",
            institution_name="Monzo",
            access_token_encrypted="encrypted-token",
            item_id="item-123",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        assert connection.provider == BankProvider.TRUELAYER
        assert connection.institution_name == "Monzo"
        assert connection.status == ConnectionStatus.ACTIVE

    def test_is_active_property(self):
        """Test is_active property."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.PLAID,
            institution_id="ins_1",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        assert connection.is_active is True

        connection.status = ConnectionStatus.EXPIRED
        assert connection.is_active is False

    def test_needs_reauthorization(self):
        """Test needs_reauthorization property."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="bank",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        assert connection.needs_reauthorization is False

        connection.status = ConnectionStatus.EXPIRED
        assert connection.needs_reauthorization is True

        connection.status = ConnectionStatus.REVOKED
        assert connection.needs_reauthorization is True

        connection.status = ConnectionStatus.ERROR
        assert connection.needs_reauthorization is True

    def test_consent_is_valid(self):
        """Test consent_is_valid property."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="bank",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
            consent_expires_at=datetime.utcnow() + timedelta(days=30),
        )
        assert connection.consent_is_valid is True

        # Expired consent
        connection.consent_expires_at = datetime.utcnow() - timedelta(days=1)
        assert connection.consent_is_valid is False

        # Pending consent
        connection.consent_status = ConsentStatus.PENDING
        assert connection.consent_is_valid is False

    def test_mark_synced(self):
        """Test mark_synced method."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.PLAID,
            institution_id="bank",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
            error_code="SOME_ERROR",
            error_message="Previous error",
        )
        connection.mark_synced(cursor="new-cursor-123")

        assert connection.last_sync_at is not None
        assert connection.sync_cursor == "new-cursor-123"
        assert connection.error_code is None
        assert connection.error_message is None

    def test_mark_error(self):
        """Test mark_error method."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="bank",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        connection.mark_error("SYNC_ERROR", "Failed to sync transactions")

        assert connection.status == ConnectionStatus.ERROR
        assert connection.error_code == "SYNC_ERROR"
        assert connection.error_message == "Failed to sync transactions"

    def test_disconnect(self):
        """Test disconnect method."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="bank",
            institution_name="Bank",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        connection.disconnect()

        assert connection.status == ConnectionStatus.DISCONNECTED
        assert connection.consent_status == ConsentStatus.REVOKED

    def test_repr(self):
        """Test string representation."""
        connection = BankConnection(
            user_id="user-123",
            provider=BankProvider.TRUELAYER,
            institution_id="ob-monzo",
            institution_name="Monzo",
            access_token_encrypted="token",
            item_id="item",
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
        )
        repr_str = repr(connection)
        assert "Monzo" in repr_str
        assert "truelayer" in repr_str
        assert "active" in repr_str


# ============================================================================
# Model Tests - BankAccount
# ============================================================================


class TestBankAccountModel:
    """Tests for BankAccount model."""

    def test_create_account(self):
        """Test creating a bank account."""
        account = BankAccount(
            connection_id="conn-123",
            account_id_external="acc_123",
            name="Main Checking",
            account_type=AccountType.CHECKING,
            currency="GBP",
            current_balance=1500.50,
        )
        assert account.name == "Main Checking"
        assert account.account_type == AccountType.CHECKING
        assert account.currency == "GBP"

    def test_display_name_with_mask(self):
        """Test display_name with mask."""
        account = BankAccount(
            connection_id="conn-123",
            account_id_external="acc_123",
            name="Current Account",
            account_type=AccountType.CHECKING,
            currency="GBP",
            mask="4567",
        )
        assert account.display_name == "Current Account (****4567)"

    def test_display_name_without_mask(self):
        """Test display_name without mask."""
        account = BankAccount(
            connection_id="conn-123",
            account_id_external="acc_123",
            name="Current Account",
            account_type=AccountType.CHECKING,
            currency="GBP",
        )
        assert account.display_name == "Current Account"

    def test_repr(self):
        """Test string representation."""
        account = BankAccount(
            connection_id="conn-123",
            account_id_external="acc_123",
            name="Savings",
            account_type=AccountType.SAVINGS,
            currency="EUR",
        )
        repr_str = repr(account)
        assert "Savings" in repr_str
        assert "savings" in repr_str
        assert "EUR" in repr_str


# ============================================================================
# Model Tests - BankTransaction
# ============================================================================


class TestBankTransactionModel:
    """Tests for BankTransaction model."""

    def test_create_transaction(self):
        """Test creating a bank transaction."""
        transaction = BankTransaction(
            connection_id="conn-123",
            account_id="acc-123",
            transaction_id_external="txn_123",
            amount=-15.99,
            currency="GBP",
            description="NETFLIX.COM",
            merchant_name="Netflix",
            category=TransactionCategory.SUBSCRIPTION,
            date=datetime(2025, 1, 15),
        )
        assert transaction.amount == -15.99
        assert transaction.merchant_name == "Netflix"
        assert transaction.category == TransactionCategory.SUBSCRIPTION

    def test_is_debit(self):
        """Test is_debit property."""
        transaction = BankTransaction(
            connection_id="conn-123",
            account_id="acc-123",
            transaction_id_external="txn_123",
            amount=-50.00,
            currency="GBP",
            description="Purchase",
            date=datetime.utcnow(),
        )
        assert transaction.is_debit is True

        transaction.amount = 100.00  # Credit
        assert transaction.is_debit is False

    def test_absolute_amount(self):
        """Test absolute_amount property."""
        transaction = BankTransaction(
            connection_id="conn-123",
            account_id="acc-123",
            transaction_id_external="txn_123",
            amount=-75.50,
            currency="GBP",
            description="Purchase",
            date=datetime.utcnow(),
        )
        assert transaction.absolute_amount == 75.50

    def test_repr(self):
        """Test string representation."""
        transaction = BankTransaction(
            connection_id="conn-123",
            account_id="acc-123",
            transaction_id_external="txn_123",
            amount=-9.99,
            currency="GBP",
            description="SPOTIFY",
            merchant_name="Spotify",
            category=TransactionCategory.SUBSCRIPTION,
            date=datetime(2025, 1, 20),
        )
        repr_str = repr(transaction)
        assert "Spotify" in repr_str
        assert "-9.99" in repr_str


# ============================================================================
# Schema Tests - Connection Schemas
# ============================================================================


class TestBankConnectionSchemas:
    """Tests for bank connection Pydantic schemas."""

    def test_connection_create_defaults(self):
        """Test BankConnectionCreate with defaults."""
        schema = BankConnectionCreate()
        assert schema.provider == BankProviderEnum.TRUELAYER
        assert schema.country_code == "GB"
        assert schema.redirect_uri is None

    def test_connection_create_plaid(self):
        """Test BankConnectionCreate for Plaid."""
        schema = BankConnectionCreate(
            provider=BankProviderEnum.PLAID,
            country_code="US",
        )
        assert schema.provider == BankProviderEnum.PLAID
        assert schema.country_code == "US"

    def test_connection_link_response(self):
        """Test BankConnectionLinkResponse."""
        schema = BankConnectionLinkResponse(
            link_url="https://auth.truelayer.com/?...",
            link_token="token-123",
            expiration=datetime(2025, 1, 15, 12, 0, 0),
        )
        assert schema.link_url.startswith("https://")
        assert schema.link_token == "token-123"

    def test_connection_callback(self):
        """Test BankConnectionCallback."""
        schema = BankConnectionCallback(
            code="auth-code-123",
            state="state-abc",
        )
        assert schema.code == "auth-code-123"
        assert schema.state == "state-abc"

    def test_connection_response(self):
        """Test BankConnectionResponse."""
        schema = BankConnectionResponse(
            id="conn-123",
            provider=BankProviderEnum.TRUELAYER,
            institution_id="ob-monzo",
            institution_name="Monzo",
            institution_logo_url="https://example.com/logo.png",
            status=ConnectionStatusEnum.ACTIVE,
            consent_status=ConsentStatusEnum.AUTHORIZED,
            consent_expires_at=datetime(2025, 4, 15),
            accounts_count=2,
            last_sync_at=datetime(2025, 1, 15, 10, 0, 0),
            is_auto_sync_enabled=True,
            error_message=None,
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 15),
        )
        assert schema.institution_name == "Monzo"
        assert schema.accounts_count == 2

    def test_connection_update(self):
        """Test BankConnectionUpdate."""
        schema = BankConnectionUpdate(is_auto_sync_enabled=False)
        assert schema.is_auto_sync_enabled is False


# ============================================================================
# Schema Tests - Account Schemas
# ============================================================================


class TestBankAccountSchemas:
    """Tests for bank account Pydantic schemas."""

    def test_account_response(self):
        """Test BankAccountResponse."""
        schema = BankAccountResponse(
            id="acc-123",
            connection_id="conn-123",
            account_id_external="ext_acc_1",
            name="Current Account",
            official_name="Personal Current Account",
            account_type=AccountTypeEnum.CHECKING,
            subtype="checking",
            currency="GBP",
            current_balance=1500.00,
            available_balance=1450.00,
            credit_limit=None,
            mask="4567",
            is_syncing=True,
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 15),
        )
        assert schema.name == "Current Account"
        assert schema.display_name == "Current Account (****4567)"

    def test_account_update(self):
        """Test BankAccountUpdate."""
        schema = BankAccountUpdate(is_syncing=False)
        assert schema.is_syncing is False


# ============================================================================
# Schema Tests - Transaction Schemas
# ============================================================================


class TestBankTransactionSchemas:
    """Tests for bank transaction Pydantic schemas."""

    def test_transaction_response(self):
        """Test BankTransactionResponse."""
        schema = BankTransactionResponse(
            id="txn-123",
            connection_id="conn-123",
            account_id="acc-123",
            transaction_id_external="ext_txn_1",
            amount=-15.99,
            currency="GBP",
            description="NETFLIX.COM",
            merchant_name="Netflix",
            category=TransactionCategoryEnum.SUBSCRIPTION,
            category_raw="Service",
            date=datetime(2025, 1, 15),
            pending=False,
            is_recurring=True,
            recurring_stream_id="stream-123",
            matched_subscription_id="sub-123",
            created_at=datetime(2025, 1, 15),
        )
        assert schema.amount == -15.99
        assert schema.is_recurring is True

    def test_transaction_filters(self):
        """Test BankTransactionFilters."""
        schema = BankTransactionFilters(
            category=TransactionCategoryEnum.SUBSCRIPTION,
            is_recurring=True,
            min_amount=-100.00,
            max_amount=-5.00,
        )
        assert schema.is_recurring is True
        assert schema.min_amount == -100.00


# ============================================================================
# Schema Tests - Sync Schemas
# ============================================================================


class TestSyncSchemas:
    """Tests for sync-related schemas."""

    def test_sync_status_response(self):
        """Test SyncStatusResponse."""
        schema = SyncStatusResponse(
            connection_id="conn-123",
            status=ConnectionStatusEnum.ACTIVE,
            last_sync_at=datetime(2025, 1, 15, 10, 0, 0),
            next_sync_at=datetime(2025, 1, 16, 10, 0, 0),
            transactions_synced=150,
            new_transactions=5,
            error=None,
        )
        assert schema.transactions_synced == 150
        assert schema.new_transactions == 5

    def test_trigger_sync_request(self):
        """Test TriggerSyncRequest."""
        schema = TriggerSyncRequest(
            connection_id="conn-123",
            full_refresh=True,
        )
        assert schema.full_refresh is True

    def test_trigger_sync_response(self):
        """Test TriggerSyncResponse."""
        schema = TriggerSyncResponse(
            success=True,
            message="Synced 10 transactions",
            job_id="job-123",
        )
        assert schema.success is True


# ============================================================================
# Schema Tests - Recurring Schemas
# ============================================================================


class TestRecurringSchemas:
    """Tests for recurring detection schemas."""

    def test_recurring_stream_response(self):
        """Test RecurringStreamResponse."""
        schema = RecurringStreamResponse(
            stream_id="stream-123",
            merchant_name="Netflix",
            average_amount=15.99,
            currency="GBP",
            frequency="monthly",
            transaction_count=12,
            first_date=datetime(2024, 1, 15),
            last_date=datetime(2025, 1, 15),
            next_expected_date=datetime(2025, 2, 15),
            category=TransactionCategoryEnum.SUBSCRIPTION,
            is_active=True,
            matched_subscription_id=None,
        )
        assert schema.frequency == "monthly"
        assert schema.transaction_count == 12

    def test_recurring_streams_response(self):
        """Test RecurringStreamsResponse."""
        stream = RecurringStreamResponse(
            stream_id="stream-123",
            merchant_name="Netflix",
            average_amount=15.99,
            currency="GBP",
            frequency="monthly",
            transaction_count=12,
            first_date=datetime(2024, 1, 15),
            last_date=datetime(2025, 1, 15),
            next_expected_date=datetime(2025, 2, 15),
            category=TransactionCategoryEnum.SUBSCRIPTION,
            is_active=True,
        )
        schema = RecurringStreamsResponse(
            streams=[stream],
            total=1,
        )
        assert schema.total == 1
        assert len(schema.streams) == 1

    def test_match_subscription_request(self):
        """Test MatchSubscriptionRequest."""
        schema = MatchSubscriptionRequest(
            stream_id="stream-123",
            subscription_id="sub-456",
        )
        assert schema.stream_id == "stream-123"
        assert schema.subscription_id == "sub-456"


# ============================================================================
# Schema Tests - Stats
# ============================================================================


class TestBankingStatsSchemas:
    """Tests for banking statistics schemas."""

    def test_banking_stats_response(self):
        """Test BankingStatsResponse."""
        schema = BankingStatsResponse(
            total_connections=2,
            active_connections=1,
            total_accounts=5,
            total_transactions=150,
            recurring_streams_detected=8,
            matched_subscriptions=5,
            last_sync_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        assert schema.total_connections == 2
        assert schema.active_connections == 1
        assert schema.recurring_streams_detected == 8


# ============================================================================
# Service Tests - Category Mapping
# ============================================================================


class TestCategoryMapping:
    """Tests for category mapping from providers."""

    def test_plaid_category_map_exists(self):
        """Test Plaid category map is defined."""
        from src.services.open_banking_service import PLAID_CATEGORY_MAP

        assert "SUBSCRIPTION" in PLAID_CATEGORY_MAP
        assert "UTILITIES" in PLAID_CATEGORY_MAP
        assert "RENT" in PLAID_CATEGORY_MAP

    def test_truelayer_category_map_exists(self):
        """Test TrueLayer category map is defined."""
        from src.services.open_banking_service import TRUELAYER_CATEGORY_MAP

        assert "DIRECT_DEBIT" in TRUELAYER_CATEGORY_MAP
        assert "STANDING_ORDER" in TRUELAYER_CATEGORY_MAP
        assert "TRANSFER" in TRUELAYER_CATEGORY_MAP


# ============================================================================
# Service Tests - Account Type Mapping
# ============================================================================


class TestAccountTypeMapping:
    """Tests for account type mapping."""

    def test_map_checking_account(self):
        """Test mapping checking/current accounts."""
        from src.services.open_banking_service import OpenBankingService

        # Create a mock service (we only need the static method)
        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("checking") == AccountType.CHECKING
        assert service._map_account_type("current") == AccountType.CHECKING

    def test_map_savings_account(self):
        """Test mapping savings accounts."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("savings") == AccountType.SAVINGS
        assert service._map_account_type("saving") == AccountType.SAVINGS

    def test_map_credit_account(self):
        """Test mapping credit accounts."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("credit card") == AccountType.CREDIT

    def test_map_loan_account(self):
        """Test mapping loan accounts."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("loan") == AccountType.LOAN
        assert service._map_account_type("mortgage") == AccountType.LOAN

    def test_map_investment_account(self):
        """Test mapping investment accounts."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("investment") == AccountType.INVESTMENT
        assert service._map_account_type("brokerage") == AccountType.INVESTMENT

    def test_map_other_account(self):
        """Test mapping unknown account types."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)

        assert service._map_account_type("unknown") == AccountType.OTHER
        assert service._map_account_type("") == AccountType.OTHER
        assert service._map_account_type(None) == AccountType.OTHER


# ============================================================================
# Service Tests - Encryption
# ============================================================================


class TestEncryption:
    """Tests for token encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypting and decrypting a token."""
        from src.services.open_banking_service import OpenBankingService

        # Create a mock service
        service = OpenBankingService.__new__(OpenBankingService)
        service._fernet = service._get_fernet()

        original = "access-token-12345"
        encrypted = service._encrypt_token(original)
        decrypted = service._decrypt_token(encrypted)

        assert encrypted != original  # Should be encrypted
        assert decrypted == original  # Should decrypt back

    def test_encrypted_token_is_different_each_time(self):
        """Test that encryption produces different output (due to IV)."""
        from src.services.open_banking_service import OpenBankingService

        service = OpenBankingService.__new__(OpenBankingService)
        service._fernet = service._get_fernet()

        original = "access-token-12345"
        encrypted1 = service._encrypt_token(original)
        encrypted2 = service._encrypt_token(original)

        # Fernet uses random IV, so same input produces different output
        assert encrypted1 != encrypted2


# ============================================================================
# Provider Enum Schema Tests
# ============================================================================


class TestProviderEnumSchemas:
    """Tests for provider enum schemas."""

    def test_provider_enum_values(self):
        """Test BankProviderEnum values."""
        assert BankProviderEnum.PLAID.value == "plaid"
        assert BankProviderEnum.TRUELAYER.value == "truelayer"

    def test_status_enum_values(self):
        """Test ConnectionStatusEnum values."""
        assert ConnectionStatusEnum.PENDING.value == "pending"
        assert ConnectionStatusEnum.ACTIVE.value == "active"
        assert ConnectionStatusEnum.EXPIRED.value == "expired"

    def test_consent_enum_values(self):
        """Test ConsentStatusEnum values."""
        assert ConsentStatusEnum.AUTHORIZED.value == "authorized"
        assert ConsentStatusEnum.REJECTED.value == "rejected"

    def test_account_type_enum_values(self):
        """Test AccountTypeEnum values."""
        assert AccountTypeEnum.CHECKING.value == "checking"
        assert AccountTypeEnum.SAVINGS.value == "savings"
        assert AccountTypeEnum.CREDIT.value == "credit"

    def test_transaction_category_enum_values(self):
        """Test TransactionCategoryEnum values."""
        assert TransactionCategoryEnum.SUBSCRIPTION.value == "subscription"
        assert TransactionCategoryEnum.UTILITIES.value == "utilities"
        assert TransactionCategoryEnum.RENT.value == "rent"
