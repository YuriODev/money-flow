"""User service for authentication operations.

This module provides business logic for user management including
registration, authentication, and profile operations.

All database operations are async for non-blocking I/O.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import TokenType, create_token_pair, decode_token
from src.auth.security import (
    get_password_hash,
    needs_rehash,
    validate_password_strength,
    verify_password,
)

# Note: Direct imports from src.auth.jwt and src.auth.security
# to avoid circular imports through src.auth.__init__.py
from src.models.user import User, UserRole
from src.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class UserNotFoundError(Exception):
    """Raised when a user is not found.

    Attributes:
        identifier: The identifier that was not found (email or ID).
    """

    def __init__(self, identifier: str) -> None:
        """Initialize the error.

        Args:
            identifier: The user identifier that was not found.
        """
        super().__init__(f"User '{identifier}' not found")
        self.identifier = identifier


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user that already exists.

    Attributes:
        email: The email that already exists.
    """

    def __init__(self, email: str) -> None:
        """Initialize the error.

        Args:
            email: The email that already exists.
        """
        super().__init__(f"User with email '{email}' already exists")
        self.email = email


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(message)


class AccountLockedError(Exception):
    """Raised when account is locked due to too many failed attempts.

    Attributes:
        locked_until: When the lockout expires.
    """

    def __init__(self, locked_until: datetime) -> None:
        """Initialize the error.

        Args:
            locked_until: When the lockout expires.
        """
        super().__init__(f"Account locked until {locked_until}")
        self.locked_until = locked_until


class AccountInactiveError(Exception):
    """Raised when attempting to authenticate an inactive account."""

    def __init__(self, message: str = "Account is inactive") -> None:
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(message)


