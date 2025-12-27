"""Google Calendar OAuth connection model.

This module defines the SQLAlchemy ORM model for storing Google Calendar
OAuth tokens and connection status for users.

Sprint 5.6 - Calendar Integration
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class GoogleCalendarSyncStatus(str, enum.Enum):
    """Sync status for Google Calendar integration.

    Attributes:
        CONNECTED: Successfully connected and ready to sync.
        DISCONNECTED: User disconnected the integration.
        TOKEN_EXPIRED: Refresh token is expired, needs re-auth.
        ERROR: An error occurred during sync.
    """

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TOKEN_EXPIRED = "token_expired"
    ERROR = "error"


class GoogleCalendarConnection(Base):
    """Google Calendar OAuth connection model.

    Stores OAuth tokens and connection state for Google Calendar integration.
    Each user can have one Google Calendar connection.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this connection.
        access_token: OAuth access token (encrypted in production).
        refresh_token: OAuth refresh token for obtaining new access tokens.
        token_expiry: When the access token expires.
        calendar_id: The Google Calendar ID to sync with (default: 'primary').
        sync_status: Current sync status.
        last_sync_at: Timestamp of last successful sync.
        sync_enabled: Whether automatic sync is enabled.
        created_at: When the connection was created.
        updated_at: When the connection was last updated.

    Example:
        >>> connection = GoogleCalendarConnection(
        ...     user_id="user-uuid",
        ...     access_token="ya29...",
        ...     refresh_token="1//...",
        ...     token_expiry=datetime.utcnow() + timedelta(hours=1),
        ... )
    """

    __tablename__ = "google_calendar_connections"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key to user (one-to-one)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # OAuth tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Calendar settings
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary")

    # Sync status
    sync_status: Mapped[GoogleCalendarSyncStatus] = mapped_column(
        Enum(GoogleCalendarSyncStatus),
        default=GoogleCalendarSyncStatus.CONNECTED,
        nullable=False,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to User
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="google_calendar_connection",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        status_val = self.sync_status.value if self.sync_status else "none"
        return f"<GoogleCalendarConnection(user_id='{self.user_id}', status={status_val})>"

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token has expired.

        Returns:
            True if token_expiry is in the past.
        """
        if self.token_expiry is None:
            return True
        return datetime.utcnow() >= self.token_expiry

    @property
    def needs_reauthorization(self) -> bool:
        """Check if the user needs to re-authorize.

        Returns:
            True if token is expired and no refresh token is available.
        """
        return self.is_token_expired and not self.refresh_token
