"""Integration API endpoints for IFTTT/Zapier.

This module provides API endpoints for managing external integrations,
including API keys, REST Hook subscriptions, and sample data.

Sprint 5.6 - IFTTT/Zapier Integration

Endpoints:
- GET /api/v1/integrations/events - List available event types
- GET /api/v1/integrations/stats - Get integration statistics

API Keys:
- GET /api/v1/integrations/api-keys - List API keys
- POST /api/v1/integrations/api-keys - Create API key
- DELETE /api/v1/integrations/api-keys/{id} - Revoke API key

REST Hooks (Zapier/IFTTT subscription endpoints):
- POST /api/v1/integrations/hooks/subscribe - Subscribe to events
- DELETE /api/v1/integrations/hooks/{id} - Unsubscribe
- GET /api/v1/integrations/hooks - List subscriptions
- GET /api/v1/integrations/hooks/sample - Get sample data
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.integration import IntegrationStatus, IntegrationType
from src.models.user import User
from src.schemas.integration import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyListResponse,
    APIKeyResponse,
    EventTypeInfo,
    IntegrationStatsResponse,
    IntegrationStatusEnum,
    IntegrationTypeEnum,
    RestHookListResponse,
    RestHookResponse,
    RestHookSubscribe,
    SampleDataResponse,
)
from src.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

# API Key header for external service authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_integration_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntegrationService:
    """Create IntegrationService instance for the current user."""
    return IntegrationService(db, current_user.id)


async def get_user_from_api_key(
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get user from API key for external service authentication.

    Returns None if no API key provided (allows falling back to JWT).
    """
    if not api_key:
        return None

    # Validate API key
    service = IntegrationService(db, "")  # User ID not needed for validation
    api_key_obj, error = await service.validate_api_key(api_key)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    # Get user
    from sqlalchemy import select

    from src.models.user import User

    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ============================================================================
# Event Types
# ============================================================================


@router.get("/events", response_model=list[EventTypeInfo])
async def list_event_types() -> list[EventTypeInfo]:
    """List all available event types for integrations.

    Returns event types with descriptions and sample payloads.
    Used by Zapier/IFTTT to show available triggers.

    Returns:
        List of event type information.
    """
    events = [
        EventTypeInfo(
            name="subscription.created",
            description="Triggered when a new subscription is created",
            sample_payload={
                "subscription_id": "uuid",
                "name": "Netflix",
                "amount": 15.99,
                "currency": "GBP",
                "frequency": "monthly",
                "next_payment_date": "2025-01-15T00:00:00Z",
                "category": "Entertainment",
            },
        ),
        EventTypeInfo(
            name="subscription.updated",
            description="Triggered when a subscription is modified",
            sample_payload={
                "subscription_id": "uuid",
                "name": "Netflix Premium",
                "amount": 17.99,
                "currency": "GBP",
                "frequency": "monthly",
                "next_payment_date": "2025-01-15T00:00:00Z",
                "category": "Entertainment",
            },
        ),
        EventTypeInfo(
            name="subscription.deleted",
            description="Triggered when a subscription is cancelled/deleted",
            sample_payload={
                "subscription_id": "uuid",
                "name": "Cancelled Service",
                "amount": 9.99,
                "currency": "GBP",
                "frequency": "monthly",
            },
        ),
        EventTypeInfo(
            name="payment.due",
            description="Triggered when a payment is due soon",
            sample_payload={
                "subscription_id": "uuid",
                "subscription_name": "Netflix",
                "amount": 15.99,
                "currency": "GBP",
                "payment_date": "2025-01-15T00:00:00Z",
                "status": "due",
                "days_until_due": 3,
            },
        ),
        EventTypeInfo(
            name="payment.overdue",
            description="Triggered when a payment is past due",
            sample_payload={
                "subscription_id": "uuid",
                "subscription_name": "Gym Membership",
                "amount": 29.99,
                "currency": "GBP",
                "payment_date": "2025-01-10T00:00:00Z",
                "status": "overdue",
                "days_until_due": -2,
            },
        ),
        EventTypeInfo(
            name="payment.completed",
            description="Triggered when a payment is marked as completed",
            sample_payload={
                "subscription_id": "uuid",
                "subscription_name": "Spotify",
                "amount": 10.99,
                "currency": "GBP",
                "payment_date": "2025-01-15T00:00:00Z",
                "status": "completed",
            },
        ),
        EventTypeInfo(
            name="payment.skipped",
            description="Triggered when a payment is skipped",
            sample_payload={
                "subscription_id": "uuid",
                "subscription_name": "Paused Subscription",
                "amount": 5.99,
                "currency": "GBP",
                "payment_date": "2025-01-15T00:00:00Z",
                "status": "skipped",
            },
        ),
        EventTypeInfo(
            name="budget.alert",
            description="Triggered when category spending exceeds budget",
            sample_payload={
                "category": "Entertainment",
                "budget_limit": 100.00,
                "current_spend": 115.50,
                "percent_used": 115.5,
                "currency": "GBP",
            },
        ),
        EventTypeInfo(
            name="import.completed",
            description="Triggered when a bank statement import finishes",
            sample_payload={
                "import_id": "uuid",
                "file_name": "statement.csv",
                "bank_name": "Monzo",
                "subscriptions_detected": 5,
                "subscriptions_imported": 3,
            },
        ),
        EventTypeInfo(
            name="calendar.synced",
            description="Triggered when calendar sync completes",
            sample_payload={
                "sync_type": "google",
                "events_synced": 12,
                "calendar_name": "Money Flow Payments",
            },
        ),
    ]
    return events


