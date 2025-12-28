"""Open Banking API endpoints.

This module provides API endpoints for Open Banking operations,
including bank connection management, transaction syncing, and
recurring payment detection.

Sprint 5.7 - Open Banking Integration

Endpoints:
- POST /api/v1/banking/connect - Initiate bank connection
- POST /api/v1/banking/callback - OAuth callback
- GET /api/v1/banking/connections - List connections
- GET /api/v1/banking/connections/{id} - Get connection details
- PATCH /api/v1/banking/connections/{id} - Update connection
- DELETE /api/v1/banking/connections/{id} - Disconnect/delete

Accounts:
- GET /api/v1/banking/accounts - List accounts
- PATCH /api/v1/banking/accounts/{id} - Update account settings

Transactions:
- GET /api/v1/banking/transactions - List transactions
- POST /api/v1/banking/sync - Trigger transaction sync

Recurring:
- GET /api/v1/banking/recurring - Detect recurring payments
- POST /api/v1/banking/recurring/match - Match to subscription

Stats:
- GET /api/v1/banking/stats - Get banking statistics
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.bank_connection import (
    BankProvider,
    TransactionCategory,
)
from src.models.user import User
from src.schemas.bank_connection import (
    BankAccountListResponse,
    BankAccountResponse,
    BankAccountUpdate,
    BankConnectionCallback,
    BankConnectionCreate,
    BankConnectionLinkResponse,
    BankConnectionListResponse,
    BankConnectionResponse,
    BankConnectionUpdate,
    BankingStatsResponse,
    BankProviderEnum,
    BankTransactionListResponse,
    BankTransactionResponse,
    ConnectionStatusEnum,
    MatchSubscriptionRequest,
    RecurringStreamsResponse,
    SyncStatusResponse,
    TransactionCategoryEnum,
    TriggerSyncRequest,
    TriggerSyncResponse,
)
from src.services.open_banking_service import OpenBankingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banking", tags=["banking"])


def get_banking_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpenBankingService:
    """Create OpenBankingService instance for the current user."""
    return OpenBankingService(db, current_user.id)


# ============================================================================
# Connection Management
# ============================================================================


@router.post("/connect", response_model=BankConnectionLinkResponse)
async def initiate_connection(
    data: BankConnectionCreate,
    service: OpenBankingService = Depends(get_banking_service),
) -> BankConnectionLinkResponse:
    """Initiate a bank connection.

    Creates a link token/URL for the user to authorize access
    to their bank account via Plaid or TrueLayer.

    Args:
        data: Connection parameters (provider, country code).

    Returns:
        Link response with authorization URL and token.
    """
    return await service.create_link_token(data)


@router.post("/callback", response_model=BankConnectionResponse)
async def handle_callback(
    data: BankConnectionCallback,
    provider: BankProviderEnum = Query(BankProviderEnum.TRUELAYER),
    service: OpenBankingService = Depends(get_banking_service),
) -> BankConnectionResponse:
    """Handle OAuth callback from bank authorization.

    Exchanges the authorization code for access tokens and
    creates the bank connection.

    Args:
        data: Callback parameters (code, state).
        provider: Banking API provider.

    Returns:
        Created bank connection.
    """
    connection = await service.exchange_token(
        code=data.code,
        state=data.state,
        provider=BankProvider(provider.value),
    )
    return BankConnectionResponse.model_validate(connection)


@router.get("/connections", response_model=BankConnectionListResponse)
async def list_connections(
    service: OpenBankingService = Depends(get_banking_service),
) -> BankConnectionListResponse:
    """List all bank connections for the current user.

    Returns:
        List of bank connections.
    """
    connections, total = await service.list_connections()
    return BankConnectionListResponse(
        connections=[BankConnectionResponse.model_validate(c) for c in connections],
        total=total,
    )


@router.get("/connections/{connection_id}", response_model=BankConnectionResponse)
async def get_connection(
    connection_id: str,
    service: OpenBankingService = Depends(get_banking_service),
) -> BankConnectionResponse:
    """Get details of a specific bank connection.

    Args:
        connection_id: Connection UUID.

    Returns:
        Bank connection details.

    Raises:
        HTTPException: 404 if not found.
    """
    connection = await service.get_connection(connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found",
        )
    return BankConnectionResponse.model_validate(connection)


@router.patch("/connections/{connection_id}", response_model=BankConnectionResponse)
async def update_connection(
    connection_id: str,
    data: BankConnectionUpdate,
    service: OpenBankingService = Depends(get_banking_service),
) -> BankConnectionResponse:
    """Update bank connection settings.

    Args:
        connection_id: Connection UUID.
        data: Update data.

    Returns:
        Updated bank connection.

    Raises:
        HTTPException: 404 if not found.
    """
    connection = await service.update_connection(connection_id, data)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found",
        )
    return BankConnectionResponse.model_validate(connection)


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    permanent: bool = Query(False, description="Delete permanently (vs just disconnect)"),
    service: OpenBankingService = Depends(get_banking_service),
) -> None:
    """Disconnect or delete a bank connection.

    Args:
        connection_id: Connection UUID.
        permanent: If true, delete all data. Otherwise just disconnect.

    Raises:
        HTTPException: 404 if not found.
    """
    if permanent:
        deleted = await service.delete_connection(connection_id)
    else:
        deleted = await service.disconnect(connection_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found",
        )


# ============================================================================
# Account Management
# ============================================================================


@router.get("/accounts", response_model=BankAccountListResponse)
async def list_accounts(
    connection_id: str | None = Query(None, description="Filter by connection"),
    service: OpenBankingService = Depends(get_banking_service),
) -> BankAccountListResponse:
    """List bank accounts.

    Args:
        connection_id: Optional filter by connection.

    Returns:
        List of bank accounts.
    """
    accounts, total = await service.list_accounts(connection_id)
    return BankAccountListResponse(
        accounts=[BankAccountResponse.model_validate(a) for a in accounts],
        total=total,
    )


@router.patch("/accounts/{account_id}", response_model=BankAccountResponse)
async def update_account(
    account_id: str,
    data: BankAccountUpdate,
    service: OpenBankingService = Depends(get_banking_service),
) -> BankAccountResponse:
    """Update bank account settings.

    Args:
        account_id: Account UUID.
        data: Update data.

    Returns:
        Updated bank account.

    Raises:
        HTTPException: 404 if not found.
    """
    if data.is_syncing is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided",
        )

    account = await service.update_account(account_id, data.is_syncing)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )
    return BankAccountResponse.model_validate(account)


# ============================================================================
# Transaction Syncing
# ============================================================================


@router.get("/transactions", response_model=BankTransactionListResponse)
async def list_transactions(
    connection_id: str | None = Query(None),
    account_id: str | None = Query(None),
    category: TransactionCategoryEnum | None = Query(None),
    is_recurring: bool | None = Query(None),
    start_date: str | None = Query(None, description="ISO date string"),
    end_date: str | None = Query(None, description="ISO date string"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: OpenBankingService = Depends(get_banking_service),
) -> BankTransactionListResponse:
    """List bank transactions with filters.

    Args:
        connection_id: Filter by connection.
        account_id: Filter by account.
        category: Filter by category.
        is_recurring: Filter recurring only.
        start_date: Start date filter (ISO format).
        end_date: End date filter (ISO format).
        limit: Max results (1-500).
        offset: Pagination offset.

    Returns:
        List of transactions with pagination.
    """
    from datetime import datetime

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    cat = TransactionCategory(category.value) if category else None

    transactions, total, has_more = await service.list_transactions(
        connection_id=connection_id,
        account_id=account_id,
        category=cat,
        is_recurring=is_recurring,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset,
    )

    return BankTransactionListResponse(
        transactions=[BankTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        has_more=has_more,
    )


@router.post("/sync", response_model=TriggerSyncResponse)
async def trigger_sync(
    data: TriggerSyncRequest,
    service: OpenBankingService = Depends(get_banking_service),
) -> TriggerSyncResponse:
    """Trigger transaction sync for a connection.

    Args:
        data: Sync request with connection ID.

    Returns:
        Sync trigger response.
    """
    # Verify connection exists
    connection = await service.get_connection(data.connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found",
        )

    # Trigger sync
    result = await service.sync_transactions(data.connection_id, full_refresh=data.full_refresh)

    if result.error:
        return TriggerSyncResponse(
            success=False,
            message=f"Sync failed: {result.error}",
            job_id=None,
        )

    return TriggerSyncResponse(
        success=True,
        message=f"Synced {result.new_transactions} new transactions",
        job_id=None,  # Would be job ID if async
    )


@router.get("/sync/{connection_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    connection_id: str,
    service: OpenBankingService = Depends(get_banking_service),
) -> SyncStatusResponse:
    """Get sync status for a connection.

    Args:
        connection_id: Connection UUID.

    Returns:
        Current sync status.
    """
    connection = await service.get_connection(connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found",
        )

    from datetime import timedelta

    return SyncStatusResponse(
        connection_id=connection_id,
        status=ConnectionStatusEnum(connection.status.value),
        last_sync_at=connection.last_sync_at,
        next_sync_at=(
            connection.last_sync_at + timedelta(hours=24)
            if connection.last_sync_at and connection.is_auto_sync_enabled
            else None
        ),
        transactions_synced=await service._count_transactions(connection_id),
        new_transactions=0,
        error=connection.error_message,
    )


# ============================================================================
# Recurring Detection
# ============================================================================


@router.get("/recurring", response_model=RecurringStreamsResponse)
async def detect_recurring(
    connection_id: str | None = Query(None, description="Filter by connection"),
    service: OpenBankingService = Depends(get_banking_service),
) -> RecurringStreamsResponse:
    """Detect recurring payment patterns.

    Analyzes transaction history to identify recurring payments
    based on merchant, amount, and timing patterns.

    Args:
        connection_id: Optional filter by connection.

    Returns:
        List of detected recurring streams.
    """
    streams = await service.detect_recurring_payments(connection_id)
    return RecurringStreamsResponse(
        streams=streams,
        total=len(streams),
    )


@router.post("/recurring/match", status_code=status.HTTP_200_OK)
async def match_recurring_to_subscription(
    data: MatchSubscriptionRequest,
    service: OpenBankingService = Depends(get_banking_service),
) -> dict:
    """Match a recurring stream to a subscription.

    Links detected recurring payments to an existing subscription
    for better tracking and reconciliation.

    Args:
        data: Match request with stream and subscription IDs.

    Returns:
        Number of transactions matched.
    """
    count = await service.match_stream_to_subscription(data.stream_id, data.subscription_id)
    return {"matched_transactions": count}


# ============================================================================
# Statistics
# ============================================================================


@router.get("/stats", response_model=BankingStatsResponse)
async def get_banking_stats(
    service: OpenBankingService = Depends(get_banking_service),
) -> BankingStatsResponse:
    """Get banking statistics for the current user.

    Returns aggregate stats about connections, accounts,
    transactions, and recurring patterns.

    Returns:
        Banking statistics.
    """
    return await service.get_stats()
