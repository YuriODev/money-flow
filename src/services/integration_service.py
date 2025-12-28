"""Integration service for IFTTT/Zapier.

This module provides business logic for managing external integrations,
including API keys and REST Hook subscriptions.

Sprint 5.6 - IFTTT/Zapier Integration
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.integration import (
    APIKey,
    IntegrationStatus,
    IntegrationType,
    RestHookSubscription,
)
from src.models.subscription import Subscription
from src.schemas.integration import (
    APIKeyCreate,
    EventPayload,
    PaymentEventData,
    RestHookSubscribe,
    SubscriptionEventData,
)

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing IFTTT/Zapier integrations.

    Provides methods for:
    - API key management (CRUD)
    - REST Hook subscription management
    - Event delivery to external services
    - Sample data generation for Zapier

    Attributes:
        db: Database session.
        user_id: Current user's ID.
    """

    def __init__(self, db: AsyncSession, user_id: str):
        """Initialize the integration service.

        Args:
            db: Async database session.
            user_id: Current user's ID.
        """
        self.db = db
        self.user_id = user_id

    # ========================================================================
    # API Key Management
    # ========================================================================

    async def create_api_key(self, data: APIKeyCreate) -> tuple[APIKey, str]:
        """Create a new API key.

        Args:
            data: API key creation data.

        Returns:
            Tuple of (APIKey object, plain API key string).
            The plain key is only returned once.
        """
        # Generate key
        full_key, key_hash, key_prefix = APIKey.generate_key()

        # Calculate expiration
        expires_at = None
        if data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)

        # Create API key
        api_key = APIKey(
            user_id=self.user_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            integration_type=IntegrationType(data.integration_type.value),
            scopes=data.scopes or "read:subscriptions,write:subscriptions",
            expires_at=expires_at,
        )

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        logger.info(f"Created API key {api_key.id} for user {self.user_id}")

        return api_key, full_key

    async def list_api_keys(self) -> tuple[list[APIKey], int]:
        """List all API keys for the current user.

        Returns:
            Tuple of (list of API keys, total count).
        """
        query = select(APIKey).where(
            APIKey.user_id == self.user_id,
            APIKey.is_active == True,  # noqa: E712
        ).order_by(APIKey.created_at.desc())

        result = await self.db.execute(query)
        keys = list(result.scalars().all())

        return keys, len(keys)

    async def get_api_key(self, key_id: str) -> APIKey | None:
        """Get an API key by ID.

        Args:
            key_id: API key UUID.

        Returns:
            APIKey if found and owned by user, None otherwise.
        """
        query = select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: API key UUID.

        Returns:
            True if revoked, False if not found.
        """
        api_key = await self.get_api_key(key_id)
        if not api_key:
            return False

        api_key.is_active = False
        await self.db.commit()

        logger.info(f"Revoked API key {key_id}")
        return True

    async def validate_api_key(self, key: str) -> tuple[APIKey | None, str | None]:
        """Validate an API key.

        Args:
            key: Plain API key string.

        Returns:
            Tuple of (APIKey if valid, error message if invalid).
        """
        # Hash the provided key
        key_hash = APIKey.hash_key(key)

        # Look up by hash
        query = select(APIKey).where(APIKey.key_hash == key_hash)
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None, "Invalid API key"

        if not api_key.is_active:
            return None, "API key has been revoked"

        if api_key.is_expired():
            return None, "API key has expired"

        # Update last used
        api_key.record_usage()
        await self.db.commit()

        return api_key, None

    # ========================================================================
    # REST Hook Subscription Management
    # ========================================================================

    async def subscribe(
        self,
        data: RestHookSubscribe,
        integration_type: IntegrationType,
        api_key_id: str | None = None,
    ) -> RestHookSubscription:
        """Create a REST Hook subscription.

        Args:
            data: Subscription data with target_url and event_type.
            integration_type: Type of integration (Zapier, IFTTT, etc.).
            api_key_id: Optional API key ID used to create this.

        Returns:
            Created RestHookSubscription.
        """
        subscription = RestHookSubscription(
            user_id=self.user_id,
            api_key_id=api_key_id,
            integration_type=integration_type,
            target_url=str(data.target_url),
            event_type=data.event_type,
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(
            f"Created REST Hook subscription {subscription.id} "
            f"for event {data.event_type} -> {data.target_url}"
        )

        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a REST Hook subscription.

        Args:
            subscription_id: Subscription UUID.

        Returns:
            True if unsubscribed, False if not found.
        """
        query = select(RestHookSubscription).where(
            RestHookSubscription.id == subscription_id,
            RestHookSubscription.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return False

        # Soft delete - mark as revoked
        subscription.revoke()
        await self.db.commit()

        logger.info(f"Unsubscribed REST Hook {subscription_id}")
        return True

    async def list_subscriptions(
        self,
        event_type: str | None = None,
        status: IntegrationStatus | None = None,
    ) -> tuple[list[RestHookSubscription], int]:
        """List REST Hook subscriptions.

        Args:
            event_type: Optional filter by event type.
            status: Optional filter by status.

        Returns:
            Tuple of (list of subscriptions, total count).
        """
        query = select(RestHookSubscription).where(
            RestHookSubscription.user_id == self.user_id,
        )

        if event_type:
            query = query.where(RestHookSubscription.event_type == event_type)
        if status:
            query = query.where(RestHookSubscription.status == status)

        query = query.order_by(RestHookSubscription.created_at.desc())

        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())

        return subscriptions, len(subscriptions)

    async def get_subscription(self, subscription_id: str) -> RestHookSubscription | None:
        """Get a subscription by ID.

        Args:
            subscription_id: Subscription UUID.

        Returns:
            RestHookSubscription if found, None otherwise.
        """
        query = select(RestHookSubscription).where(
            RestHookSubscription.id == subscription_id,
            RestHookSubscription.user_id == self.user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # Event Delivery
    # ========================================================================

    async def trigger_event(
        self,
        event_type: str,
        data: dict[str, Any],
        user_id: str | None = None,
    ) -> int:
        """Trigger an event to all subscribed REST Hooks.

        Args:
            event_type: Type of event to trigger.
            data: Event data payload.
            user_id: Optional specific user (defaults to service user_id).

        Returns:
            Number of successful deliveries.
        """
        target_user_id = user_id or self.user_id

        # Find all active subscriptions for this event
        query = select(RestHookSubscription).where(
            RestHookSubscription.user_id == target_user_id,
            RestHookSubscription.event_type == event_type,
            RestHookSubscription.status == IntegrationStatus.ACTIVE,
        )
        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())

        if not subscriptions:
            return 0

        # Create event payload
        event_id = str(uuid.uuid4())
        payload = EventPayload(
            id=event_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
        )

        # Deliver to each subscription
        successful = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for subscription in subscriptions:
                try:
                    response = await client.post(
                        subscription.target_url,
                        json=payload.model_dump(mode="json"),
                        headers={
                            "Content-Type": "application/json",
                            "X-MoneyFlow-Event": event_type,
                            "X-MoneyFlow-Event-ID": event_id,
                        },
                    )

                    if 200 <= response.status_code < 300:
                        subscription.record_success()
                        successful += 1
                        logger.info(
                            f"Delivered event {event_type} to {subscription.target_url}"
                        )
                    elif response.status_code == 410:
                        # 410 Gone - Zapier wants us to unsubscribe
                        subscription.revoke()
                        logger.info(
                            f"Subscription {subscription.id} returned 410, revoking"
                        )
                    else:
                        subscription.record_failure(f"HTTP {response.status_code}")
                        logger.warning(
                            f"Failed to deliver to {subscription.target_url}: "
                            f"HTTP {response.status_code}"
                        )

                except httpx.RequestError as e:
                    subscription.record_failure(str(e))
                    logger.error(
                        f"Request error delivering to {subscription.target_url}: {e}"
                    )

        await self.db.commit()
        return successful

    # ========================================================================
    # Sample Data (for Zapier field mapping)
    # ========================================================================

    async def get_sample_data(
        self,
        event_type: str,
        limit: int = 3,
    ) -> list[EventPayload]:
        """Get sample event data for Zapier.

        Zapier calls this to show users what fields are available
        for mapping in their Zaps.

        Args:
            event_type: Event type to get samples for.
            limit: Maximum number of samples.

        Returns:
            List of sample event payloads.
        """
        samples = []

        if event_type.startswith("subscription."):
            # Get recent subscriptions
            query = select(Subscription).where(
                Subscription.user_id == self.user_id,
            ).order_by(Subscription.updated_at.desc()).limit(limit)

            result = await self.db.execute(query)
            subscriptions = list(result.scalars().all())

            for sub in subscriptions:
                data = SubscriptionEventData(
                    subscription_id=sub.id,
                    name=sub.name,
                    amount=float(sub.amount),
                    currency=sub.currency,
                    frequency=sub.frequency.value,
                    next_payment_date=sub.next_payment_date,
                    category=None,  # Would need to join
                )
                samples.append(EventPayload(
                    id=str(uuid.uuid4()),
                    event_type=event_type,
                    timestamp=datetime.utcnow(),
                    data=data.model_dump(mode="json"),
                ))

        elif event_type.startswith("payment."):
            # Generate sample payment data
            query = select(Subscription).where(
                Subscription.user_id == self.user_id,
            ).order_by(Subscription.next_payment_date.asc()).limit(limit)

            result = await self.db.execute(query)
            subscriptions = list(result.scalars().all())

            for sub in subscriptions:
                data = PaymentEventData(
                    subscription_id=sub.id,
                    subscription_name=sub.name,
                    amount=float(sub.amount),
                    currency=sub.currency,
                    payment_date=sub.next_payment_date or datetime.utcnow(),
                    status="due",
                    days_until_due=0,
                )
                samples.append(EventPayload(
                    id=str(uuid.uuid4()),
                    event_type=event_type,
                    timestamp=datetime.utcnow(),
                    data=data.model_dump(mode="json"),
                ))

        # If no real data, provide static samples
        if not samples:
            samples = self._get_static_samples(event_type, limit)

        return samples

    def _get_static_samples(self, event_type: str, limit: int) -> list[EventPayload]:
        """Get static sample data when no real data exists.

        Args:
            event_type: Event type.
            limit: Number of samples.

        Returns:
            List of static sample payloads.
        """
        static_samples = {
            "subscription.created": {
                "subscription_id": "sample-sub-123",
                "name": "Netflix",
                "amount": 15.99,
                "currency": "GBP",
                "frequency": "monthly",
                "next_payment_date": datetime.utcnow().isoformat(),
                "category": "Entertainment",
            },
            "subscription.updated": {
                "subscription_id": "sample-sub-123",
                "name": "Netflix Premium",
                "amount": 17.99,
                "currency": "GBP",
                "frequency": "monthly",
                "next_payment_date": datetime.utcnow().isoformat(),
                "category": "Entertainment",
            },
            "subscription.deleted": {
                "subscription_id": "sample-sub-123",
                "name": "Cancelled Service",
                "amount": 9.99,
                "currency": "GBP",
                "frequency": "monthly",
                "next_payment_date": None,
                "category": None,
            },
            "payment.due": {
                "subscription_id": "sample-sub-123",
                "subscription_name": "Netflix",
                "amount": 15.99,
                "currency": "GBP",
                "payment_date": datetime.utcnow().isoformat(),
                "status": "due",
                "days_until_due": 3,
            },
            "payment.overdue": {
                "subscription_id": "sample-sub-123",
                "subscription_name": "Gym Membership",
                "amount": 29.99,
                "currency": "GBP",
                "payment_date": datetime.utcnow().isoformat(),
                "status": "overdue",
                "days_until_due": -2,
            },
            "payment.completed": {
                "subscription_id": "sample-sub-123",
                "subscription_name": "Spotify",
                "amount": 10.99,
                "currency": "GBP",
                "payment_date": datetime.utcnow().isoformat(),
                "status": "completed",
                "days_until_due": 0,
            },
            "payment.skipped": {
                "subscription_id": "sample-sub-123",
                "subscription_name": "Paused Subscription",
                "amount": 5.99,
                "currency": "GBP",
                "payment_date": datetime.utcnow().isoformat(),
                "status": "skipped",
                "days_until_due": 0,
            },
            "budget.alert": {
                "category": "Entertainment",
                "budget_limit": 100.00,
                "current_spend": 115.50,
                "percent_used": 115.5,
                "currency": "GBP",
            },
            "import.completed": {
                "import_id": "sample-import-123",
                "file_name": "statement.csv",
                "bank_name": "Monzo",
                "subscriptions_detected": 5,
                "subscriptions_imported": 3,
            },
            "calendar.synced": {
                "sync_type": "google",
                "events_synced": 12,
                "calendar_name": "Money Flow Payments",
            },
        }

        sample_data = static_samples.get(event_type, {"message": "Sample event"})

        return [
            EventPayload(
                id=f"sample-{i}",
                event_type=event_type,
                timestamp=datetime.utcnow(),
                data=sample_data,
            )
            for i in range(min(limit, 3))
        ]

    # ========================================================================
    # Statistics
    # ========================================================================

    async def get_stats(self) -> dict[str, Any]:
        """Get integration statistics for the current user.

        Returns:
            Dictionary with integration stats.
        """
        # API key stats
        key_query = select(
            func.count(APIKey.id).label("total"),
            func.sum(func.cast(APIKey.is_active, Integer)).label("active"),
        ).where(APIKey.user_id == self.user_id)

        key_result = await self.db.execute(key_query)
        key_row = key_result.one()

        # Subscription stats
        sub_query = select(
            func.count(RestHookSubscription.id).label("total"),
            func.sum(
                func.cast(
                    RestHookSubscription.status == IntegrationStatus.ACTIVE,
                    Integer,
                )
            ).label("active"),
            func.sum(RestHookSubscription.delivery_count).label("deliveries"),
            func.sum(RestHookSubscription.failure_count).label("failures"),
        ).where(RestHookSubscription.user_id == self.user_id)

        sub_result = await self.db.execute(sub_query)
        sub_row = sub_result.one()

        total_deliveries = (sub_row.deliveries or 0) + (sub_row.failures or 0)
        success_rate = (
            (sub_row.deliveries or 0) / total_deliveries * 100
            if total_deliveries > 0
            else 0.0
        )

        return {
            "total_api_keys": key_row.total or 0,
            "active_api_keys": key_row.active or 0,
            "total_subscriptions": sub_row.total or 0,
            "active_subscriptions": sub_row.active or 0,
            "total_deliveries": total_deliveries,
            "successful_deliveries": sub_row.deliveries or 0,
            "failed_deliveries": sub_row.failures or 0,
            "delivery_success_rate": round(success_rate, 2),
        }