class UserService:
    """Service for user management operations.

    Provides all business logic for user authentication and profile
    management, including registration, login, and account security.

    All database operations use async/await for non-blocking I/O.

    Attributes:
        db: Async database session for operations.

    Example:
        >>> async with get_db() as session:
        ...     service = UserService(session)
        ...     user = await service.create_user(UserCreate(
        ...         email="user@example.com",
        ...         password="SecurePass123!"
        ...     ))
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the user service.

        Args:
            db: Async database session for database operations.
        """
        self.db = db

    async def get_by_id(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            User model instance.

        Raises:
            UserNotFoundError: If user is not found.

        Example:
            >>> user = await service.get_by_id("user-123")
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The user's email address.

        Returns:
            User model instance or None if not found.

        Example:
            >>> user = await service.get_by_email("user@example.com")
        """
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        user_data: UserCreate,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Create a new user.

        Validates password strength, hashes password, and creates user record.

        Args:
            user_data: User registration data.
            role: User role (default: USER).

        Returns:
            Created User model instance.

        Raises:
            UserAlreadyExistsError: If email already exists.
            PasswordStrengthError: If password doesn't meet requirements.

        Example:
            >>> user = await service.create_user(UserCreate(
            ...     email="user@example.com",
            ...     password="SecurePass123!",
            ...     full_name="John Doe"
            ... ))
        """
        # Check if user already exists
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(user_data.email)

        # Validate password strength
        validate_password_strength(user_data.password)

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user = User(
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=role,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Created new user: {user.email}")
        return user

    async def authenticate(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate user and return tokens.

        Verifies credentials, handles account lockout, updates login tracking,
        and returns JWT tokens on success.

        Args:
            email: User's email address.
            password: User's password.

        Returns:
            Tuple of (User, access_token, refresh_token).

        Raises:
            InvalidCredentialsError: If email or password is wrong.
            AccountLockedError: If account is locked.
            AccountInactiveError: If account is deactivated.

        Example:
            >>> user, access, refresh = await service.authenticate(
            ...     "user@example.com",
            ...     "SecurePass123!"
            ... )
        """
        # Get user
        user = await self.get_by_email(email)
        if not user:
            # Use same error to prevent email enumeration
            raise InvalidCredentialsError()

        # Check if account is active
        if not user.is_active:
            raise AccountInactiveError()

        # Check if account is locked
        if user.is_locked:
            raise AccountLockedError(user.locked_until)

        # Verify password
        if not verify_password(password, user.hashed_password):
            await self._handle_failed_login(user)
            raise InvalidCredentialsError()

        # Check if password needs rehashing (algorithm upgrade)
        if needs_rehash(user.hashed_password):
            user.hashed_password = get_password_hash(password)

        # Reset failed attempts and update login time
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        # Create tokens
        access_token, refresh_token = create_token_pair(
            user_id=user.id,
            email=user.email,
        )

        logger.info(f"User authenticated: {user.email}")
        return user, access_token, refresh_token

    async def _handle_failed_login(self, user: User) -> None:
        """Handle a failed login attempt.

        Increments failed attempt counter and locks account if threshold exceeded.

        Args:
            user: User who failed login.
        """
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Account locked due to failed attempts: {user.email}")

        await self.db.commit()

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token.

        Validates refresh token and creates new token pair.

        Args:
            refresh_token: Valid refresh token.

        Returns:
            Tuple of (new_access_token, new_refresh_token).

        Raises:
            TokenError: If refresh token is invalid or expired.
            UserNotFoundError: If user no longer exists.
            AccountInactiveError: If account was deactivated.

        Example:
            >>> new_access, new_refresh = await service.refresh_tokens(
            ...     refresh_token="eyJ..."
            ... )
        """
        # Decode and validate refresh token
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)

        # Get user and verify still active
        user = await self.get_by_id(payload.user_id)
        if not user.is_active:
            raise AccountInactiveError()

        # Create new tokens
        access_token, new_refresh_token = create_token_pair(
            user_id=user.id,
            email=user.email,
        )

        logger.info(f"Tokens refreshed for user: {user.email}")
        return access_token, new_refresh_token

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user profile.

        Args:
            user_id: User ID to update.
            user_data: Updated profile data.

        Returns:
            Updated User model instance.

        Raises:
            UserNotFoundError: If user is not found.

        Example:
            >>> user = await service.update_user(
            ...     "user-123",
            ...     UserUpdate(full_name="Jane Doe")
            ... )
        """
        user = await self.get_by_id(user_id)

        # Update provided fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Updated user profile: {user.email}")
        return user

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user's password.

        Verifies current password, validates new password, and updates hash.

        Args:
            user_id: User ID.
            current_password: Current password for verification.
            new_password: New password to set.

        Raises:
            UserNotFoundError: If user is not found.
            InvalidCredentialsError: If current password is wrong.
            PasswordStrengthError: If new password doesn't meet requirements.

        Example:
            >>> await service.change_password(
            ...     "user-123",
            ...     "OldPass123!",
            ...     "NewPass456!"
            ... )
        """
        user = await self.get_by_id(user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        # Validate new password strength
        validate_password_strength(new_password)

        # Update password hash
        user.hashed_password = get_password_hash(new_password)

        await self.db.commit()
        logger.info(f"Password changed for user: {user.email}")

    async def deactivate_user(self, user_id: str) -> None:
        """Deactivate a user account.

        Args:
            user_id: User ID to deactivate.

        Raises:
            UserNotFoundError: If user is not found.

        Example:
            >>> await service.deactivate_user("user-123")
        """
        user = await self.get_by_id(user_id)
        user.is_active = False
        await self.db.commit()
        logger.info(f"Deactivated user: {user.email}")

    async def activate_user(self, user_id: str) -> None:
        """Activate a user account.

        Args:
            user_id: User ID to activate.

        Raises:
            UserNotFoundError: If user is not found.

        Example:
            >>> await service.activate_user("user-123")
        """
        user = await self.get_by_id(user_id)
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.commit()
        logger.info(f"Activated user: {user.email}")
