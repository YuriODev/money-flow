"""Webhook Pydantic schemas.

This module defines request/response schemas for the Webhook API endpoints.

Sprint 5.6 - Webhooks System
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class WebhookEventEnum(str, Enum):
    """Types of events that can trigger webhooks."""

    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_DELETED = "subscription.deleted"
    PAYMENT_DUE = "payment.due"
    PAYMENT_OVERDUE = "payment.overdue"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_SKIPPED = "payment.skipped"
    BUDGET_ALERT = "budget.alert"
    IMPORT_COMPLETED = "import.completed"
    CALENDAR_SYNCED = "calendar.synced"


class WebhookStatusEnum(str, Enum):
    """Status of a webhook subscription."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    DELETED = "deleted"


class DeliveryStatusEnum(str, Enum):
    """Status of a webhook delivery attempt."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


# Request schemas


class WebhookCreate(BaseModel):
    """Schema for creating a webhook subscription.

    Attributes:
        name: Human-readable name for the webhook.
        url: Target URL for webhook delivery (must be HTTPS in production).
        events: List of event types to subscribe to.
        headers: Optional custom headers to include in requests.

    Example:
        >>> WebhookCreate(
        ...     name="Payment Alerts",
        ...     url="https://example.com/webhooks",
        ...     events=["payment.due", "payment.overdue"],
        ... )
    """

    name: str = Field(..., min_length=1, max_length=100, description="Webhook name")
    url: HttpUrl = Field(..., description="Target URL for webhook delivery")
    events: list[WebhookEventEnum] = Field(
        ...,
        min_length=1,
        description="List of events to subscribe to",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Optional custom headers for requests",
    )

    @field_validator("events")
    @classmethod
    def unique_events(cls, v: list[WebhookEventEnum]) -> list[WebhookEventEnum]:
        """Ensure events are unique."""
        return list(set(v))


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook subscription.

    All fields are optional; only provided fields will be updated.

    Attributes:
        name: Updated name.
        url: Updated URL.
        events: Updated event list.
        headers: Updated custom headers.
        is_active: Pause/resume webhook.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    events: list[WebhookEventEnum] | None = None
    headers: dict[str, str] | None = None
    is_active: bool | None = None

    @field_validator("events")
    @classmethod
    def unique_events(cls, v: list[WebhookEventEnum] | None) -> list[WebhookEventEnum] | None:
        """Ensure events are unique."""
        if v is None:
            return None
        return list(set(v))


class WebhookTestRequest(BaseModel):
    """Schema for testing a webhook.

    Attributes:
        event_type: Optional event type to use for test payload.
    """

    event_type: WebhookEventEnum = Field(
        default=WebhookEventEnum.SUBSCRIPTION_CREATED,
        description="Event type to simulate",
    )


# Response schemas


class WebhookResponse(BaseModel):
    """Schema for webhook subscription response.

    Attributes:
        id: Webhook UUID.
        name: Human-readable name.
        url: Target URL.
        events: Subscribed event types.
        status: Current status.
        is_active: Whether webhook is active.
        headers: Custom headers (if any).
        consecutive_failures: Number of consecutive failures.
        last_triggered_at: When webhook was last triggered.
        last_success_at: When webhook last succeeded.
        last_failure_at: When webhook last failed.
        last_failure_reason: Reason for last failure.
        created_at: When webhook was created.
        updated_at: When webhook was last updated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: str
    events: list[str]
    status: WebhookStatusEnum
    is_active: bool
    headers: dict[str, str] | None = None
    consecutive_failures: int
    last_triggered_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("headers", mode="before")
    @classmethod
    def parse_headers(cls, v):
        """Parse headers from JSON string if needed."""
        import json

        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class WebhookListResponse(BaseModel):
    """Schema for listing webhooks.

    Attributes:
        webhooks: List of webhook subscriptions.
        total: Total count of webhooks.
    """

    webhooks: list[WebhookResponse]
    total: int


class WebhookSecretResponse(BaseModel):
    """Schema for webhook secret (returned only on create or regenerate).

    Attributes:
        id: Webhook UUID.
        secret: HMAC signing secret.
    """

    id: str
    secret: str


class DeliveryResponse(BaseModel):
    """Schema for webhook delivery log entry.

    Attributes:
        id: Delivery UUID.
        webhook_id: Parent webhook UUID.
        event_type: Type of event.
        event_id: Unique event ID.
        status: Delivery status.
        status_code: HTTP response status code.
        error_message: Error message if failed.
        attempt_number: Which attempt this is.
        duration_ms: Request duration in milliseconds.
        created_at: When delivery was attempted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    webhook_id: str
    event_type: str
    event_id: str
    status: DeliveryStatusEnum
    status_code: int | None
    error_message: str | None
    attempt_number: int
    duration_ms: int | None
    created_at: datetime


class DeliveryListResponse(BaseModel):
    """Schema for listing webhook deliveries.

    Attributes:
        deliveries: List of delivery logs.
        total: Total count of deliveries.
    """

    deliveries: list[DeliveryResponse]
    total: int


class WebhookTestResponse(BaseModel):
    """Schema for webhook test result.

    Attributes:
        success: Whether test delivery succeeded.
        status_code: HTTP response status code.
        response_time_ms: Response time in milliseconds.
        error: Error message if failed.
    """

    success: bool
    status_code: int | None
    response_time_ms: int | None
    error: str | None = None


class WebhookEventPayload(BaseModel):
    """Schema for webhook event payload.

    This is the payload sent to webhook URLs.

    Attributes:
        event_id: Unique event ID.
        event_type: Type of event.
        timestamp: When event occurred.
        data: Event-specific data.
    """

    event_id: str
    event_type: str
    timestamp: datetime
    data: dict


class WebhookStatsResponse(BaseModel):
    """Schema for webhook statistics.

    Attributes:
        total_webhooks: Total webhook subscriptions.
        active_webhooks: Currently active webhooks.
        paused_webhooks: Paused webhooks.
        disabled_webhooks: Auto-disabled webhooks.
        total_deliveries: Total delivery attempts.
        successful_deliveries: Successful deliveries.
        failed_deliveries: Failed deliveries.
        avg_response_time_ms: Average response time.
    """

    total_webhooks: int
    active_webhooks: int
    paused_webhooks: int
    disabled_webhooks: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    avg_response_time_ms: float | None
