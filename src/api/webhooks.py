"""Webhook API endpoints.

This module provides API endpoints for managing webhook subscriptions
and viewing delivery logs.

Sprint 5.6 - Webhooks System

Endpoints:
- GET /api/v1/webhooks - List webhooks
- POST /api/v1/webhooks - Create webhook
- GET /api/v1/webhooks/{id} - Get webhook details
- PATCH /api/v1/webhooks/{id} - Update webhook
- DELETE /api/v1/webhooks/{id} - Delete webhook
- POST /api/v1/webhooks/{id}/test - Test webhook
- POST /api/v1/webhooks/{id}/regenerate-secret - Regenerate secret
- GET /api/v1/webhooks/{id}/deliveries - List deliveries
- GET /api/v1/webhooks/stats - Get statistics
- GET /api/v1/webhooks/events - List available event types
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.user import User
from src.models.webhook import DeliveryStatus, WebhookStatus
from src.schemas.webhook import (
    DeliveryListResponse,
    DeliveryResponse,
    DeliveryStatusEnum,
    WebhookCreate,
    WebhookEventEnum,
    WebhookListResponse,
    WebhookResponse,
    WebhookSecretResponse,
    WebhookStatsResponse,
    WebhookStatusEnum,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)
from src.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_webhook_service(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WebhookService:
    """Create WebhookService instance for the current user."""
    return WebhookService(db, current_user.id)


@router.get("/events", response_model=list[dict])
async def list_event_types() -> list[dict]:
    """List all available webhook event types.

    Returns a list of event types with descriptions.

    Returns:
        List of event type objects with name and description.
    """
    events = [
        {
            "name": WebhookEventEnum.SUBSCRIPTION_CREATED.value,
            "description": "Triggered when a new subscription is created",
        },
        {
            "name": WebhookEventEnum.SUBSCRIPTION_UPDATED.value,
            "description": "Triggered when a subscription is updated",
        },
        {
            "name": WebhookEventEnum.SUBSCRIPTION_DELETED.value,
            "description": "Triggered when a subscription is deleted",
        },
        {
            "name": WebhookEventEnum.PAYMENT_DUE.value,
            "description": "Triggered when a payment is due soon",
        },
        {
            "name": WebhookEventEnum.PAYMENT_OVERDUE.value,
            "description": "Triggered when a payment is overdue",
        },
        {
            "name": WebhookEventEnum.PAYMENT_COMPLETED.value,
            "description": "Triggered when a payment is marked as completed",
        },
        {
            "name": WebhookEventEnum.PAYMENT_SKIPPED.value,
            "description": "Triggered when a payment is skipped",
        },
        {
            "name": WebhookEventEnum.BUDGET_ALERT.value,
            "description": "Triggered when a category budget threshold is exceeded",
        },
        {
            "name": WebhookEventEnum.IMPORT_COMPLETED.value,
            "description": "Triggered when a bank statement import is completed",
        },
        {
            "name": WebhookEventEnum.CALENDAR_SYNCED.value,
            "description": "Triggered when calendar sync is completed",
        },
    ]
    return events


@router.get("/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats(
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookStatsResponse:
    """Get webhook statistics for the current user.

    Returns aggregate statistics about webhooks and deliveries.

    Returns:
        Webhook statistics including counts and average response time.
    """
    stats = await service.get_stats()
    return WebhookStatsResponse(**stats)


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    status: WebhookStatusEnum | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum webhooks to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookListResponse:
    """List webhook subscriptions for the current user.

    Args:
        status: Optional status filter.
        limit: Maximum webhooks to return (default: 50, max: 100).
        offset: Pagination offset.

    Returns:
        List of webhooks with total count.
    """
    # Convert enum if provided
    webhook_status = None
    if status:
        webhook_status = WebhookStatus(status.value)

    webhooks, total = await service.list(status=webhook_status, limit=limit, offset=offset)

    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(w) for w in webhooks],
        total=total,
    )


@router.post("", response_model=WebhookSecretResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookSecretResponse:
    """Create a new webhook subscription.

    The response includes the webhook secret, which is only returned once.
    Store it securely for verifying webhook signatures.

    Args:
        data: Webhook creation data.

    Returns:
        Created webhook with secret (secret only shown once).
    """
    webhook = await service.create(data)

    logger.info(f"Webhook created: {webhook.id}")

    return WebhookSecretResponse(
        id=webhook.id,
        secret=webhook.secret,
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """Get a webhook subscription by ID.

    Args:
        webhook_id: Webhook UUID.

    Returns:
        Webhook details.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    webhook = await service.get(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return WebhookResponse.model_validate(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdate,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    """Update a webhook subscription.

    Args:
        webhook_id: Webhook UUID.
        data: Update data.

    Returns:
        Updated webhook.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    webhook = await service.update(webhook_id, data)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    service: WebhookService = Depends(get_webhook_service),
) -> None:
    """Delete a webhook subscription.

    This performs a soft delete. The webhook will no longer receive events.

    Args:
        webhook_id: Webhook UUID.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    deleted = await service.delete(webhook_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: str,
    data: WebhookTestRequest | None = None,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookTestResponse:
    """Send a test event to a webhook.

    Sends a test payload to verify the webhook is configured correctly.

    Args:
        webhook_id: Webhook UUID.
        data: Optional test configuration.

    Returns:
        Test result with status code and response time.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    event_type = data.event_type.value if data else "subscription.created"

    delivery = await service.test_webhook(webhook_id, event_type)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return WebhookTestResponse(
        success=delivery.status == DeliveryStatus.SUCCESS,
        status_code=delivery.status_code,
        response_time_ms=delivery.duration_ms,
        error=delivery.error_message,
    )


@router.post("/{webhook_id}/regenerate-secret", response_model=WebhookSecretResponse)
async def regenerate_webhook_secret(
    webhook_id: str,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookSecretResponse:
    """Regenerate a webhook's secret.

    The old secret will be invalidated. Update your integration
    with the new secret to continue receiving webhooks.

    Args:
        webhook_id: Webhook UUID.

    Returns:
        Webhook ID with new secret.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    new_secret = await service.regenerate_secret(webhook_id)
    if not new_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return WebhookSecretResponse(
        id=webhook_id,
        secret=new_secret,
    )


@router.get("/{webhook_id}/deliveries", response_model=DeliveryListResponse)
async def list_deliveries(
    webhook_id: str,
    status: DeliveryStatusEnum | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum deliveries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: WebhookService = Depends(get_webhook_service),
) -> DeliveryListResponse:
    """List delivery logs for a webhook.

    Args:
        webhook_id: Webhook UUID.
        status: Optional status filter.
        limit: Maximum deliveries to return (default: 50, max: 100).
        offset: Pagination offset.

    Returns:
        List of deliveries with total count.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    # Convert enum if provided
    delivery_status = None
    if status:
        delivery_status = DeliveryStatus(status.value)

    deliveries, total = await service.get_deliveries(
        webhook_id,
        status=delivery_status,
        limit=limit,
        offset=offset,
    )

    # Check if webhook exists (deliveries will be empty list if not found)
    webhook = await service.get(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return DeliveryListResponse(
        deliveries=[DeliveryResponse.model_validate(d) for d in deliveries],
        total=total,
    )
