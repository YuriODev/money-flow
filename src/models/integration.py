"""Integration models for IFTTT/Zapier connections.

This module defines SQLAlchemy ORM models for external service integrations,
supporting REST Hook subscriptions for Zapier and IFTTT webhook triggers.

Sprint 5.6 - IFTTT/Zapier Integration
"""

import enum
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class IntegrationType(str, enum.Enum):
    """Types of external integrations.

    Attributes:
        ZAPIER: Zapier automation platform.
        IFTTT: If This Then That service.
        CUSTOM: Custom/generic webhook integration.
    """

    ZAPIER = "zapier"
    IFTTT = "ifttt"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    """Status of an integration connection.

    Attributes:
        ACTIVE: Integration is active and receiving events.
        PAUSED: Integration temporarily paused by user.
        EXPIRED: API key or subscription expired.
        REVOKED: Access revoked by user.
    """

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    REVOKED = "revoked"


class APIKey(Base):
    """API Key model for external service authentication.

    Stores API keys that can be used by IFTTT, Zapier, or other
    external services to authenticate with our API.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this key.
        name: Human-readable name for the API key.
        key_hash: Hashed API key (we don't store plain keys).
        key_prefix: First 8 chars of key for identification.
        integration_type: Type of integration this key is for.
        scopes: Comma-separated list of allowed scopes.
        is_active: Whether the key is currently active.
        last_used_at: When the key was last used.
        expires_at: Optional expiration date.
        created_at: When the key was created.

    Example:
        >>> api_key = APIKey(
        ...     user_id="user-uuid",
        ...     name="Zapier Integration",
        ...     integration_type=IntegrationType.ZAPIER,
        ... )
    """

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Key details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hash
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # First 8 chars for ID
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType), default=IntegrationType.CUSTOM, nullable=False
    )
    scopes: Mapped[str] = mapped_column(
        String(500), default="read:subscriptions,write:subscriptions", nullable=False
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # noqa: F821

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<APIKey(name='{self.name}', prefix='{self.key_prefix}...', type={self.integration_type.value})>"

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key.

        Returns:
            Tuple of (full_key, key_hash, key_prefix).
            The full_key should be shown to user once and never stored.
        """
        import hashlib

        # Generate a secure random key: mf_live_xxxxx (32 random chars)
        random_part = secrets.token_hex(16)
        full_key = f"mf_live_{random_part}"

        # Hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Prefix for identification
        key_prefix = full_key[:8]

        return full_key, key_hash, key_prefix

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison.

        Args:
            key: The plain API key.

        Returns:
            SHA-256 hash of the key.
        """
        import hashlib

        return hashlib.sha256(key.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Check if the key has expired.

        Returns:
            True if expires_at is set and in the past.
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if the key has a specific scope.

        Args:
            scope: The scope to check (e.g., 'read:subscriptions').

        Returns:
            True if the key has this scope.
        """
        return scope in self.scopes.split(",")

    def record_usage(self) -> None:
        """Record that the key was used."""
        self.last_used_at = datetime.utcnow()


class RestHookSubscription(Base):
    """REST Hook subscription for Zapier/IFTTT.

    Stores webhook subscriptions created by external services
    via REST Hook protocol (subscribe/unsubscribe endpoints).

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this subscription.
        api_key_id: Foreign key to the API key used to create this.
        integration_type: Type of integration (Zapier, IFTTT, etc.).
        target_url: URL to send webhook payloads to.
        event_type: Event type this subscription is for.
        status: Current subscription status.
        delivery_count: Number of successful deliveries.
        failure_count: Number of failed deliveries.
        last_delivery_at: When the last delivery was made.
        created_at: When the subscription was created.

    Example:
        >>> hook = RestHookSubscription(
        ...     user_id="user-uuid",
        ...     target_url="https://hooks.zapier.com/...",
        ...     event_type="subscription.created",
        ...     integration_type=IntegrationType.ZAPIER,
        ... )
    """

    __tablename__ = "rest_hook_subscriptions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # API key used to create this subscription (optional)
    api_key_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True
    )

    # Subscription details
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType), nullable=False, index=True
    )
    target_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Status
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.ACTIVE, nullable=False
    )

    # Statistics
    delivery_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rest_hook_subscriptions")  # noqa: F821
    api_key: Mapped["APIKey | None"] = relationship("APIKey")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<RestHookSubscription(event={self.event_type}, type={self.integration_type.value}, status={self.status.value})>"

    def record_success(self) -> None:
        """Record a successful delivery."""
        self.delivery_count += 1
        self.last_delivery_at = datetime.utcnow()
        self.last_error = None

    def record_failure(self, error: str) -> None:
        """Record a failed delivery.

        Args:
            error: Error message.
        """
        self.failure_count += 1
        self.last_delivery_at = datetime.utcnow()
        self.last_error = error[:500] if error else None

    def pause(self) -> None:
        """Pause the subscription."""
        self.status = IntegrationStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused subscription."""
        self.status = IntegrationStatus.ACTIVE

    def revoke(self) -> None:
        """Revoke the subscription."""
        self.status = IntegrationStatus.REVOKED
