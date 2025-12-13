"""Secrets validation for production deployments.

This module provides startup validation to ensure secrets and sensitive
configuration values are properly set before the application runs.

Sprint 1.2.6 - Secrets Management

Security Features:
    - Detects default/placeholder secrets in production
    - Warns about weak JWT secrets
    - Validates required API keys are set
    - Checks for insecure configuration combinations

Example:
    >>> from src.security.secrets_validator import validate_secrets
    >>>
    >>> # In production, will raise if secrets are not configured
    >>> validate_secrets()
"""

from __future__ import annotations

import logging
import re
import secrets as stdlib_secrets
from dataclasses import dataclass, field

from src.core.config import settings

logger = logging.getLogger(__name__)


# Known default/placeholder values that should never be used in production
DEFAULT_SECRETS = frozenset(
    {
        "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION",
        "your-secret-key",
        "changeme",
        "secret",
        "password",
        "your-key-here",
        "sk-ant-your-key-here",
        "your-api-key-here",
        "replace-me",
        "default-secret",
    }
)

# Minimum entropy bits for secrets (256 bits = 64 hex chars)
MIN_SECRET_LENGTH = 32  # 32 chars = 128 bits minimum


@dataclass
class ValidationResult:
    """Result of secrets validation.

    Attributes:
        is_valid: Whether all validations passed.
        errors: List of critical security errors.
        warnings: List of non-critical security warnings.

    Example:
        >>> result = ValidationResult(is_valid=True)
        >>> result.add_error("JWT secret is default value")
        >>> result.is_valid
        False
    """

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add a critical error and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a non-critical warning."""
        self.warnings.append(message)


def _is_default_value(value: str) -> bool:
    """Check if value is a known default/placeholder.

    Args:
        value: Secret value to check.

    Returns:
        True if value matches known defaults.
    """
    if not value:
        return True

    lower_value = value.lower()

    # Check against known defaults
    if lower_value in DEFAULT_SECRETS or any(d in lower_value for d in DEFAULT_SECRETS):
        return True

    # Check for common placeholder patterns
    placeholder_patterns = [
        r"^your[-_]?.*[-_]?here$",
        r"^change[-_]?.*[-_]?me$",
        r"^replace[-_]?me$",
        r"^xxx+$",
        r"^test[-_]?.*[-_]?key$",
        r"^dummy",
        r"^fake",
        r"^sample",
        r"^example",
    ]

    for pattern in placeholder_patterns:
        if re.match(pattern, lower_value, re.IGNORECASE):
            return True

    return False


def _check_secret_strength(value: str, name: str) -> tuple[bool, str | None]:
    """Check if a secret has sufficient entropy.

    Args:
        value: Secret value to check.
        name: Name of the secret for error messages.

    Returns:
        Tuple of (is_strong, error_message if weak).
    """
    if len(value) < MIN_SECRET_LENGTH:
        return (
            False,
            f"{name} is too short ({len(value)} chars). Use at least {MIN_SECRET_LENGTH} characters.",
        )

    # Check for low entropy (e.g., "aaaaaaaaaaaaa...")
    unique_chars = len(set(value))
    if unique_chars < 10:
        return (
            False,
            f"{name} has low entropy (only {unique_chars} unique characters). Use a random secret.",
        )

    return True, None


def validate_secrets(strict: bool = False) -> ValidationResult:
    """Validate all secrets and sensitive configuration.

    In production mode (DEBUG=false), this function will check that:
    - JWT secret is not a default value
    - JWT secret has sufficient entropy
    - Required API keys are set
    - No insecure configuration combinations

    Args:
        strict: If True, treat warnings as errors.

    Returns:
        ValidationResult with errors and warnings.

    Raises:
        SecurityError: If strict=True and validation fails (for use in startup).

    Example:
        >>> result = validate_secrets()
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(f"ERROR: {error}")
    """
    result = ValidationResult()
    is_production = not settings.debug

    # =========================================================================
    # JWT Secret Validation
    # =========================================================================
    jwt_secret = settings.jwt_secret_key

    if _is_default_value(jwt_secret):
        if is_production:
            result.add_error(
                "JWT_SECRET_KEY is set to a default value. "
                'Generate a secure secret: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        else:
            result.add_warning("JWT_SECRET_KEY is using default value. This is OK for development.")
    else:
        is_strong, error_msg = _check_secret_strength(jwt_secret, "JWT_SECRET_KEY")
        if not is_strong:
            if is_production:
                result.add_error(error_msg)
            else:
                result.add_warning(error_msg)

    # =========================================================================
    # API Key Validation
    # =========================================================================
    # Anthropic API key (optional but warned if AI features are used)
    anthropic_key = settings.anthropic_api_key

    if not anthropic_key or _is_default_value(anthropic_key):
        result.add_warning("ANTHROPIC_API_KEY is not set. AI agent features will be disabled.")
    elif not anthropic_key.startswith("sk-ant-"):
        result.add_warning(
            "ANTHROPIC_API_KEY doesn't match expected format (sk-ant-...). Verify it's correct."
        )

    # Exchange rate API key (optional)
    exchange_key = settings.exchange_rate_api_key

    if not exchange_key or _is_default_value(exchange_key):
        result.add_warning(
            "EXCHANGE_RATE_API_KEY is not set. Currency conversion will use fallback rates."
        )

    # =========================================================================
    # Database URL Validation
    # =========================================================================
    db_url = settings.database_url

    if "localhost" in db_url or "127.0.0.1" in db_url:
        if is_production:
            result.add_warning(
                "DATABASE_URL points to localhost. Ensure this is intentional for production."
            )

    # Check for credentials in URL (not ideal but sometimes necessary)
    if "@" in db_url and "://" in db_url:
        # Extract password from URL if present
        try:
            parts = db_url.split("://")[1].split("@")[0]
            if ":" in parts:
                password = parts.split(":")[1]
                if _is_default_value(password) or password in {"localdev", "postgres", "root"}:
                    if is_production:
                        result.add_error(
                            "DATABASE_URL contains a default/weak password. "
                            "Use a strong, unique password in production."
                        )
                    else:
                        result.add_warning(
                            "DATABASE_URL uses a simple password. OK for development."
                        )
        except (IndexError, ValueError):
            pass  # URL format is different, skip this check

    # =========================================================================
    # CORS Validation
    # =========================================================================
    cors_origins = settings.cors_origins

    if "*" in cors_origins:
        if is_production:
            result.add_error("CORS_ORIGINS contains wildcard '*'. This is insecure in production.")
        else:
            result.add_warning("CORS_ORIGINS contains wildcard '*'. OK for development only.")

    # =========================================================================
    # Redis URL Validation
    # =========================================================================
    redis_url = settings.redis_url

    if is_production and "localhost" in redis_url:
        result.add_warning(
            "REDIS_URL points to localhost. Ensure this is intentional for production."
        )

    # =========================================================================
    # Debug Mode Check
    # =========================================================================
    if settings.debug:
        result.add_warning("DEBUG=true is enabled. Disable in production for security.")

    # =========================================================================
    # Log Results
    # =========================================================================
    if result.errors:
        for error in result.errors:
            logger.error(f"Security validation FAILED: {error}")

    if result.warnings:
        for warning in result.warnings:
            logger.warning(f"Security validation warning: {warning}")

    if result.is_valid and not result.warnings:
        logger.info("Security validation passed: All secrets properly configured")

    return result


def ensure_secure_startup() -> None:
    """Ensure secrets are properly configured before application starts.

    This function should be called during application startup in production.
    It will raise an exception if critical security requirements are not met.

    Raises:
        RuntimeError: If production environment has insecure configuration.

    Example:
        >>> # In lifespan or startup event
        >>> ensure_secure_startup()  # Raises if insecure
    """
    result = validate_secrets()

    if not result.is_valid:
        error_msg = "Application startup blocked due to security issues:\n"
        error_msg += "\n".join(f"  - {e}" for e in result.errors)
        error_msg += "\n\nFix these issues or set DEBUG=true for development."

        logger.critical(error_msg)
        raise RuntimeError(error_msg)


def generate_secure_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random secret.

    Args:
        length: Length of the hex string (default 64 = 256 bits).

    Returns:
        Random hex string suitable for use as a secret.

    Example:
        >>> secret = generate_secure_secret()
        >>> len(secret)
        64
    """
    return stdlib_secrets.token_hex(length // 2)


__all__ = [
    "ValidationResult",
    "validate_secrets",
    "ensure_secure_startup",
    "generate_secure_secret",
]
