"""Pydantic schemas for User authentication.

This module defines Pydantic v2 schemas for request/response validation
of user authentication data. Includes schemas for registration, login,
token responses, and user profile.

Schemas:
    UserCreate: For user registration.
    UserLogin: For login requests.
    UserUpdate: For profile updates.
    UserResponse: For API responses (excludes password).
    TokenResponse: For JWT token responses.
    TokenRefreshRequest: For token refresh requests.

Security:
    - Passwords are validated for strength (uppercase, lowercase, digit, special char)
    - Common passwords are rejected
    - URLs are validated for safe schemes (no javascript:, data:, etc.)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole
from src.security.validators import validate_password_strength, validate_safe_url


class UserCreate(BaseModel):
    """Schema for user registration.

    Validates registration data including email format and password strength.

    Security:
        Password must contain:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Cannot be a common password

    Attributes:
        email: Valid email address (unique).
        password: Strong password (will be hashed).
        full_name: Optional display name.

    Example:
        >>> user = UserCreate(
        ...     email="user@example.com",
        ...     password="SecureP@ss123!",
        ...     full_name="John Doe"
        ... )
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Strong password (8-128 characters)"
    )
    full_name: str | None = Field(None, max_length=255, description="User's full name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        return validate_password_strength(v)


class UserLogin(BaseModel):
    """Schema for login requests.

    Validates login credentials.

    Attributes:
        email: User's email address.
        password: User's password.

    Example:
        >>> login = UserLogin(
        ...     email="user@example.com",
        ...     password="SecurePass123!"
        ... )
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """Schema for updating user profile.

    All fields are optional for partial updates.

    Security:
        - Avatar URL is validated for safe schemes (no javascript:, data:)

    Attributes:
        full_name: Updated display name.
        avatar_url: Updated avatar URL (validated for safety).
        preferences: JSON string of user preferences.

    Example:
        >>> update = UserUpdate(full_name="Jane Doe")
    """

    full_name: str | None = Field(None, max_length=255, description="User's full name")
    avatar_url: str | None = Field(None, max_length=500, description="Avatar URL")
    preferences: str | None = Field(None, description="User preferences (JSON)")

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        """Validate avatar URL is safe."""
        return validate_safe_url(v)


class UserResponse(BaseModel):
    """Schema for user API responses.

    Excludes sensitive data like password hash.

    Attributes:
        id: User's unique identifier.
        email: User's email address.
        full_name: User's display name.
        role: User's role (user or admin).
        is_active: Whether account is active.
        is_verified: Whether email is verified.
        avatar_url: User's avatar URL.
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.

    Example:
        >>> response = UserResponse(
        ...     id="user-123",
        ...     email="user@example.com",
        ...     role=UserRole.USER,
        ...     is_active=True,
        ...     is_verified=False,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str | None = Field(None, description="User's full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email verification status")
    avatar_url: str | None = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime = Field(..., description="Last update time")


class TokenResponse(BaseModel):
    """Schema for JWT token responses.

    Returned after successful login or token refresh.

    Attributes:
        access_token: JWT access token for API requests.
        refresh_token: JWT refresh token for obtaining new access tokens.
        token_type: Token type (always "bearer").
        expires_in: Access token expiration time in seconds.

    Example:
        >>> tokens = TokenResponse(
        ...     access_token="eyJ...",
        ...     refresh_token="eyJ...",
        ...     token_type="bearer",
        ...     expires_in=1800
        ... )
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration (seconds)")


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh requests.

    Attributes:
        refresh_token: Valid refresh token.

    Example:
        >>> refresh = TokenRefreshRequest(refresh_token="eyJ...")
    """

    refresh_token: str = Field(..., description="Refresh token")


class LoginResponse(BaseModel):
    """Schema for login response with user info and tokens.

    Combines token response with user data for convenience.

    Attributes:
        user: User profile data.
        tokens: JWT tokens.

    Example:
        >>> response = LoginResponse(
        ...     user=UserResponse(...),
        ...     tokens=TokenResponse(...)
        ... )
    """

    user: UserResponse = Field(..., description="User profile")
    tokens: TokenResponse = Field(..., description="Authentication tokens")


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests.

    Security:
        New password must meet strength requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Cannot be a common password

    Attributes:
        current_password: User's current password.
        new_password: New strong password to set.

    Example:
        >>> change = PasswordChangeRequest(
        ...     current_password="OldP@ss123!",
        ...     new_password="NewP@ss456!"
        ... )
    """

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New strong password (8-128 characters)"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        return validate_password_strength(v)
