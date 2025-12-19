"""Notification history ORM model.

This module defines the SQLAlchemy ORM model for storing sent notification
history, allowing users to view past notifications and their delivery status.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class NotificationChannel(str, Enum):
    """Notification delivery channel."""

    TELEGRAM = "telegram"
    EMAIL = "email"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    PENDING = "pending"


class NotificationType(str, Enum):
    """Type of notification."""

    PAYMENT_REMINDER = "payment_reminder"
    OVERDUE_ALERT = "overdue_alert"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"
    TEST = "test"
    WELCOME = "welcome"
    VERIFICATION = "verification"


class NotificationHistory(Base):
    """Notification history model.

    Stores records of all notifications sent to users, including
    the channel, type, content, and delivery status.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: Foreign key to users table.
        subscription_id: Optional foreign key to subscriptions (for reminders).
        channel: Notification channel (telegram, email, push).
        notification_type: Type of notification.
        title: Notification title.
        body: Notification body text.
        status: Delivery status.
        error_message: Error message if delivery failed.
        sent_at: When the notification was sent.
        delivered_at: When the notification was delivered (if known).
        extra_data: Additional JSON data (tags, actions, etc.).

    Example:
        >>> history = NotificationHistory(
        ...     user_id="user-uuid",
        ...     channel=NotificationChannel.TELEGRAM,
        ...     notification_type=NotificationType.PAYMENT_REMINDER,
        ...     title="Payment Due",
        ...     body="Netflix £15.99 due tomorrow",
        ...     status=NotificationStatus.SENT,
        ... )
    """

    __tablename__ = "notification_history"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Optional subscription reference (for payment reminders)
    subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    # Notification details
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Delivery status
    status: Mapped[str] = mapped_column(String(20), default=NotificationStatus.PENDING.value)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Additional extra data (JSON string)
    extra_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_history")  # noqa: F821
    subscription: Mapped["Subscription"] = relationship("Subscription")  # noqa: F821

    def __repr__(self) -> str:
        """Return string representation of notification history."""
        return (
            f"<NotificationHistory(user_id='{self.user_id}', "
            f"channel='{self.channel}', type='{self.notification_type}')>"
        )

    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT.value
        self.sent_at = datetime.utcnow()

    def mark_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = NotificationStatus.DELIVERED.value
        self.delivered_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed.

        Args:
            error: Error message describing the failure.
        """
        self.status = NotificationStatus.FAILED.value
        self.error_message = error

    def get_extra_data_dict(self) -> dict | None:
        """Get extra data as a dictionary.

        Returns:
            The extra data parsed from JSON, or None if not set.
        """
        import json

        if not self.extra_data:
            return None
        try:
            return json.loads(self.extra_data)
        except json.JSONDecodeError:
            return None

    def set_extra_data(self, data: dict) -> None:
        """Set extra data from a dictionary.

        Args:
            data: The extra data to store.
        """
        import json

        self.extra_data = json.dumps(data)
