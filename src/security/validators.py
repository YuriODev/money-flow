"""Enhanced Pydantic validators for input security.

This module provides custom validators for enhanced security validation
including password strength, string sanitization, URL safety, and more.

Sprint 1.2.3 - Input Validation Enhancement

Security Features:
    - Password strength validation (entropy, common patterns)
    - String sanitization (XSS, SQL injection prevention)
    - URL safety validation (block javascript:, data:, etc.)
    - Currency code validation against allowed list
    - UUID format validation
    - Safe text normalization

Example:
    >>> from src.security.validators import validate_password_strength
    >>>
    >>> # Valid password
    >>> validate_password_strength("SecureP@ss123!")
    'SecureP@ss123!'
    >>>
    >>> # Weak password raises ValueError
    >>> validate_password_strength("password123")
    ValueError: Password too weak...
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata
from typing import Annotated, Any
from urllib.parse import urlparse

from pydantic import AfterValidator, BeforeValidator, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Allowed currencies (ISO 4217)
ALLOWED_CURRENCIES = frozenset({"GBP", "USD", "EUR", "UAH", "PLN", "CHF", "CAD", "AUD", "JPY"})

# Common weak passwords to reject
COMMON_PASSWORDS = frozenset(
    {
        "password",
        "password123",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "monkey",
        "letmein",
        "dragon",
        "111111",
        "baseball",
        "iloveyou",
        "trustno1",
        "sunshine",
        "master",
        "welcome",
        "shadow",
        "ashley",
        "football",
        "jesus",
        "michael",
        "ninja",
        "mustang",
        "password1",
    }
)

# Dangerous URL schemes
DANGEROUS_SCHEMES = frozenset({"javascript", "data", "vbscript", "file"})

# Patterns for XSS detection in text
XSS_PATTERNS = [
    re.compile(r"<script\b[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, etc.
    re.compile(r"<iframe\b", re.IGNORECASE),
    re.compile(r"<object\b", re.IGNORECASE),
    re.compile(r"<embed\b", re.IGNORECASE),
    re.compile(r"<link\b[^>]*href", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),  # CSS expression
    re.compile(r"url\s*\(\s*['\"]?\s*javascript", re.IGNORECASE),
]

# Patterns for SQL injection detection
SQL_PATTERNS = [
    re.compile(r";\s*(drop|delete|truncate|update|insert)\s+", re.IGNORECASE),
    re.compile(r"'\s*or\s+'?1'?\s*=\s*'?1", re.IGNORECASE),
    re.compile(r"'\s*or\s+''='", re.IGNORECASE),
    re.compile(r"--\s*$", re.MULTILINE),  # SQL comment at end
    re.compile(r"/\*.*?\*/", re.DOTALL),  # SQL block comment
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"xp_cmdshell", re.IGNORECASE),
]

# UUID pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Hex color pattern
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ============================================================================
# Password Validation
# ============================================================================


def validate_password_strength(password: str) -> str:
    """Validate password strength with comprehensive checks.

    Enforces:
        - Minimum 8 characters, maximum 128
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Not a common password
        - No more than 3 consecutive identical characters

    Args:
        password: Plain text password to validate.

    Returns:
        The original password if valid.

    Raises:
        ValueError: If password doesn't meet strength requirements.

    Example:
        >>> validate_password_strength("MySecure@Pass123")
        'MySecure@Pass123'
        >>> validate_password_strength("weak")
        ValueError: Password must be at least 8 characters
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters")

    # Check against common passwords
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common. Please choose a stronger password.")

    # Check for required character types
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'`~]", password))

    missing = []
    if not has_upper:
        missing.append("uppercase letter")
    if not has_lower:
        missing.append("lowercase letter")
    if not has_digit:
        missing.append("digit")
    if not has_special:
        missing.append("special character")

    if missing:
        raise ValueError(f"Password must contain at least one: {', '.join(missing)}")

    # Check for repeated characters (e.g., "aaaa")
    if re.search(r"(.)\1{3,}", password):
        raise ValueError("Password cannot contain more than 3 consecutive identical characters")

    # Check for sequential characters (e.g., "1234", "abcd")
    if _has_sequential_chars(password, 4):
        raise ValueError("Password cannot contain more than 3 sequential characters")

    return password


