"""Notification preferences ORM model.

This module defines the SQLAlchemy ORM model for user notification preferences,
including Telegram integration settings, reminder configuration, and digest options.
"""

import secrets
import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class NotificationPreferences(Base):
    """User notification preferences model.

    Stores user-specific notification settings including Telegram integration,
    payment reminder configuration, and digest preferences.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: Foreign key to users table (one-to-one).

        Telegram Integration:
            telegram_enabled: Whether Telegram notifications are enabled.
            telegram_chat_id: Telegram chat ID for sending messages.
            telegram_username: User's Telegram username.
            telegram_verified: Whether Telegram account is verified.
            telegram_verification_code: Code for linking Telegram account.
            telegram_verification_expires: When the verification code expires.

        Reminder Settings:
            reminder_enabled: Whether payment reminders are enabled.
            reminder_days_before: Days before payment to send reminder (default: 3).
            reminder_time: Time of day to send reminders (default: 09:00).
            overdue_alerts: Whether to send alerts for overdue payments.

        Digest Settings:
            daily_digest: Whether to send daily payment digest.
            weekly_digest: Whether to send weekly payment summary.
            weekly_digest_day: Day of week for weekly digest (0=Monday, 6=Sunday).

        Quiet Hours:
            quiet_hours_enabled: Whether quiet hours are enabled.
            quiet_hours_start: Start time for quiet hours (e.g., 22:00).
            quiet_hours_end: End time for quiet hours (e.g., 07:00).

        Timestamps:
            created_at: Record creation timestamp.
            updated_at: Last modification timestamp.

    Example:
        >>> prefs = NotificationPreferences(
        ...     user_id="user-uuid",
        ...     telegram_enabled=True,
        ...     telegram_chat_id="123456789",
        ...     reminder_days_before=3,
        ... )
    """

    __tablename__ = "notification_preferences"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User relationship (one-to-one)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Telegram integration
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_verification_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telegram_verification_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Reminder settings
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=3)
    reminder_time: Mapped[time] = mapped_column(Time, default=time(9, 0))  # 09:00
    overdue_alerts: Mapped[bool] = mapped_column(Boolean, default=True)

    # Digest settings
    daily_digest: Mapped[bool] = mapped_column(Boolean, default=False)
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_digest_day: Mapped[int] = mapped_column(Integer, default=0)  # 0 = Monday

    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")  # noqa: F821

    def __repr__(self) -> str:
        """Return string representation of notification preferences."""
        return (
            f"<NotificationPreferences(user_id='{self.user_id}', telegram={self.telegram_enabled})>"
        )

    def generate_verification_code(self) -> str:
        """Generate a new verification code for Telegram linking.

        Creates a 6-character alphanumeric code and sets expiration to 10 minutes.

        Returns:
            The generated verification code.
        """
        from datetime import timedelta

        code = secrets.token_hex(3).upper()  # 6 characters
        self.telegram_verification_code = code
        self.telegram_verification_expires = datetime.utcnow() + timedelta(minutes=10)
        return code

    def verify_code(self, code: str) -> bool:
        """Verify a Telegram verification code.

        Args:
            code: The code to verify.

        Returns:
            True if the code is valid and not expired.
        """
        if not self.telegram_verification_code or not self.telegram_verification_expires:
            return False
        if datetime.utcnow() > self.telegram_verification_expires:
            return False
        return self.telegram_verification_code.upper() == code.upper()

    def clear_verification(self) -> None:
        """Clear verification code after successful linking."""
        self.telegram_verification_code = None
        self.telegram_verification_expires = None

    @property
    def is_telegram_linked(self) -> bool:
        """Check if Telegram is successfully linked.

        Returns:
            True if Telegram is enabled and verified with a chat ID.
        """
        return bool(self.telegram_enabled and self.telegram_verified and self.telegram_chat_id)

    def is_in_quiet_hours(self, current_time: time | None = None) -> bool:
        """Check if current time is within quiet hours.

        Args:
            current_time: Time to check (defaults to current UTC time).

        Returns:
            True if currently in quiet hours and quiet hours are enabled.
        """
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        if current_time is None:
            current_time = datetime.utcnow().time()

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 - 07:00)
        if start > end:
            return current_time >= start or current_time <= end
        else:
            return start <= current_time <= end
