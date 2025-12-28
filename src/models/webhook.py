"""Webhook subscription ORM model.

This module defines the SQLAlchemy ORM model for webhook subscriptions,
allowing users to receive notifications about subscription events via HTTP callbacks.

Sprint 5.6 - Webhooks System
"""

import enum
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class WebhookEvent(str, enum.Enum):
    """Types of events that can trigger webhooks.

    Attributes:
        SUBSCRIPTION_CREATED: New subscription added.
        SUBSCRIPTION_UPDATED: Subscription details changed.
        SUBSCRIPTION_DELETED: Subscription removed.
        PAYMENT_DUE: Payment is due soon (based on reminder settings).
        PAYMENT_OVERDUE: Payment is past due date.
        PAYMENT_COMPLETED: Payment marked as completed.
        PAYMENT_SKIPPED: Payment marked as skipped.
        BUDGET_ALERT: Category budget threshold exceeded.
        IMPORT_COMPLETED: Bank statement import finished.
        CALENDAR_SYNCED: Calendar sync completed.
    """

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


class WebhookStatus(str, enum.Enum):
    """Status of a webhook subscription.

    Attributes:
        ACTIVE: Webhook is active and will receive events.
        PAUSED: Webhook is temporarily paused by user.
        DISABLED: Webhook automatically disabled after too many failures.
        DELETED: Webhook marked for deletion (soft delete).
    """

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    DELETED = "deleted"