def _has_sequential_chars(s: str, length: int) -> bool:
    """Check if string contains sequential characters.

    Args:
        s: String to check.
        length: Minimum sequential length to detect.

    Returns:
        True if sequential characters found.
    """
    s_lower = s.lower()
    for i in range(len(s_lower) - length + 1):
        chunk = s_lower[i : i + length]
        # Check if all characters are sequential
        if all(ord(chunk[j + 1]) == ord(chunk[j]) + 1 for j in range(length - 1)):
            return True
        # Check reverse sequence
        if all(ord(chunk[j + 1]) == ord(chunk[j]) - 1 for j in range(length - 1)):
            return True
    return False


# ============================================================================
# String Sanitization
# ============================================================================


def sanitize_string(value: str) -> str:
    """Sanitize string input for safe storage and display.

    Performs:
        - Unicode normalization (NFC)
        - HTML entity encoding for dangerous characters
        - Strips leading/trailing whitespace
        - Collapses multiple spaces
        - Removes null bytes and control characters

    Args:
        value: Raw string input.

    Returns:
        Sanitized string safe for storage.

    Example:
        >>> sanitize_string("  Hello <script>  ")
        'Hello &lt;script&gt;'
    """
    if not value:
        return value

    # Normalize Unicode
    normalized = unicodedata.normalize("NFC", value)

    # Remove null bytes and most control characters (keep newlines, tabs)
    cleaned = "".join(char for char in normalized if char.isprintable() or char in "\n\t")

    # Strip and collapse whitespace
    cleaned = " ".join(cleaned.split())

    # Encode HTML entities for dangerous characters
    # This prevents XSS when displaying user input
    cleaned = html.escape(cleaned, quote=True)

    return cleaned


def sanitize_name(value: str) -> str:
    """Sanitize a name field (subscription name, card name, etc.).

    More restrictive than general string sanitization:
        - No HTML entities needed (names shouldn't have < or >)
        - Single line only
        - Printable characters only

    Args:
        value: Name to sanitize.

    Returns:
        Sanitized name.

    Raises:
        ValueError: If name contains invalid characters.

    Example:
        >>> sanitize_name("Netflix Premium")
        'Netflix Premium'
        >>> sanitize_name("Bad<script>Name")
        ValueError: Name contains invalid characters
    """
    if not value:
        return value

    # Normalize Unicode
    normalized = unicodedata.normalize("NFC", value)

    # Remove control characters
    cleaned = "".join(char for char in normalized if char.isprintable())

    # Strip whitespace
    cleaned = cleaned.strip()

    # Check for HTML/script injection attempts
    if re.search(r"[<>]", cleaned):
        raise ValueError("Name contains invalid characters")

    # Collapse multiple spaces
    cleaned = " ".join(cleaned.split())

    return cleaned


def validate_safe_text(value: str) -> str:
    """Validate text doesn't contain XSS or SQL injection patterns.

    Used for freeform text fields like notes.

    Args:
        value: Text to validate.

    Returns:
        The original text if safe.

    Raises:
        ValueError: If dangerous patterns detected.

    Example:
        >>> validate_safe_text("This is a normal note")
        'This is a normal note'
        >>> validate_safe_text("<script>alert('xss')</script>")
        ValueError: Text contains potentially dangerous content
    """
    if not value:
        return value

    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            logger.warning(f"XSS pattern detected in text input: {value[:50]}...")
            raise ValueError("Text contains potentially dangerous content")

    # Check for SQL injection patterns
    for pattern in SQL_PATTERNS:
        if pattern.search(value):
            logger.warning(f"SQL injection pattern detected in text input: {value[:50]}...")
            raise ValueError("Text contains potentially dangerous content")

    return value


# ============================================================================
# URL Validation
# ============================================================================


def validate_safe_url(url: str | None) -> str | None:
    """Validate URL is safe (no javascript:, data:, etc.).

    Args:
        url: URL to validate.

    Returns:
        The original URL if safe, None if input was None.

    Raises:
        ValueError: If URL uses a dangerous scheme.

    Example:
        >>> validate_safe_url("https://example.com/image.png")
        'https://example.com/image.png'
        >>> validate_safe_url("javascript:alert('xss')")
        ValueError: URL scheme not allowed
    """
    if url is None:
        return None

    if not url.strip():
        return None

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        # Empty scheme is relative URL - generally safe
        if not scheme:
            return url

        # Check for dangerous schemes
        if scheme in DANGEROUS_SCHEMES:
            logger.warning(f"Dangerous URL scheme blocked: {scheme}")
            raise ValueError(f"URL scheme '{scheme}' not allowed")

        # Only allow http and https for absolute URLs
        if scheme not in {"http", "https"}:
            raise ValueError(f"URL scheme '{scheme}' not allowed. Use http or https.")

        return url

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        raise ValueError("Invalid URL format")