# ============================================================================
# Statistics
# ============================================================================


@router.get("/stats", response_model=IntegrationStatsResponse)
async def get_integration_stats(
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationStatsResponse:
    """Get integration statistics for the current user.

    Returns aggregate stats about API keys and REST Hook subscriptions.

    Returns:
        Integration statistics.
    """
    stats = await service.get_stats()
    return IntegrationStatsResponse(**stats)


# ============================================================================
# API Keys
# ============================================================================


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    service: IntegrationService = Depends(get_integration_service),
) -> APIKeyListResponse:
    """List all API keys for the current user.

    Returns:
        List of API keys (without secrets).
    """
    keys, total = await service.list_api_keys()
    return APIKeyListResponse(
        keys=[APIKeyResponse.model_validate(k) for k in keys],
        total=total,
    )


@router.post(
    "/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    data: APIKeyCreate,
    service: IntegrationService = Depends(get_integration_service),
) -> APIKeyCreatedResponse:
    """Create a new API key.

    The API key is only returned once in this response.
    Store it securely - it cannot be retrieved again.

    Args:
        data: API key creation data.

    Returns:
        Created API key with the secret (shown once).
    """
    api_key, full_key = await service.create_api_key(data)

    logger.info(f"Created API key {api_key.id}")

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=full_key,
        key_prefix=api_key.key_prefix,
        integration_type=IntegrationTypeEnum(api_key.integration_type.value),
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    service: IntegrationService = Depends(get_integration_service),
) -> None:
    """Revoke an API key.

    The key will no longer be valid for authentication.

    Args:
        key_id: API key UUID.

    Raises:
        HTTPException: 404 if key not found.
    """
    revoked = await service.revoke_api_key(key_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )


# ============================================================================
# REST Hooks (Subscribe/Unsubscribe endpoints for Zapier/IFTTT)
# ============================================================================


@router.post(
    "/hooks/subscribe",
    response_model=RestHookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_hook(
    data: RestHookSubscribe,
    integration_type: IntegrationTypeEnum = Query(
        IntegrationTypeEnum.CUSTOM,
        description="Type of integration",
    ),
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
    api_key_user: User | None = Depends(get_user_from_api_key),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RestHookResponse:
    """Subscribe to events via REST Hook.

    Called by Zapier/IFTTT when a user enables a trigger.
    Can be authenticated via API key or JWT token.

    Args:
        data: Subscription data with target_url and event_type.
        integration_type: Type of integration.

    Returns:
        Created subscription.
    """
    # Use API key user if available, otherwise JWT user
    user = api_key_user or current_user
    service = IntegrationService(db, user.id)

    # Get API key ID if authenticated via API key
    api_key_id = None
    if api_key:
        api_key_obj, _ = await service.validate_api_key(api_key)
        if api_key_obj:
            api_key_id = api_key_obj.id

    subscription = await service.subscribe(
        data,
        IntegrationType(integration_type.value),
        api_key_id,
    )

    return RestHookResponse.model_validate(subscription)


@router.delete("/hooks/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_hook(
    subscription_id: str,
    api_key_user: User | None = Depends(get_user_from_api_key),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Unsubscribe from events.

    Called by Zapier/IFTTT when a user disables a trigger.

    Args:
        subscription_id: Subscription UUID.

    Raises:
        HTTPException: 404 if subscription not found.
    """
    user = api_key_user or current_user
    service = IntegrationService(db, user.id)

    unsubscribed = await service.unsubscribe(subscription_id)
    if not unsubscribed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )


@router.get("/hooks", response_model=RestHookListResponse)
async def list_hooks(
    event_type: str | None = Query(None, description="Filter by event type"),
    status_filter: IntegrationStatusEnum | None = Query(
        None, alias="status", description="Filter by status"
    ),
    service: IntegrationService = Depends(get_integration_service),
) -> RestHookListResponse:
    """List REST Hook subscriptions.

    Args:
        event_type: Optional event type filter.
        status_filter: Optional status filter.

    Returns:
        List of subscriptions.
    """
    hook_status = None
    if status_filter:
        hook_status = IntegrationStatus(status_filter.value)

    subscriptions, total = await service.list_subscriptions(
        event_type=event_type,
        status=hook_status,
    )

    return RestHookListResponse(
        subscriptions=[RestHookResponse.model_validate(s) for s in subscriptions],
        total=total,
    )


@router.get("/hooks/sample", response_model=SampleDataResponse)
async def get_sample_data(
    event_type: str = Query(..., description="Event type to get samples for"),
    limit: int = Query(3, ge=1, le=10, description="Number of samples"),
    api_key_user: User | None = Depends(get_user_from_api_key),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SampleDataResponse:
    """Get sample event data for Zapier field mapping.

    Zapier calls this endpoint to show users what fields
    are available when setting up triggers.

    Args:
        event_type: Event type to get samples for.
        limit: Maximum number of samples (1-10).

    Returns:
        Sample event payloads.
    """
    user = api_key_user or current_user
    service = IntegrationService(db, user.id)

    samples = await service.get_sample_data(event_type, limit)

    return SampleDataResponse(samples=samples)
