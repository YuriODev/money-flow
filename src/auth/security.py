"""Password security utilities using bcrypt.

This module provides secure password hashing and verification using bcrypt,
along with password strength validation for user registration.

Security features:
- Bcrypt hashing with configurable work factor (default: 12 rounds)
- Constant-time password verification to prevent timing attacks
- Password strength validation with configurable requirements

Example:
    >>> from src.auth.security import get_password_hash, verify_password
    >>> hashed = get_password_hash("my_secure_password")
    >>> verify_password("my_secure_password", hashed)
    True
    >>> verify_password("wrong_password", hashed)
    False
"""

import re
from dataclasses import dataclass

from passlib.context import CryptContext

# Bcrypt context with 12 rounds (2^12 iterations)
# This provides good security while keeping hashing time under 300ms
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


class PasswordStrengthError(ValueError):
    """Exception raised when password doesn't meet strength requirements.

    Attributes:
        message: Human-readable error message.
        errors: List of specific validation failures.

    Example:
        >>> raise PasswordStrengthError(
        ...     "Password too weak",
        ...     ["Must be at least 8 characters", "Must contain uppercase"]
        ... )
    """

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        """Initialize PasswordStrengthError.

        Args:
            message: Human-readable error message.
            errors: List of specific validation failures.
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or []


@dataclass
class PasswordRequirements:
    """Password strength requirements configuration.

    Attributes:
        min_length: Minimum password length (default: 8).
        max_length: Maximum password length (default: 128).
        require_uppercase: Require at least one uppercase letter.
        require_lowercase: Require at least one lowercase letter.
        require_digit: Require at least one digit.
        require_special: Require at least one special character.
        special_chars: Allowed special characters.

    Example:
        >>> reqs = PasswordRequirements(min_length=12, require_special=True)
        >>> reqs.min_length
        12
    """

    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;':\",./<>?"


# Default password requirements
DEFAULT_REQUIREMENTS = PasswordRequirements()


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Uses bcrypt with 12 rounds for secure one-way hashing.
    The resulting hash includes the salt and algorithm info.

    Args:
        password: Plaintext password to hash.

    Returns:
        Bcrypt hash string (60 characters).

    Example:
        >>> hashed = get_password_hash("my_password")
        >>> hashed.startswith("$2b$")
        True
        >>> len(hashed)
        60

    Security Notes:
        - Never log or store the plaintext password
        - Each call generates a unique hash due to random salt
        - Hash includes algorithm version and work factor
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Plaintext password to verify.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.

    Example:
        >>> hashed = get_password_hash("correct_password")
        >>> verify_password("correct_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False

    Security Notes:
        - Uses constant-time comparison (timing-safe)
        - Automatically handles different bcrypt versions
        - Returns False for invalid hash formats
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Return False for any verification errors (invalid hash format, etc.)
        return False


def validate_password_strength(
    password: str,
    requirements: PasswordRequirements | None = None,
) -> bool:
    """Validate password meets strength requirements.

    Checks password against configurable requirements and raises
    PasswordStrengthError with detailed error messages if validation fails.

    Args:
        password: Password to validate.
        requirements: Custom requirements (uses DEFAULT_REQUIREMENTS if None).

    Returns:
        True if password meets all requirements.

    Raises:
        PasswordStrengthError: If password doesn't meet requirements.
            Contains list of specific failures in `errors` attribute.

    Example:
        >>> validate_password_strength("WeakPwd1!")
        True
        >>> validate_password_strength("weak")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        PasswordStrengthError: Password does not meet requirements

    Security Notes:
        - Does not log or expose the actual password
        - Returns generic errors to avoid information disclosure
    """
    reqs = requirements or DEFAULT_REQUIREMENTS
    errors: list[str] = []

    # Length checks
    if len(password) < reqs.min_length:
        errors.append(f"Must be at least {reqs.min_length} characters")

    if len(password) > reqs.max_length:
        errors.append(f"Must be at most {reqs.max_length} characters")

    # Character type checks
    if reqs.require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Must contain at least one uppercase letter")

    if reqs.require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Must contain at least one lowercase letter")

    if reqs.require_digit and not re.search(r"\d", password):
        errors.append("Must contain at least one digit")

    if reqs.require_special:
        # Escape special regex characters
        escaped_chars = re.escape(reqs.special_chars)
        if not re.search(f"[{escaped_chars}]", password):
            errors.append("Must contain at least one special character")

    if errors:
        raise PasswordStrengthError("Password does not meet requirements", errors)

    return True


def check_password_strength(password: str) -> dict[str, bool | int | list[str]]:
    """Analyze password strength without raising exceptions.

    Provides detailed strength analysis for UI feedback.

    Args:
        password: Password to analyze.

    Returns:
        Dictionary with strength analysis:
            - is_valid: Whether password meets all requirements
            - length: Password length
            - has_uppercase: Contains uppercase letter
            - has_lowercase: Contains lowercase letter
            - has_digit: Contains digit
            - has_special: Contains special character
            - errors: List of unmet requirements (empty if valid)

    Example:
        >>> result = check_password_strength("MyPass123!")
        >>> result["is_valid"]
        True
        >>> result["has_uppercase"]
        True
    """
    reqs = DEFAULT_REQUIREMENTS
    errors: list[str] = []

    has_uppercase = bool(re.search(r"[A-Z]", password))
    has_lowercase = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    escaped_chars = re.escape(reqs.special_chars)
    has_special = bool(re.search(f"[{escaped_chars}]", password))

    # Check requirements
    if len(password) < reqs.min_length:
        errors.append(f"Must be at least {reqs.min_length} characters")
    if len(password) > reqs.max_length:
        errors.append(f"Must be at most {reqs.max_length} characters")
    if reqs.require_uppercase and not has_uppercase:
        errors.append("Must contain at least one uppercase letter")
    if reqs.require_lowercase and not has_lowercase:
        errors.append("Must contain at least one lowercase letter")
    if reqs.require_digit and not has_digit:
        errors.append("Must contain at least one digit")
    if reqs.require_special and not has_special:
        errors.append("Must contain at least one special character")

    return {
        "is_valid": len(errors) == 0,
        "length": len(password),
        "has_uppercase": has_uppercase,
        "has_lowercase": has_lowercase,
        "has_digit": has_digit,
        "has_special": has_special,
        "errors": errors,
    }


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be rehashed.

    Returns True if the hash uses an outdated algorithm or work factor.
    Useful for gradually upgrading password hashes on login.

    Args:
        hashed_password: Bcrypt hash to check.

    Returns:
        True if hash should be regenerated with current settings.

    Example:
        >>> # Old hash with fewer rounds would return True
        >>> needs_rehash("$2b$12$...")  # Current settings
        False

    Security Notes:
        - Call this on successful login to upgrade old hashes
        - Rehash immediately if True, then update stored hash
    """
    return pwd_context.needs_update(hashed_password)