# ============================================================================
# Currency Validation
# ============================================================================


def validate_currency(currency: str) -> str:
    """Validate currency code is in allowed list.

    Args:
        currency: ISO 4217 currency code.

    Returns:
        Uppercase currency code.

    Raises:
        ValueError: If currency not in allowed list.

    Example:
        >>> validate_currency("gbp")
        'GBP'
        >>> validate_currency("XYZ")
        ValueError: Currency 'XYZ' not supported
    """
    upper_currency = currency.upper().strip()

    if upper_currency not in ALLOWED_CURRENCIES:
        allowed = ", ".join(sorted(ALLOWED_CURRENCIES))
        raise ValueError(f"Currency '{currency}' not supported. Allowed: {allowed}")

    return upper_currency


# ============================================================================
# UUID Validation
# ============================================================================


def validate_uuid(value: str | None) -> str | None:
    """Validate string is a valid UUID format.

    Args:
        value: String to validate as UUID.

    Returns:
        Lowercase UUID string, or None if input was None.

    Raises:
        ValueError: If string is not a valid UUID.

    Example:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        '550e8400-e29b-41d4-a716-446655440000'
        >>> validate_uuid("not-a-uuid")
        ValueError: Invalid UUID format
    """
    if value is None:
        return None

    value = value.strip().lower()

    if not UUID_PATTERN.match(value):
        raise ValueError("Invalid UUID format")

    return value


# ============================================================================
# Color Validation
# ============================================================================


def validate_hex_color(color: str) -> str:
    """Validate hex color code format.

    Args:
        color: Hex color code (e.g., #FF5733).

    Returns:
        Uppercase hex color.

    Raises:
        ValueError: If not a valid hex color.

    Example:
        >>> validate_hex_color("#ff5733")
        '#FF5733'
    """
    color = color.strip()

    if not HEX_COLOR_PATTERN.match(color):
        raise ValueError("Invalid hex color format. Use #RRGGBB format.")

    return color.upper()


# ============================================================================
# Numeric Validation
# ============================================================================


def validate_positive_decimal(value: Any) -> Any:
    """Validate decimal is positive.

    Args:
        value: Decimal value to validate.

    Returns:
        The value if positive.

    Raises:
        ValueError: If value is not positive.
    """
    from decimal import Decimal

    if isinstance(value, (int, float, Decimal)):
        if value <= 0:
            raise ValueError("Value must be positive")
    return value


def validate_non_negative_decimal(value: Any) -> Any:
    """Validate decimal is non-negative (>= 0).

    Args:
        value: Decimal value to validate.

    Returns:
        The value if non-negative.

    Raises:
        ValueError: If value is negative.
    """
    from decimal import Decimal

    if isinstance(value, (int, float, Decimal)):
        if value < 0:
            raise ValueError("Value cannot be negative")
    return value


# ============================================================================
# Pydantic Annotated Types
# ============================================================================

# Secure password with strength validation
SecurePassword = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(validate_password_strength),
]

# Sanitized string for general text
SanitizedString = Annotated[
    str,
    BeforeValidator(lambda v: sanitize_string(v) if isinstance(v, str) else v),
]

# Sanitized name (more restrictive)
SanitizedName = Annotated[
    str,
    AfterValidator(sanitize_name),
]

# Safe text (notes, descriptions)
SafeText = Annotated[
    str,
    BeforeValidator(lambda v: sanitize_string(v) if isinstance(v, str) else v),
    AfterValidator(validate_safe_text),
]

# Safe URL
SafeUrl = Annotated[
    str | None,
    AfterValidator(validate_safe_url),
]

# Validated currency
ValidCurrency = Annotated[
    str,
    AfterValidator(validate_currency),
]

# Validated UUID
ValidUUID = Annotated[
    str | None,
    AfterValidator(validate_uuid),
]

# Validated hex color
ValidHexColor = Annotated[
    str,
    AfterValidator(validate_hex_color),
]


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Validation functions
    "validate_password_strength",
    "sanitize_string",
    "sanitize_name",
    "validate_safe_text",
    "validate_safe_url",
    "validate_currency",
    "validate_uuid",
    "validate_hex_color",
    "validate_positive_decimal",
    "validate_non_negative_decimal",
    # Constants
    "ALLOWED_CURRENCIES",
    "COMMON_PASSWORDS",
    "DANGEROUS_SCHEMES",
    # Annotated types
    "SecurePassword",
    "SanitizedString",
    "SanitizedName",
    "SafeText",
    "SafeUrl",
    "ValidCurrency",
    "ValidUUID",
    "ValidHexColor",
]
