"""Webhook delivery service.

This module provides functionality for managing webhook subscriptions
and delivering webhook events to registered endpoints.

Sprint 5.6 - Webhooks System

Features:
- CRUD operations for webhook subscriptions
- Event delivery with HMAC signing
- Retry logic with exponential backoff
- Delivery logging and statistics
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.webhook import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEvent,
    WebhookStatus,
    WebhookSubscription,
)
from src.schemas.webhook import (
    WebhookCreate,
    WebhookEventPayload,
    WebhookUpdate,
)

logger = logging.getLogger(__name__)

# Retry configuration
RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min
DELIVERY_TIMEOUT = 30  # seconds
MAX_PAYLOAD_SIZE = 65536  # 64KB


class WebhookService:
    """Service for webhook subscription and delivery management.

    Handles CRUD operations for webhooks, event delivery with HMAC signing,
    retry logic, and delivery statistics.

    Attributes:
        db: AsyncSession for database access.
        user_id: UUID of the current user.

    Example:
        >>> service = WebhookService(db, user_id)
        >>> webhook = await service.create(WebhookCreate(...))
        >>> await service.trigger_event(WebhookEvent.PAYMENT_DUE, {...})
    """

    def __init__(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """Initialize the webhook service.

        Args:
            db: AsyncSession for database access.
            user_id: UUID of the current user.
        """
        self.db = db
        self.user_id = user_id

    async def create(self, data: WebhookCreate) -> WebhookSubscription:
        """Create a new webhook subscription.

        Args:
            data: Webhook creation data.

        Returns:
            Created WebhookSubscription.
        """
        # Convert events to string list
        events = [e.value if isinstance(e, WebhookEvent) else str(e) for e in data.events]

        webhook = WebhookSubscription(
            user_id=str(self.user_id),
            name=data.name,
            url=str(data.url),
            events=events,
        )

        if data.headers:
            webhook.set_headers(data.headers)

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info(f"Created webhook {webhook.id} for user {self.user_id}")
        return webhook

    async def get(self, webhook_id: str) -> WebhookSubscription | None:
        """Get a webhook by ID.

        Args:
            webhook_id: Webhook UUID.

        Returns:
            WebhookSubscription or None if not found.
        """
        result = await self.db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.id == webhook_id,
                WebhookSubscription.user_id == str(self.user_id),
                WebhookSubscription.status != WebhookStatus.DELETED,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        status: WebhookStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WebhookSubscription], int]:
        """List webhooks for the current user.

        Args:
            status: Optional status filter.
            limit: Maximum webhooks to return.
            offset: Pagination offset.

        Returns:
            Tuple of (webhooks, total_count).
        """
        query = select(WebhookSubscription).where(
            WebhookSubscription.user_id == str(self.user_id),
            WebhookSubscription.status != WebhookStatus.DELETED,
        )

        if status:
            query = query.where(WebhookSubscription.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.order_by(WebhookSubscription.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        webhooks = list(result.scalars().all())

        return webhooks, total

    async def update(
        self,
        webhook_id: str,
        data: WebhookUpdate,
    ) -> WebhookSubscription | None:
        """Update a webhook subscription.

        Args:
            webhook_id: Webhook UUID.
            data: Update data.

        Returns:
            Updated WebhookSubscription or None if not found.
        """
        webhook = await self.get(webhook_id)
        if not webhook:
            return None

        if data.name is not None:
            webhook.name = data.name

        if data.url is not None:
            webhook.url = str(data.url)

        if data.events is not None:
            webhook.events = [e.value if hasattr(e, "value") else str(e) for e in data.events]

        if data.headers is not None:
            webhook.set_headers(data.headers)

        if data.is_active is not None:
            if data.is_active:
                webhook.resume()
            else:
                webhook.pause()

        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    async def delete(self, webhook_id: str) -> bool:
        """Delete a webhook (soft delete).

        Args:
            webhook_id: Webhook UUID.

        Returns:
            True if deleted, False if not found.
        """
        webhook = await self.get(webhook_id)
        if not webhook:
            return False

        webhook.status = WebhookStatus.DELETED
        webhook.is_active = False
        await self.db.commit()

        logger.info(f"Deleted webhook {webhook_id}")
        return True

    async def regenerate_secret(self, webhook_id: str) -> str | None:
        """Regenerate a webhook's secret.

        Args:
            webhook_id: Webhook UUID.

        Returns:
            New secret or None if webhook not found.
        """
        webhook = await self.get(webhook_id)
        if not webhook:
            return None

        new_secret = webhook.regenerate_secret()
        await self.db.commit()

        logger.info(f"Regenerated secret for webhook {webhook_id}")
        return new_secret

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for payload.

        Args:
            payload: JSON payload string.
            secret: Webhook secret.

        Returns:
            Hex-encoded signature.
        """
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        )
        return signature.hexdigest()

    async def deliver(
        self,
        webhook: WebhookSubscription,
        event_type: str,
        data: dict[str, Any],
    ) -> WebhookDelivery:
        """Deliver an event to a webhook.

        Args:
            webhook: Target webhook subscription.
            event_type: Type of event.
            data: Event data payload.

        Returns:
            WebhookDelivery record.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Build payload
        payload = WebhookEventPayload(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            data=data,
        )
        payload_json = payload.model_dump_json()

        # Check payload size
        if len(payload_json) > MAX_PAYLOAD_SIZE:
            logger.warning(f"Payload too large for webhook {webhook.id}: {len(payload_json)} bytes")
            payload_json = json.dumps(
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "timestamp": timestamp.isoformat(),
                    "data": {"error": "Payload too large, truncated"},
                }
            )

        # Generate signature
        signature = self._sign_payload(payload_json, webhook.secret)

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_id,
            payload=payload_json,
            status=DeliveryStatus.PENDING,
        )
        self.db.add(delivery)
        await self.db.commit()

        # Attempt delivery
        start_time = time.time()
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={signature}",
                "X-Webhook-Event": event_type,
                "X-Webhook-Id": webhook.id,
                "X-Webhook-Delivery": delivery.id,
            }

            # Add custom headers
            custom_headers = webhook.get_headers_dict()
            if custom_headers:
                headers.update(custom_headers)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers,
                    timeout=DELIVERY_TIMEOUT,
                )

            duration_ms = int((time.time() - start_time) * 1000)

            if 200 <= response.status_code < 300:
                # Success
                delivery.mark_success(
                    status_code=response.status_code,
                    response_body=response.text[:1000] if response.text else None,
                    duration_ms=duration_ms,
                )
                webhook.record_success()
                logger.info(
                    f"Delivered webhook {webhook.id}: {event_type} ({response.status_code})"
                )
            else:
                # HTTP error
                error_msg = f"HTTP {response.status_code}"
                delivery.mark_failed(
                    error_message=error_msg,
                    status_code=response.status_code,
                    response_body=response.text[:1000] if response.text else None,
                    duration_ms=duration_ms,
                )
                webhook.record_failure(error_msg)
                logger.warning(f"Webhook delivery failed {webhook.id}: {error_msg}")

        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = "Request timeout"
            delivery.mark_failed(error_message=error_msg, duration_ms=duration_ms)
            webhook.record_failure(error_msg)
            logger.warning(f"Webhook delivery timeout {webhook.id}")

        except httpx.RequestError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Connection error: {str(e)[:200]}"
            delivery.mark_failed(error_message=error_msg, duration_ms=duration_ms)
            webhook.record_failure(error_msg)
            logger.warning(f"Webhook delivery error {webhook.id}: {error_msg}")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)[:200]}"
            delivery.mark_failed(error_message=error_msg, duration_ms=duration_ms)
            webhook.record_failure(error_msg)
            logger.error(f"Webhook delivery exception {webhook.id}: {e}")

        # Schedule retry if failed and can retry
        if delivery.status == DeliveryStatus.FAILED and delivery.can_retry:
            retry_delay = RETRY_DELAYS[min(delivery.attempt_number - 1, len(RETRY_DELAYS) - 1)]
            delivery.schedule_retry(datetime.utcnow() + timedelta(seconds=retry_delay))
            logger.info(f"Scheduled retry for webhook {webhook.id} in {retry_delay}s")

        await self.db.commit()
        await self.db.refresh(delivery)

        return delivery

    async def trigger_event(
        self,
        event_type: WebhookEvent | str,
        data: dict[str, Any],
    ) -> list[WebhookDelivery]:
        """Trigger an event for all subscribed webhooks.

        Args:
            event_type: Type of event.
            data: Event data payload.

        Returns:
            List of WebhookDelivery records.
        """
        event_str = event_type.value if isinstance(event_type, WebhookEvent) else event_type

        # Find all active webhooks subscribed to this event
        result = await self.db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.user_id == str(self.user_id),
                WebhookSubscription.status == WebhookStatus.ACTIVE,
                WebhookSubscription.is_active == True,  # noqa: E712
                WebhookSubscription.events.contains([event_str]),
            )
        )
        webhooks = result.scalars().all()

        if not webhooks:
            logger.debug(f"No webhooks subscribed to {event_str}")
            return []

        # Deliver to all webhooks
        deliveries = []
        for webhook in webhooks:
            delivery = await self.deliver(webhook, event_str, data)
            deliveries.append(delivery)

        logger.info(f"Triggered {event_str} for {len(deliveries)} webhooks")
        return deliveries

    async def test_webhook(
        self,
        webhook_id: str,
        event_type: str = "subscription.created",
    ) -> WebhookDelivery | None:
        """Send a test event to a webhook.

        Args:
            webhook_id: Webhook UUID.
            event_type: Event type to simulate.

        Returns:
            WebhookDelivery record or None if webhook not found.
        """
        webhook = await self.get(webhook_id)
        if not webhook:
            return None

        # Test payload
        test_data = {
            "test": True,
            "message": "This is a test webhook delivery from Money Flow",
            "webhook_id": webhook_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self.deliver(webhook, f"test.{event_type}", test_data)

    async def get_deliveries(
        self,
        webhook_id: str,
        status: DeliveryStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WebhookDelivery], int]:
        """Get delivery logs for a webhook.

        Args:
            webhook_id: Webhook UUID.
            status: Optional status filter.
            limit: Maximum deliveries to return.
            offset: Pagination offset.

        Returns:
            Tuple of (deliveries, total_count).
        """
        # Verify webhook ownership
        webhook = await self.get(webhook_id)
        if not webhook:
            return [], 0

        query = select(WebhookDelivery).where(
            WebhookDelivery.webhook_id == webhook_id,
        )

        if status:
            query = query.where(WebhookDelivery.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.order_by(WebhookDelivery.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        deliveries = list(result.scalars().all())

        return deliveries, total

    async def get_stats(self) -> dict[str, Any]:
        """Get webhook statistics for the current user.

        Returns:
            Dictionary with webhook statistics.
        """
        # Count webhooks by status
        result = await self.db.execute(
            select(
                WebhookSubscription.status,
                func.count(WebhookSubscription.id),
            )
            .where(
                WebhookSubscription.user_id == str(self.user_id),
                WebhookSubscription.status != WebhookStatus.DELETED,
            )
            .group_by(WebhookSubscription.status)
        )
        status_counts = dict(result.all())

        total_webhooks = sum(status_counts.values())
        active = status_counts.get(WebhookStatus.ACTIVE, 0)
        paused = status_counts.get(WebhookStatus.PAUSED, 0)
        disabled = status_counts.get(WebhookStatus.DISABLED, 0)

        # Get webhook IDs for this user
        webhook_ids_query = select(WebhookSubscription.id).where(
            WebhookSubscription.user_id == str(self.user_id),
        )

        # Count deliveries by status
        delivery_result = await self.db.execute(
            select(
                WebhookDelivery.status,
                func.count(WebhookDelivery.id),
            )
            .where(WebhookDelivery.webhook_id.in_(webhook_ids_query))
            .group_by(WebhookDelivery.status)
        )
        delivery_counts = dict(delivery_result.all())

        total_deliveries = sum(delivery_counts.values())
        successful = delivery_counts.get(DeliveryStatus.SUCCESS, 0)
        failed = delivery_counts.get(DeliveryStatus.FAILED, 0)

        # Average response time for successful deliveries
        avg_result = await self.db.execute(
            select(func.avg(WebhookDelivery.duration_ms)).where(
                WebhookDelivery.webhook_id.in_(webhook_ids_query),
                WebhookDelivery.status == DeliveryStatus.SUCCESS,
                WebhookDelivery.duration_ms.isnot(None),
            )
        )
        avg_response_time = avg_result.scalar()

        return {
            "total_webhooks": total_webhooks,
            "active_webhooks": active,
            "paused_webhooks": paused,
            "disabled_webhooks": disabled,
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "avg_response_time_ms": float(avg_response_time) if avg_response_time else None,
        }

    async def retry_failed_deliveries(self) -> int:
        """Retry failed deliveries that are due for retry.

        This should be called by a background task.

        Returns:
            Number of deliveries retried.
        """
        now = datetime.utcnow()

        # Find deliveries due for retry
        result = await self.db.execute(
            select(WebhookDelivery)
            .join(WebhookSubscription)
            .where(
                WebhookDelivery.status == DeliveryStatus.RETRYING,
                WebhookDelivery.next_retry_at <= now,
                WebhookSubscription.user_id == str(self.user_id),
                WebhookSubscription.status == WebhookStatus.ACTIVE,
            )
            .limit(100)
        )
        deliveries = result.scalars().all()

        if not deliveries:
            return 0

        retried = 0
        for delivery in deliveries:
            # Get webhook
            webhook_result = await self.db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.id == delivery.webhook_id,
                )
            )
            webhook = webhook_result.scalar_one_or_none()

            if not webhook or webhook.status != WebhookStatus.ACTIVE:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = "Webhook no longer active"
                continue

            # Retry delivery
            payload_dict = delivery.get_payload_dict()
            data = payload_dict.get("data", {})

            # Re-deliver
            await self.deliver(webhook, delivery.event_type, data)
            retried += 1

        await self.db.commit()
        logger.info(f"Retried {retried} webhook deliveries")
        return retried
