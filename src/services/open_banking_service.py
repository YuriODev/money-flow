"""Open Banking service for Plaid/TrueLayer integration.

This module provides the business logic for Open Banking operations,
including bank connection management, transaction syncing, and
recurring payment detection.

Sprint 5.7 - Open Banking Integration

Note: This implementation supports both Plaid and TrueLayer providers.
- TrueLayer: Recommended for UK/EU (99% UK bank coverage, PSD2 compliant)
- Plaid: Recommended for US (12,000+ institutions)
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
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
    BankConnectionCreate,
    BankConnectionLinkResponse,
    BankConnectionUpdate,
    BankingStatsResponse,
    RecurringStreamResponse,
    SyncStatusResponse,
)

logger = logging.getLogger(__name__)

# Category mapping from provider categories to our categories
PLAID_CATEGORY_MAP: dict[str, TransactionCategory] = {
    "SUBSCRIPTION": TransactionCategory.SUBSCRIPTION,
    "UTILITIES": TransactionCategory.UTILITIES,
    "RENT_AND_UTILITIES": TransactionCategory.RENT,
    "RENT": TransactionCategory.RENT,
    "INSURANCE": TransactionCategory.INSURANCE,
    "LOAN_PAYMENTS": TransactionCategory.LOAN,
    "TRANSFER": TransactionCategory.TRANSFER,
    "INCOME": TransactionCategory.INCOME,
    "GENERAL_MERCHANDISE": TransactionCategory.SHOPPING,
    "FOOD_AND_DRINK": TransactionCategory.FOOD,
    "TRANSPORTATION": TransactionCategory.TRANSPORT,
    "ENTERTAINMENT": TransactionCategory.ENTERTAINMENT,
    "MEDICAL": TransactionCategory.HEALTH,
}

TRUELAYER_CATEGORY_MAP: dict[str, TransactionCategory] = {
    "PURCHASE": TransactionCategory.SHOPPING,
    "BILL_PAYMENT": TransactionCategory.UTILITIES,
    "DIRECT_DEBIT": TransactionCategory.SUBSCRIPTION,
    "STANDING_ORDER": TransactionCategory.SUBSCRIPTION,
    "TRANSFER": TransactionCategory.TRANSFER,
    "INTEREST": TransactionCategory.INCOME,
    "ATM": TransactionCategory.OTHER,
}


class OpenBankingService:
    """Service for Open Banking operations.

    Handles bank connection lifecycle, transaction syncing, and
    recurring payment detection using Plaid or TrueLayer APIs.

    Attributes:
        db: Async database session.
        user_id: Current user's UUID.
        _fernet: Fernet cipher for token encryption.

    Example:
        >>> service = OpenBankingService(db, user_id)
        >>> link = await service.create_link_token(provider="truelayer")
        >>> connection = await service.exchange_token(code, state)
    """

    def __init__(self, db: AsyncSession, user_id: str) -> None:
        """Initialize Open Banking service.

        Args:
            db: Async database session.
            user_id: Current user's UUID.
        """
        self.db = db
        self.user_id = user_id
        self._fernet = self._get_fernet()

    def _get_fernet(self) -> Fernet:
        """Get Fernet cipher for token encryption.

        Uses the secret key from settings to derive an encryption key.

        Returns:
            Fernet cipher instance.
        """
        # Derive a 32-byte key from the secret key
        key = hashlib.sha256(settings.secret_key.encode()).digest()
        # Fernet requires base64 encoded 32 byte key
        import base64

        fernet_key = base64.urlsafe_b64encode(key)
        return Fernet(fernet_key)

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage.

        Args:
            token: Plain text token.

        Returns:
            Encrypted token string.
        """
        return self._fernet.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted: str) -> str:
        """Decrypt a stored token.

        Args:
            encrypted: Encrypted token string.

        Returns:
            Decrypted plain text token.
        """
        return self._fernet.decrypt(encrypted.encode()).decode()

    # =========================================================================
    # Connection Management
    # =========================================================================

    async def create_link_token(self, data: BankConnectionCreate) -> BankConnectionLinkResponse:
        """Create a link token for bank authorization.

        Generates a link URL and token for the user to authorize
        access to their bank account.

        Args:
            data: Connection creation parameters.

        Returns:
            Link response with URL and token.

        Note:
            In production, this would call Plaid's /link/token/create
            or TrueLayer's auth URL generator.
        """
        state = secrets.token_urlsafe(32)

        if data.provider == BankProvider.PLAID:
            # In production: Call Plaid API
            # client = plaid.Client(client_id, secret)
            # response = client.LinkToken.create({...})
            link_url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={state}"
            link_token = f"link-sandbox-{state[:16]}"
        else:
            # TrueLayer auth URL
            # In production: Use TrueLayer SDK
            redirect_uri = data.redirect_uri or settings.truelayer_redirect_uri
            link_url = (
                f"https://auth.truelayer.com/?response_type=code"
                f"&client_id={settings.truelayer_client_id}"
                f"&scope=accounts%20balance%20transactions"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
            link_token = state

        expiration = datetime.utcnow() + timedelta(hours=4)

        logger.info(f"Created link token for user {self.user_id}, provider={data.provider.value}")

        return BankConnectionLinkResponse(
            link_url=link_url,
            link_token=link_token,
            expiration=expiration,
        )

    async def exchange_token(
        self,
        code: str,
        state: str,
        provider: BankProvider = BankProvider.TRUELAYER,
    ) -> BankConnection:
        """Exchange authorization code for access token.

        Completes the OAuth flow by exchanging the auth code for
        access and refresh tokens, then creates the connection.

        Args:
            code: Authorization code from callback.
            state: State parameter for CSRF validation.
            provider: Banking API provider.

        Returns:
            Created bank connection.

        Note:
            In production, this would call the provider's token endpoint.
        """
        # In production: Exchange code for tokens via API
        # For Plaid: client.Item.public_token.exchange(public_token)
        # For TrueLayer: POST /connect/token

        # Simulated response for development
        access_token = f"access-{secrets.token_hex(16)}"
        refresh_token = f"refresh-{secrets.token_hex(16)}"
        item_id = f"item-{secrets.token_hex(8)}"

        # Create the connection
        connection = BankConnection(
            user_id=self.user_id,
            provider=provider,
            institution_id="sandbox-institution",
            institution_name="Sandbox Bank",
            access_token_encrypted=self._encrypt_token(access_token),
            refresh_token_encrypted=self._encrypt_token(refresh_token),
            item_id=item_id,
            status=ConnectionStatus.ACTIVE,
            consent_status=ConsentStatus.AUTHORIZED,
            consent_expires_at=datetime.utcnow() + timedelta(days=90),
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        logger.info(f"Created bank connection {connection.id} for user {self.user_id}")

        return connection

    async def get_connection(self, connection_id: str) -> BankConnection | None:
        """Get a bank connection by ID.

        Args:
            connection_id: Connection UUID.

        Returns:
            Connection if found and owned by user.
        """
        result = await self.db.execute(
            select(BankConnection).where(
                and_(
                    BankConnection.id == connection_id,
                    BankConnection.user_id == self.user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_connections(self) -> tuple[list[BankConnection], int]:
        """List all bank connections for the user.

        Returns:
            Tuple of (connections list, total count).
        """
        result = await self.db.execute(
            select(BankConnection)
            .where(BankConnection.user_id == self.user_id)
            .order_by(BankConnection.created_at.desc())
        )
        connections = list(result.scalars().all())
        return connections, len(connections)

    async def update_connection(
        self, connection_id: str, data: BankConnectionUpdate
    ) -> BankConnection | None:
        """Update bank connection settings.

        Args:
            connection_id: Connection UUID.
            data: Update data.

        Returns:
            Updated connection or None if not found.
        """
        connection = await self.get_connection(connection_id)
        if not connection:
            return None

        if data.is_auto_sync_enabled is not None:
            connection.is_auto_sync_enabled = data.is_auto_sync_enabled

        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def disconnect(self, connection_id: str) -> bool:
        """Disconnect a bank connection.

        Args:
            connection_id: Connection UUID.

        Returns:
            True if disconnected.
        """
        connection = await self.get_connection(connection_id)
        if not connection:
            return False

        connection.disconnect()
        await self.db.commit()

        logger.info(f"Disconnected bank connection {connection_id}")
        return True

    async def delete_connection(self, connection_id: str) -> bool:
        """Delete a bank connection and all associated data.

        Args:
            connection_id: Connection UUID.

        Returns:
            True if deleted.
        """
        connection = await self.get_connection(connection_id)
        if not connection:
            return False

        await self.db.delete(connection)
        await self.db.commit()

        logger.info(f"Deleted bank connection {connection_id}")
        return True

    # =========================================================================
    # Account Management
    # =========================================================================

    async def list_accounts(
        self, connection_id: str | None = None
    ) -> tuple[list[BankAccount], int]:
        """List bank accounts.

        Args:
            connection_id: Optional filter by connection.

        Returns:
            Tuple of (accounts list, total count).
        """
        query = (
            select(BankAccount).join(BankConnection).where(BankConnection.user_id == self.user_id)
        )

        if connection_id:
            query = query.where(BankAccount.connection_id == connection_id)

        result = await self.db.execute(query.order_by(BankAccount.name))
        accounts = list(result.scalars().all())
        return accounts, len(accounts)

    async def update_account(self, account_id: str, is_syncing: bool) -> BankAccount | None:
        """Update account sync setting.

        Args:
            account_id: Account UUID.
            is_syncing: Whether to sync this account.

        Returns:
            Updated account or None.
        """
        result = await self.db.execute(
            select(BankAccount)
            .join(BankConnection)
            .where(
                and_(
                    BankAccount.id == account_id,
                    BankConnection.user_id == self.user_id,
                )
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return None

        account.is_syncing = is_syncing
        await self.db.commit()
        await self.db.refresh(account)
        return account

    # =========================================================================
    # Transaction Syncing
    # =========================================================================

    async def sync_transactions(
        self, connection_id: str, full_refresh: bool = False
    ) -> SyncStatusResponse:
        """Sync transactions for a bank connection.

        Fetches new transactions from the provider API and
        stores them in the database.

        Args:
            connection_id: Connection UUID.
            full_refresh: Whether to re-fetch all transactions.

        Returns:
            Sync status response.

        Note:
            In production, this would call /transactions/sync (Plaid)
            or /data/v1/transactions (TrueLayer).
        """
        connection = await self.get_connection(connection_id)
        if not connection:
            return SyncStatusResponse(
                connection_id=connection_id,
                status=ConnectionStatus.ERROR,
                last_sync_at=None,
                next_sync_at=None,
                transactions_synced=0,
                new_transactions=0,
                error="Connection not found",
            )

        if connection.status != ConnectionStatus.ACTIVE:
            return SyncStatusResponse(
                connection_id=connection_id,
                status=connection.status,
                last_sync_at=connection.last_sync_at,
                next_sync_at=None,
                transactions_synced=0,
                new_transactions=0,
                error=f"Connection is {connection.status.value}",
            )

        try:
            # In production: Call provider API
            # For Plaid: client.Transactions.sync(access_token, cursor)
            # For TrueLayer: GET /data/v1/accounts/{id}/transactions

            # Get cursor for incremental sync (None for full refresh)
            _cursor = None if full_refresh else connection.sync_cursor
            new_count = 0

            # Simulated transaction fetch
            # In production, this would:
            # 1. Call API with _cursor for incremental sync
            # 2. Parse API response and create BankTransaction records
            # 3. Update cursor from API response

            connection.mark_synced(cursor=f"cursor-{datetime.utcnow().timestamp()}")
            await self.db.commit()

            logger.info(f"Synced transactions for connection {connection_id}, new={new_count}")

            return SyncStatusResponse(
                connection_id=connection_id,
                status=connection.status,
                last_sync_at=connection.last_sync_at,
                next_sync_at=datetime.utcnow() + timedelta(hours=24),
                transactions_synced=await self._count_transactions(connection_id),
                new_transactions=new_count,
            )

        except Exception as e:
            logger.error(f"Sync error for connection {connection_id}: {e}")
            connection.mark_error("SYNC_ERROR", str(e))
            await self.db.commit()

            return SyncStatusResponse(
                connection_id=connection_id,
                status=ConnectionStatus.ERROR,
                last_sync_at=connection.last_sync_at,
                next_sync_at=None,
                transactions_synced=0,
                new_transactions=0,
                error=str(e),
            )

    async def _count_transactions(self, connection_id: str) -> int:
        """Count transactions for a connection."""
        result = await self.db.execute(
            select(func.count(BankTransaction.id)).where(
                BankTransaction.connection_id == connection_id
            )
        )
        return result.scalar_one()

    async def list_transactions(
        self,
        connection_id: str | None = None,
        account_id: str | None = None,
        category: TransactionCategory | None = None,
        is_recurring: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[BankTransaction], int, bool]:
        """List transactions with filters.

        Args:
            connection_id: Filter by connection.
            account_id: Filter by account.
            category: Filter by category.
            is_recurring: Filter recurring only.
            start_date: Start date filter.
            end_date: End date filter.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            Tuple of (transactions, total, has_more).
        """
        query = (
            select(BankTransaction)
            .join(BankConnection)
            .where(BankConnection.user_id == self.user_id)
        )

        if connection_id:
            query = query.where(BankTransaction.connection_id == connection_id)
        if account_id:
            query = query.where(BankTransaction.account_id == account_id)
        if category:
            query = query.where(BankTransaction.category == category)
        if is_recurring is not None:
            query = query.where(BankTransaction.is_recurring == is_recurring)
        if start_date:
            query = query.where(BankTransaction.date >= start_date)
        if end_date:
            query = query.where(BankTransaction.date <= end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Fetch page
        query = query.order_by(BankTransaction.date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        transactions = list(result.scalars().all())

        has_more = offset + len(transactions) < total

        return transactions, total, has_more

    # =========================================================================
    # Recurring Detection
    # =========================================================================

    async def detect_recurring_payments(
        self, connection_id: str | None = None
    ) -> list[RecurringStreamResponse]:
        """Detect recurring payment patterns from transactions.

        Analyzes transaction history to identify recurring payments
        based on merchant name, amount consistency, and timing.

        Args:
            connection_id: Optional filter by connection.

        Returns:
            List of detected recurring streams.

        Note:
            For Plaid, this would use /transactions/recurring/get
        """
        # Get transactions grouped by merchant
        query = (
            select(
                BankTransaction.merchant_name,
                func.count(BankTransaction.id).label("count"),
                func.avg(BankTransaction.amount).label("avg_amount"),
                func.min(BankTransaction.date).label("first_date"),
                func.max(BankTransaction.date).label("last_date"),
                BankTransaction.currency,
                BankTransaction.category,
            )
            .join(BankConnection)
            .where(
                and_(
                    BankConnection.user_id == self.user_id,
                    BankTransaction.merchant_name.isnot(None),
                    BankTransaction.amount < 0,  # Debits only
                )
            )
            .group_by(
                BankTransaction.merchant_name,
                BankTransaction.currency,
                BankTransaction.category,
            )
            .having(func.count(BankTransaction.id) >= 3)  # At least 3 occurrences
        )

        if connection_id:
            query = query.where(BankTransaction.connection_id == connection_id)

        result = await self.db.execute(query)
        rows = result.all()

        streams = []
        for row in rows:
            # Estimate frequency based on date range and count
            date_range = (row.last_date - row.first_date).days
            if date_range > 0 and row.count > 1:
                avg_days = date_range / (row.count - 1)
                if avg_days <= 10:
                    frequency = "weekly"
                elif avg_days <= 20:
                    frequency = "biweekly"
                elif avg_days <= 40:
                    frequency = "monthly"
                elif avg_days <= 100:
                    frequency = "quarterly"
                else:
                    frequency = "yearly"
            else:
                frequency = "unknown"

            # Predict next date
            if frequency == "weekly":
                next_date = row.last_date + timedelta(days=7)
            elif frequency == "biweekly":
                next_date = row.last_date + timedelta(days=14)
            elif frequency == "monthly":
                next_date = row.last_date + timedelta(days=30)
            elif frequency == "quarterly":
                next_date = row.last_date + timedelta(days=90)
            elif frequency == "yearly":
                next_date = row.last_date + timedelta(days=365)
            else:
                next_date = None

            stream_id = hashlib.md5(f"{row.merchant_name}:{row.currency}".encode()).hexdigest()[:16]

            streams.append(
                RecurringStreamResponse(
                    stream_id=stream_id,
                    merchant_name=row.merchant_name,
                    average_amount=abs(row.avg_amount),
                    currency=row.currency,
                    frequency=frequency,
                    transaction_count=row.count,
                    first_date=row.first_date,
                    last_date=row.last_date,
                    next_expected_date=next_date,
                    category=row.category,
                    is_active=next_date and next_date > datetime.utcnow(),
                )
            )

        return sorted(streams, key=lambda s: s.transaction_count, reverse=True)

    async def match_stream_to_subscription(self, stream_id: str, subscription_id: str) -> int:
        """Match a recurring stream to a subscription.

        Updates all transactions in the stream with the subscription ID.

        Args:
            stream_id: Recurring stream ID.
            subscription_id: Subscription UUID to match.

        Returns:
            Number of transactions updated.
        """
        # In a real implementation, we'd update transactions
        # based on the stream_id (derived from merchant + currency)
        # For now, return 0 as we don't have the mapping
        logger.info(f"Matched stream {stream_id} to subscription {subscription_id}")
        return 0

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_stats(self) -> BankingStatsResponse:
        """Get banking statistics for the user.

        Returns:
            Banking statistics.
        """
        # Count connections
        conn_result = await self.db.execute(
            select(
                func.count(BankConnection.id).label("total"),
                func.count(BankConnection.id)
                .filter(BankConnection.status == ConnectionStatus.ACTIVE)
                .label("active"),
            ).where(BankConnection.user_id == self.user_id)
        )
        conn_stats = conn_result.one()

        # Count accounts
        acct_result = await self.db.execute(
            select(func.count(BankAccount.id))
            .join(BankConnection)
            .where(BankConnection.user_id == self.user_id)
        )
        total_accounts = acct_result.scalar_one()

        # Count transactions
        txn_result = await self.db.execute(
            select(
                func.count(BankTransaction.id).label("total"),
                func.count(BankTransaction.id)
                .filter(BankTransaction.is_recurring.is_(True))
                .label("recurring"),
                func.count(BankTransaction.id)
                .filter(BankTransaction.matched_subscription_id.isnot(None))
                .label("matched"),
            )
            .join(BankConnection)
            .where(BankConnection.user_id == self.user_id)
        )
        txn_stats = txn_result.one()

        # Last sync time
        last_sync_result = await self.db.execute(
            select(func.max(BankConnection.last_sync_at)).where(
                BankConnection.user_id == self.user_id
            )
        )
        last_sync = last_sync_result.scalar_one()

        return BankingStatsResponse(
            total_connections=conn_stats.total,
            active_connections=conn_stats.active,
            total_accounts=total_accounts,
            total_transactions=txn_stats.total,
            recurring_streams_detected=txn_stats.recurring,
            matched_subscriptions=txn_stats.matched,
            last_sync_at=last_sync,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _map_plaid_category(self, categories: list[str]) -> TransactionCategory:
        """Map Plaid category to our category.

        Args:
            categories: Plaid category hierarchy.

        Returns:
            Mapped transaction category.
        """
        for cat in categories:
            if cat in PLAID_CATEGORY_MAP:
                return PLAID_CATEGORY_MAP[cat]
        return TransactionCategory.OTHER

    def _map_truelayer_category(self, category: str) -> TransactionCategory:
        """Map TrueLayer category to our category.

        Args:
            category: TrueLayer transaction category.

        Returns:
            Mapped transaction category.
        """
        return TRUELAYER_CATEGORY_MAP.get(category, TransactionCategory.OTHER)

    def _map_account_type(self, subtype: str) -> AccountType:
        """Map provider account subtype to our account type.

        Args:
            subtype: Provider account subtype.

        Returns:
            Mapped account type.
        """
        subtype_lower = subtype.lower() if subtype else ""

        if "checking" in subtype_lower or "current" in subtype_lower:
            return AccountType.CHECKING
        elif "saving" in subtype_lower:
            return AccountType.SAVINGS
        elif "credit" in subtype_lower:
            return AccountType.CREDIT
        elif "loan" in subtype_lower or "mortgage" in subtype_lower:
            return AccountType.LOAN
        elif "invest" in subtype_lower or "brokerage" in subtype_lower:
            return AccountType.INVESTMENT
        else:
            return AccountType.OTHER
