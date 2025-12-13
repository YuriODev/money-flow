"""Authentication module for Money Flow.

This module provides authentication and authorization functionality including:
- Password hashing and verification (bcrypt)
- JWT token generation and validation
- Authentication middleware and dependencies

Sprint 1.1 - Authentication System
"""

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
    "DEFAULT_REQUIREMENTS",
    "PasswordRequirements",
    "PasswordStrengthError",
    "check_password_strength",
    "get_password_hash",
    "needs_rehash",
    "validate_password_strength",
    "verify_password",
]
