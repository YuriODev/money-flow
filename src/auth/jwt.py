"""JWT Token management for authentication.

This module provides JWT (JSON Web Token) creation, validation, and management
for secure user authentication. Implements access tokens for API requests
and refresh tokens for obtaining new access tokens.

Security features:
- HS256 algorithm with configurable secret key
- Separate access and refresh tokens with different expiration times
- Token type validation to prevent token misuse
- Comprehensive error handling for invalid/expired tokens

Example:
    >>> from src.auth.jwt import create_access_token, decode_token
    >>> token = create_access_token(user_id="user-123", email="user@example.com")
    >>> payload = decode_token(token)
    >>> payload.user_id
    'user-123'
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.core.config import settings


class TokenType(str, Enum):
    """Token type enumeration.

    Distinguishes between access and refresh tokens to prevent
    token misuse (e.g., using a refresh token as an access token).

    Attributes:
        ACCESS: Short-lived token for API authentication.
        REFRESH: Long-lived token for obtaining new access tokens.

    Example:
        >>> TokenType.ACCESS.value
        'access'
    """

    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(Exception):
    """Base exception for token-related errors.

    Attributes:
        message: Human-readable error message.
        code: Error code for programmatic handling.

    Example:
        >>> raise TokenError("Token has expired", code="token_expired")
    """

    def __init__(self, message: str, code: str = "token_error") -> None:
        """Initialize TokenError.

        Args:
            message: Human-readable error message.
            code: Error code for programmatic handling.
        """
        super().__init__(message)
        self.message = message
        self.code = code


class TokenExpiredError(TokenError):
    """Exception raised when a token has expired.

    Example:
        >>> raise TokenExpiredError()
    """

    def __init__(self, message: str = "Token has expired") -> None:
        """Initialize TokenExpiredError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, code="token_expired")


class TokenInvalidError(TokenError):
    """Exception raised when a token is invalid.

    Example:
        >>> raise TokenInvalidError("Invalid token signature")
    """

    def __init__(self, message: str = "Invalid token") -> None:
        """Initialize TokenInvalidError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, code="token_invalid")


class TokenTypeMismatchError(TokenError):
    """Exception raised when token type doesn't match expected type.

    Example:
        >>> raise TokenTypeMismatchError("Expected access token, got refresh")
    """

    def __init__(self, message: str = "Token type mismatch") -> None:
        """Initialize TokenTypeMismatchError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, code="token_type_mismatch")


@dataclass
class TokenPayload:
    """Decoded JWT token payload.

    Contains the essential claims extracted from a validated JWT token.

    Attributes:
        user_id: Unique identifier of the authenticated user.
        email: User's email address.
        token_type: Type of token (access or refresh).
        exp: Token expiration timestamp.
        iat: Token issued-at timestamp.
        jti: Unique token identifier for revocation tracking.

    Example:
        >>> payload = TokenPayload(
        ...     user_id="user-123",
        ...     email="user@example.com",
        ...     token_type=TokenType.ACCESS,
        ...     exp=datetime.now(UTC) + timedelta(hours=1),
        ...     iat=datetime.now(UTC),
        ...     jti="unique-token-id"
        ... )
    """

    user_id: str
    email: str
    token_type: TokenType
    exp: datetime
    iat: datetime
    jti: str


