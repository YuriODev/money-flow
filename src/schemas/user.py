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


# User Preferences Schemas


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences API responses.

    Contains all configurable user preferences for the application.

    Attributes:
        currency: Default currency for display (ISO 4217 code).
        date_format: Date format preference.
        number_format: Number format preference.
        theme: UI theme preference.
        default_view: Default dashboard view.
        week_start: First day of the week.
        timezone: User's timezone (IANA format).
        language: Preferred language (ISO 639-1).
        compact_mode: Use compact UI layout.
        show_currency_symbol: Display currency symbols.

    Example:
        >>> prefs = UserPreferencesResponse(
        ...     currency="GBP",
        ...     date_format="DD/MM/YYYY",
        ...     theme="system"
        ... )
    """

    model_config = ConfigDict(from_attributes=True)

    # Display preferences
    currency: str = Field(default="GBP", description="Default currency (ISO 4217)")
    date_format: str = Field(default="DD/MM/YYYY", description="Date format preference")
    number_format: str = Field(default="1,234.56", description="Number format preference")

    # UI preferences
    theme: str = Field(default="system", description="Theme: light, dark, or system")
    default_view: str = Field(default="list", description="Default view: list, calendar, cards")
    compact_mode: bool = Field(default=False, description="Use compact UI layout")

    # Regional preferences
    week_start: str = Field(default="monday", description="First day of week: sunday or monday")
    timezone: str = Field(default="UTC", description="User timezone (IANA format)")
    language: str = Field(default="en", description="Preferred language (ISO 639-1)")

    # Currency display
    show_currency_symbol: bool = Field(default=True, description="Show currency symbols")


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences.

    All fields are optional for partial updates.

    Attributes:
        currency: Default currency (ISO 4217 code).
        date_format: Date format preference.
        number_format: Number format preference.
        theme: UI theme preference.
        default_view: Default dashboard view.
        week_start: First day of the week.
        timezone: User's timezone.
        language: Preferred language.
        compact_mode: Use compact UI layout.
        show_currency_symbol: Display currency symbols.

    Example:
        >>> update = UserPreferencesUpdate(currency="USD", theme="dark")
    """

    # Display preferences
    currency: str | None = Field(None, description="Default currency (ISO 4217)")
    date_format: str | None = Field(None, description="Date format preference")
    number_format: str | None = Field(None, description="Number format preference")

    # UI preferences
    theme: str | None = Field(None, description="Theme: light, dark, or system")
    default_view: str | None = Field(None, description="Default view: list, calendar, cards")
    compact_mode: bool | None = Field(None, description="Use compact UI layout")

    # Regional preferences
    week_start: str | None = Field(None, description="First day of week: sunday or monday")
    timezone: str | None = Field(None, description="User timezone (IANA format)")
    language: str | None = Field(None, description="Preferred language (ISO 639-1)")

    # Currency display
    show_currency_symbol: bool | None = Field(None, description="Show currency symbols")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency is a valid ISO 4217 code."""
        if v is None:
            return v
        valid_currencies = {"GBP", "USD", "EUR", "UAH", "CAD", "AUD", "JPY", "CHF", "CNY", "INR"}
        if v.upper() not in valid_currencies:
            raise ValueError(f"Invalid currency. Supported: {', '.join(sorted(valid_currencies))}")
        return v.upper()

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str | None) -> str | None:
        """Validate theme is valid."""
        if v is None:
            return v
        valid_themes = {"light", "dark", "system"}
        if v.lower() not in valid_themes:
            raise ValueError(f"Invalid theme. Supported: {', '.join(valid_themes)}")
        return v.lower()

    @field_validator("default_view")
    @classmethod
    def validate_default_view(cls, v: str | None) -> str | None:
        """Validate default view is valid."""
        if v is None:
            return v
        valid_views = {"list", "calendar", "cards", "agent"}
        if v.lower() not in valid_views:
            raise ValueError(f"Invalid view. Supported: {', '.join(valid_views)}")
        return v.lower()

    @field_validator("date_format")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format is valid."""
        if v is None:
            return v
        valid_formats = {"DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"}
        if v.upper() not in valid_formats:
            raise ValueError(f"Invalid date format. Supported: {', '.join(valid_formats)}")
        return v.upper()

    @field_validator("week_start")
    @classmethod
    def validate_week_start(cls, v: str | None) -> str | None:
        """Validate week start day is valid."""
        if v is None:
            return v
        valid_days = {"sunday", "monday"}
        if v.lower() not in valid_days:
            raise ValueError(f"Invalid week start. Supported: {', '.join(valid_days)}")
        return v.lower()
