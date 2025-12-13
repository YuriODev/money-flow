"""Authentication module for Money Flow.

This module provides authentication and authorization functionality including:
- Password hashing and verification (bcrypt)
- JWT token generation and validation
- Authentication middleware and dependencies

Sprint 1.1 - Authentication System
"""

from src.auth.jwt import (
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenPayload,
    TokenType,
    TokenTypeMismatchError,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    get_token_expiry,
    is_token_expired,
    refresh_access_token,
)
from src.auth.security import (
    DEFAULT_REQUIREMENTS,
    PasswordRequirements,
    PasswordStrengthError,
    check_password_strength,
    get_password_hash,
    needs_rehash,
    validate_password_strength,
    verify_password,
)

__all__ = [
    # JWT Token functions
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenPayload",
    "TokenType",
    "TokenTypeMismatchError",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "get_token_expiry",
    "is_token_expired",
    "refresh_access_token",
    # Password security functions
    "DEFAULT_REQUIREMENTS",
    "PasswordRequirements",
    "PasswordStrengthError",
    "check_password_strength",
    "get_password_hash",
    "needs_rehash",
    "validate_password_strength",
    "verify_password",
]
