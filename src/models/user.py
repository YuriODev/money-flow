"""User ORM model for authentication.

This module defines the SQLAlchemy ORM model for users, including
the UserRole enum for role-based access control.

The model uses async-compatible SQLAlchemy 2.0 patterns and follows
the existing codebase conventions for Money Flow.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration for access control.

    Defines the possible roles for users in the system.
    Inherits from str for JSON serialization compatibility.

    Attributes:
        USER: Standard user with access to own data only.
        ADMIN: Administrator with full system access.

    Example:
        >>> UserRole.USER.value
        'user'
        >>> UserRole("admin")
        <UserRole.ADMIN: 'admin'>
    """

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization.

    Represents a user account with authentication credentials,
    profile information, and role-based access control.
    Automatically tracks creation and update times.

    Attributes:
        id: UUID primary key (auto-generated).
        email: Unique email address for login. Indexed for lookup.
        hashed_password: Bcrypt-hashed password. Never store plaintext.
        full_name: User's display name (optional).
        role: User role for access control (default: USER).
        is_active: Whether the account is active (default: True).
        is_verified: Whether email has been verified (default: False).
        avatar_url: URL to user's avatar image (optional).
        preferences: JSON string for user preferences (optional).
        last_login_at: Timestamp of last successful login.
        failed_login_attempts: Count of consecutive failed logins.
        locked_until: Account lockout expiration (for brute force protection).
        created_at: Account creation timestamp.
        updated_at: Last modification timestamp.
        subscriptions: Relationship to user's subscriptions.

    Example:
        >>> user = User(
        ...     email="user@example.com",
        ...     hashed_password="$2b$12$...",
        ...     full_name="John Doe",
        ...     role=UserRole.USER,
        ... )
        >>> user.email
        'user@example.com'

    Security Notes:
        - Password is stored as bcrypt hash, never plaintext
        - Account lockout after failed_login_attempts > threshold
        - Email verification required for sensitive operations
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Role and status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.USER, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # User preferences (stored as JSON string)
    preferences: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Security tracking
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships - User owns subscriptions
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # One-to-one relationship with notification preferences
    notification_preferences: Mapped["NotificationPreferences | None"] = relationship(  # noqa: F821
        "NotificationPreferences",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation of user.

        Returns:
            Debug-friendly string with email and role.

        Example:
            >>> str(user)
            "<User(email='user@example.com', role=user)>"
        """
        return f"<User(email='{self.email}', role={self.role.value})>"

    @property
    def is_locked(self) -> bool:
        """Check if the account is currently locked.

        Returns:
            True if account is locked and lockout hasn't expired.
        """
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def can_login(self) -> bool:
        """Check if the user can attempt login.

        Returns:
            True if account is active and not locked.
        """
        return self.is_active and not self.is_locked