def create_access_token(
    user_id: str,
    email: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a new JWT access token.

    Access tokens are short-lived tokens used for API authentication.
    They contain user identity and should be included in the Authorization
    header of API requests.

    Args:
        user_id: Unique identifier of the user.
        email: User's email address.
        additional_claims: Optional additional claims to include in the token.

    Returns:
        Encoded JWT access token string.

    Example:
        >>> token = create_access_token(
        ...     user_id="user-123",
        ...     email="user@example.com"
        ... )
        >>> token.startswith("eyJ")
        True

    Security Notes:
        - Default expiration: 30 minutes (configurable)
        - Store securely on client side (httpOnly cookie recommended)
        - Do not include sensitive data in additional_claims
    """
    return _create_token(
        user_id=user_id,
        email=email,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        additional_claims=additional_claims,
    )


def create_refresh_token(
    user_id: str,
    email: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a new JWT refresh token.

    Refresh tokens are long-lived tokens used to obtain new access tokens
    without requiring the user to re-authenticate. They should be stored
    securely and transmitted only when refreshing access tokens.

    Args:
        user_id: Unique identifier of the user.
        email: User's email address.
        additional_claims: Optional additional claims to include in the token.

    Returns:
        Encoded JWT refresh token string.

    Example:
        >>> token = create_refresh_token(
        ...     user_id="user-123",
        ...     email="user@example.com"
        ... )
        >>> token.startswith("eyJ")
        True

    Security Notes:
        - Default expiration: 7 days (configurable)
        - Store in httpOnly, secure cookie only
        - Implement token rotation on each refresh
        - Consider maintaining a revocation list
    """
    return _create_token(
        user_id=user_id,
        email=email,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
        additional_claims=additional_claims,
    )


def _create_token(
    user_id: str,
    email: str,
    token_type: TokenType,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT token with specified parameters.

    Internal function that handles the actual token creation with
    all required claims.

    Args:
        user_id: Unique identifier of the user.
        email: User's email address.
        token_type: Type of token (access or refresh).
        expires_delta: Time until token expiration.
        additional_claims: Optional additional claims to include.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "type": token_type.value,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),  # Unique token ID
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(
    token: str,
    expected_type: TokenType | None = None,
) -> TokenPayload:
    """Decode and validate a JWT token.

    Decodes the token, validates its signature, checks expiration,
    and optionally verifies the token type matches the expected type.

    Args:
        token: The JWT token string to decode.
        expected_type: Expected token type (access/refresh). If provided,
            raises TokenTypeMismatchError if token type doesn't match.

    Returns:
        TokenPayload containing the decoded claims.

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is malformed or signature is invalid.
        TokenTypeMismatchError: If token type doesn't match expected_type.

    Example:
        >>> token = create_access_token("user-123", "user@example.com")
        >>> payload = decode_token(token, expected_type=TokenType.ACCESS)
        >>> payload.user_id
        'user-123'

    Security Notes:
        - Always specify expected_type to prevent token substitution attacks
        - Token validation is performed synchronously (no DB lookups)
        - For revocation checking, implement a separate blacklist check
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError() from e
    except InvalidTokenError as e:
        raise TokenInvalidError(str(e)) from e

    # Validate token type if expected
    token_type_str = payload.get("type")
    if not token_type_str:
        raise TokenInvalidError("Token missing type claim")

    try:
        token_type = TokenType(token_type_str)
    except ValueError as e:
        raise TokenInvalidError(f"Invalid token type: {token_type_str}") from e

    if expected_type and token_type != expected_type:
        raise TokenTypeMismatchError(
            f"Expected {expected_type.value} token, got {token_type.value}"
        )

    # Extract and validate required claims
    user_id = payload.get("sub")
    email = payload.get("email")
    exp = payload.get("exp")
    iat = payload.get("iat")
    jti = payload.get("jti")

    if not all([user_id, email, exp, iat, jti]):
        raise TokenInvalidError("Token missing required claims")

    return TokenPayload(
        user_id=user_id,
        email=email,
        token_type=token_type,
        exp=datetime.fromtimestamp(exp, tz=UTC),
        iat=datetime.fromtimestamp(iat, tz=UTC),
        jti=jti,
    )


def create_token_pair(
    user_id: str,
    email: str,
    additional_claims: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Create both access and refresh tokens for a user.

    Convenience function that creates both token types at once,
    typically used during login or token refresh operations.

    Args:
        user_id: Unique identifier of the user.
        email: User's email address.
        additional_claims: Optional additional claims to include in both tokens.

    Returns:
        Tuple of (access_token, refresh_token).

    Example:
        >>> access, refresh = create_token_pair("user-123", "user@example.com")
        >>> access.startswith("eyJ")
        True
        >>> refresh.startswith("eyJ")
        True
    """
    access_token = create_access_token(user_id, email, additional_claims)
    refresh_token = create_refresh_token(user_id, email, additional_claims)
    return access_token, refresh_token


def refresh_access_token(refresh_token: str) -> str:
    """Create a new access token using a valid refresh token.

    Validates the refresh token and creates a new access token
    with the same user information. The refresh token itself
    is not rotated by this function.

    Args:
        refresh_token: Valid refresh token string.

    Returns:
        New access token string.

    Raises:
        TokenExpiredError: If the refresh token has expired.
        TokenInvalidError: If the refresh token is invalid.
        TokenTypeMismatchError: If the token is not a refresh token.

    Example:
        >>> refresh = create_refresh_token("user-123", "user@example.com")
        >>> new_access = refresh_access_token(refresh)
        >>> new_access.startswith("eyJ")
        True

    Security Notes:
        - Consider implementing token rotation (return new refresh token too)
        - Consider adding refresh token to blacklist after use
        - May want to add rate limiting on refresh endpoint
    """
    payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    return create_access_token(user_id=payload.user_id, email=payload.email)


def get_token_expiry(token: str) -> datetime:
    """Get the expiration datetime of a token without full validation.

    Useful for checking if a token is expired without verifying
    all claims. Does not validate signature.

    Args:
        token: JWT token string.

    Returns:
        Token expiration datetime in UTC.

    Raises:
        TokenInvalidError: If token cannot be decoded.

    Example:
        >>> token = create_access_token("user-123", "user@example.com")
        >>> expiry = get_token_expiry(token)
        >>> expiry > datetime.now(UTC)
        True

    Security Notes:
        - This function does NOT validate the token signature
        - Only use for UI/client-side expiration checks
        - Always use decode_token for security-critical operations
    """
    try:
        # Decode without verification to get expiry
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
        exp = payload.get("exp")
        if not exp:
            raise TokenInvalidError("Token missing expiration claim")
        return datetime.fromtimestamp(exp, tz=UTC)
    except InvalidTokenError as e:
        raise TokenInvalidError(str(e)) from e


def is_token_expired(token: str) -> bool:
    """Check if a token is expired without full validation.

    Quick check for token expiration, useful for client-side
    token management.

    Args:
        token: JWT token string.

    Returns:
        True if token is expired, False otherwise.

    Example:
        >>> token = create_access_token("user-123", "user@example.com")
        >>> is_token_expired(token)
        False

    Security Notes:
        - This function does NOT validate the token signature
        - Only use for UI/client-side checks
        - Always use decode_token for security-critical operations
    """
    try:
        expiry = get_token_expiry(token)
        return datetime.now(UTC) >= expiry
    except TokenError:
        return True