class DeliveryStatus(str, enum.Enum):
    """Status of a webhook delivery attempt.

    Attributes:
        PENDING: Delivery queued but not yet attempted.
        SUCCESS: Delivery succeeded (2xx response).
        FAILED: Delivery failed (non-2xx response or network error).
        RETRYING: Delivery failed, retry scheduled.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(Base):
    """Webhook subscription model.

    Stores user webhook configurations for receiving event notifications
    via HTTP POST callbacks.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this webhook.
        name: Human-readable name for the webhook.
        url: Target URL for webhook delivery.
        secret: HMAC secret for signature verification.
        events: List of event types this webhook subscribes to.
        status: Current webhook status.
        headers: Custom headers to send with webhook requests (JSON string).
        is_active: Whether the webhook is currently active.
        consecutive_failures: Number of consecutive delivery failures.
        max_failures: Max failures before auto-disable (default: 5).
        last_triggered_at: When the webhook was last triggered.
        last_success_at: When the webhook last succeeded.
        last_failure_at: When the webhook last failed.
        last_failure_reason: Reason for the last failure.
        created_at: When the webhook was created.
        updated_at: When the webhook was last updated.

    Example:
        >>> webhook = WebhookSubscription(
        ...     user_id="user-uuid",
        ...     name="Payment Alerts",
        ...     url="https://example.com/webhooks",
        ...     events=["payment.due", "payment.overdue"],
        ... )
    """

    __tablename__ = "webhook_subscriptions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Webhook configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(64), nullable=False, default=lambda: secrets.token_hex(32)
    )
    events: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False)
    headers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string

    # Status
    status: Mapped[WebhookStatus] = mapped_column(
        Enum(WebhookStatus), default=WebhookStatus.ACTIVE, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Failure tracking
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    max_failures: Mapped[int] = mapped_column(Integer, default=5)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="webhooks")  # noqa: F821

    # Relationship to delivery logs
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WebhookSubscription(name='{self.name}', url='{self.url[:50]}...', status={self.status.value})>"

    def regenerate_secret(self) -> str:
        """Generate a new webhook secret.

        Returns:
            The new secret (64 hex characters).
        """
        self.secret = secrets.token_hex(32)
        return self.secret

    def record_success(self) -> None:
        """Record a successful delivery."""
        self.consecutive_failures = 0
        self.last_triggered_at = datetime.utcnow()
        self.last_success_at = datetime.utcnow()
        self.last_failure_reason = None

    def record_failure(self, reason: str) -> None:
        """Record a failed delivery.

        Args:
            reason: Description of the failure.
        """
        self.consecutive_failures += 1
        self.last_triggered_at = datetime.utcnow()
        self.last_failure_at = datetime.utcnow()
        self.last_failure_reason = reason[:500] if reason else None

        # Auto-disable after too many failures
        if self.consecutive_failures >= self.max_failures:
            self.status = WebhookStatus.DISABLED
            self.is_active = False

    def pause(self) -> None:
        """Pause the webhook."""
        self.status = WebhookStatus.PAUSED
        self.is_active = False

    def resume(self) -> None:
        """Resume a paused webhook."""
        self.status = WebhookStatus.ACTIVE
        self.is_active = True
        self.consecutive_failures = 0

    def subscribes_to(self, event: str | WebhookEvent) -> bool:
        """Check if webhook subscribes to an event.

        Args:
            event: Event type to check.

        Returns:
            True if the webhook subscribes to this event.
        """
        event_str = event.value if isinstance(event, WebhookEvent) else event
        return event_str in self.events

    def get_headers_dict(self) -> dict[str, str]:
        """Get custom headers as a dictionary.

        Returns:
            Dictionary of custom headers, or empty dict if none.
        """
        import json

        if not self.headers:
            return {}
        try:
            return json.loads(self.headers)
        except json.JSONDecodeError:
            return {}

    def set_headers(self, headers: dict[str, str]) -> None:
        """Set custom headers from a dictionary.

        Args:
            headers: Dictionary of header name-value pairs.
        """
        import json

        self.headers = json.dumps(headers) if headers else None


class WebhookDelivery(Base):
    """Webhook delivery log model.

    Records each attempt to deliver a webhook event.

    Attributes:
        id: UUID primary key.
        webhook_id: Foreign key to the webhook subscription.
        event_type: Type of event being delivered.
        payload: JSON payload sent to the webhook.
        status: Delivery status.
        status_code: HTTP response status code (if any).
        response_body: Response body (truncated if too long).
        error_message: Error message if delivery failed.
        attempt_number: Which attempt this is (1, 2, 3, etc.).
        next_retry_at: When to retry (if status is RETRYING).
        duration_ms: Request duration in milliseconds.
        created_at: When the delivery attempt was made.

    Example:
        >>> delivery = WebhookDelivery(
        ...     webhook_id="webhook-uuid",
        ...     event_type="payment.due",
        ...     payload='{"subscription_id": "..."}',
        ...     status=DeliveryStatus.PENDING,
        ... )
    """

    __tablename__ = "webhook_deliveries"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Webhook relationship
    webhook_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event information
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Unique event ID
    payload: Mapped[str] = mapped_column(Text, nullable=False)

    # Delivery status
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False, index=True
    )
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Retry information
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Performance
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationship to WebhookSubscription
    webhook: Mapped["WebhookSubscription"] = relationship(
        "WebhookSubscription", back_populates="deliveries"
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WebhookDelivery(event={self.event_type}, status={self.status.value}, attempt={self.attempt_number})>"

    def mark_success(
        self, status_code: int, response_body: str | None = None, duration_ms: int | None = None
    ) -> None:
        """Mark delivery as successful.

        Args:
            status_code: HTTP response status code.
            response_body: Response body (truncated to 1000 chars).
            duration_ms: Request duration in milliseconds.
        """
        self.status = DeliveryStatus.SUCCESS
        self.status_code = status_code
        self.response_body = response_body[:1000] if response_body else None
        self.duration_ms = duration_ms
        self.error_message = None
        self.next_retry_at = None

    def mark_failed(
        self,
        error_message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Mark delivery as failed.

        Args:
            error_message: Error description.
            status_code: HTTP response status code (if any).
            response_body: Response body (truncated to 1000 chars).
            duration_ms: Request duration in milliseconds.
        """
        self.status = DeliveryStatus.FAILED
        self.error_message = error_message[:500] if error_message else None
        self.status_code = status_code
        self.response_body = response_body[:1000] if response_body else None
        self.duration_ms = duration_ms
        self.next_retry_at = None

    def schedule_retry(self, retry_at: datetime) -> None:
        """Schedule a retry.

        Args:
            retry_at: When to retry the delivery.
        """
        self.status = DeliveryStatus.RETRYING
        self.next_retry_at = retry_at
        self.attempt_number += 1

    @property
    def can_retry(self) -> bool:
        """Check if delivery can be retried.

        Returns:
            True if attempt_number < max_attempts.
        """
        return self.attempt_number < self.max_attempts

    def get_payload_dict(self) -> dict:
        """Get payload as a dictionary.

        Returns:
            Parsed JSON payload.
        """
        import json

        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return {}
