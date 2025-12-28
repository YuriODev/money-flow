"""Pydantic schemas for IFTTT/Zapier integrations.

This module defines request/response schemas for the integration API
endpoints, including API keys and REST Hook subscriptions.

Sprint 5.6 - IFTTT/Zapier Integration
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class IntegrationTypeEnum(str, Enum):
    """Integration type enum for API."""

    ZAPIER = "zapier"
    IFTTT = "ifttt"
    CUSTOM = "custom"


class IntegrationStatusEnum(str, Enum):
    """Integration status enum for API."""

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============================================================================
# API Key Schemas
# ============================================================================


class APIKeyCreate(BaseModel):
    """Schema for creating an API key.

    Attributes:
        name: Human-readable name for the key.
        integration_type: Type of integration (zapier, ifttt, custom).
        scopes: Optional custom scopes (default: read/write subscriptions).
        expires_in_days: Optional expiration in days.
    """

    name: str = Field(..., min_length=1, max_length=100)
    integration_type: IntegrationTypeEnum = IntegrationTypeEnum.CUSTOM
    scopes: str | None = Field(None, max_length=500)
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Schema for API key response (without secret).

    Attributes:
        id: Key UUID.
        name: Human-readable name.
        key_prefix: First 8 characters for identification.
        integration_type: Type of integration.
        scopes: Allowed scopes.
        is_active: Whether key is active.
        last_used_at: When key was last used.
        expires_at: Optional expiration date.
        created_at: When key was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    integration_type: IntegrationTypeEnum
    scopes: str
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class APIKeyCreatedResponse(BaseModel):
    """Schema for newly created API key (includes secret).

    The api_key field is only returned once at creation time.
    Store it securely - it cannot be retrieved again.

    Attributes:
        id: Key UUID.
        name: Human-readable name.
        api_key: The full API key (only shown once).
        key_prefix: First 8 characters for identification.
        integration_type: Type of integration.
        scopes: Allowed scopes.
        expires_at: Optional expiration date.
        created_at: When key was created.
    """

    id: str
    name: str
    api_key: str  # Only returned at creation
    key_prefix: str
    integration_type: IntegrationTypeEnum
    scopes: str
    expires_at: datetime | None
    created_at: datetime


class APIKeyListResponse(BaseModel):
    """Schema for list of API keys.

    Attributes:
        keys: List of API keys.
        total: Total number of keys.
    """

    keys: list[APIKeyResponse]
    total: int


# ============================================================================
# REST Hook Subscription Schemas
# ============================================================================


class RestHookSubscribe(BaseModel):
    """Schema for creating a REST Hook subscription.

    Used by Zapier/IFTTT to register a webhook URL.

    Attributes:
        target_url: URL to send webhook payloads to.
        event_type: Event type to subscribe to.
    """

    target_url: HttpUrl
    event_type: str = Field(..., min_length=1, max_length=50)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type is supported."""
        valid_events = {
            "subscription.created",
            "subscription.updated",
            "subscription.deleted",
            "payment.due",
            "payment.overdue",
            "payment.completed",
            "payment.skipped",
            "budget.alert",
            "import.completed",
            "calendar.synced",
        }
        if v not in valid_events:
            raise ValueError(f"Invalid event type. Must be one of: {', '.join(sorted(valid_events))}")
        return v


class RestHookResponse(BaseModel):
    """Schema for REST Hook subscription response.

    Attributes:
        id: Subscription UUID.
        target_url: URL for webhook delivery.
        event_type: Event type subscribed to.
        integration_type: Type of integration.
        status: Current status.
        delivery_count: Number of successful deliveries.
        failure_count: Number of failed deliveries.
        last_delivery_at: When last delivery was made.
        created_at: When subscription was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    target_url: str
    event_type: str
    integration_type: IntegrationTypeEnum
    status: IntegrationStatusEnum
    delivery_count: int
    failure_count: int
    last_delivery_at: datetime | None
    created_at: datetime


class RestHookListResponse(BaseModel):
    """Schema for list of REST Hook subscriptions.

    Attributes:
        subscriptions: List of subscriptions.
        total: Total count.
    """

    subscriptions: list[RestHookResponse]
    total: int


# ============================================================================
# Event Payload Schemas
# ============================================================================


class EventPayload(BaseModel):
    """Standard event payload for Zapier/IFTTT.

    Attributes:
        id: Unique event ID.
        event_type: Type of event.
        timestamp: When the event occurred.
        data: Event-specific data.
    """

    id: str
    event_type: str
    timestamp: datetime
    data: dict


class SubscriptionEventData(BaseModel):
    """Data for subscription events.

    Attributes:
        subscription_id: Subscription UUID.
        name: Subscription name.
        amount: Payment amount.
        currency: Currency code.
        frequency: Payment frequency.
        next_payment_date: Next payment date.
        category: Optional category name.
    """

    subscription_id: str
    name: str
    amount: float
    currency: str
    frequency: str
    next_payment_date: datetime | None
    category: str | None = None


class PaymentEventData(BaseModel):
    """Data for payment events.

    Attributes:
        subscription_id: Subscription UUID.
        subscription_name: Subscription name.
        amount: Payment amount.
        currency: Currency code.
        payment_date: Date of payment.
        status: Payment status (due, overdue, completed, skipped).
        days_until_due: Days until/since due date.
    """

    subscription_id: str
    subscription_name: str
    amount: float
    currency: str
    payment_date: datetime
    status: str
    days_until_due: int | None = None


# ============================================================================
# Sample Data Schemas (for Zapier)
# ============================================================================


class SampleDataRequest(BaseModel):
    """Request for sample data (used by Zapier to show field mapping).

    Attributes:
        event_type: Event type to get samples for.
        limit: Max number of samples (default: 3).
    """

    event_type: str
    limit: int = Field(3, ge=1, le=10)


class SampleDataResponse(BaseModel):
    """Response with sample event data.

    Attributes:
        samples: List of sample event payloads.
    """

    samples: list[EventPayload]


# ============================================================================
# Integration Stats
# ============================================================================


class IntegrationStatsResponse(BaseModel):
    """Statistics for user's integrations.

    Attributes:
        total_api_keys: Number of API keys.
        active_api_keys: Number of active API keys.
        total_subscriptions: Number of REST Hook subscriptions.
        active_subscriptions: Number of active subscriptions.
        total_deliveries: Total webhook deliveries.
        successful_deliveries: Successful deliveries.
        failed_deliveries: Failed deliveries.
        delivery_success_rate: Success rate percentage.
    """

    total_api_keys: int
    active_api_keys: int
    total_subscriptions: int
    active_subscriptions: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    delivery_success_rate: float


# ============================================================================
# Available Events
# ============================================================================


class EventTypeInfo(BaseModel):
    """Information about an event type.

    Attributes:
        name: Event type identifier.
        description: Human-readable description.
        sample_payload: Example payload structure.
    """

    name: str
    description: str
    sample_payload: dict
