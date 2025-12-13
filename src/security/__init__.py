"""Security module for Money Flow.

This module provides security features including:
- Rate limiting with Redis backend
- Input sanitization and prompt injection protection
- Enhanced Pydantic validators for input security
- Security headers middleware (XSS, clickjacking, HSTS, CSP)
- Secrets validation for production deployments

Sprint 1.2 - Security Hardening
"""

from src.security.headers import (
    DEFAULT_CSP_ENABLED,
    DEFAULT_CSP_REPORT_ONLY,
    DEFAULT_HSTS_ENABLED,
    SecurityHeadersMiddleware,
    get_security_headers_middleware,
)
from src.security.input_sanitizer import (
    InputSanitizer,
    SanitizationResult,
    get_input_sanitizer,
    sanitize_input,
)
from src.security.rate_limit import (
    RateLimitExceeded,
    get_rate_limit_key,
    limiter,
    rate_limit_agent,
    rate_limit_auth,
    rate_limit_default,
    rate_limit_get,
    rate_limit_write,
)
from src.security.secrets_validator import (
    ValidationResult,
    ensure_secure_startup,
    generate_secure_secret,
    validate_secrets,
)
from src.security.validators import (
    # Constants
    ALLOWED_CURRENCIES,
    # Annotated types
    SafeText,
    SafeUrl,
    SanitizedName,
    SanitizedString,
    SecurePassword,
    ValidCurrency,
    ValidHexColor,
    ValidUUID,
    # Validation functions
    sanitize_name,
    sanitize_string,
    validate_currency,
    validate_hex_color,
    validate_non_negative_decimal,
    validate_password_strength,
    validate_positive_decimal,
    validate_safe_text,
    validate_safe_url,
    validate_uuid,
)

__all__ = [
    # Input sanitization (prompt injection protection)
    "InputSanitizer",
    "SanitizationResult",
    "get_input_sanitizer",
    "sanitize_input",
    # Rate limiting
    "RateLimitExceeded",
    "get_rate_limit_key",
    "limiter",
    "rate_limit_agent",
    "rate_limit_auth",
    "rate_limit_default",
    "rate_limit_get",
    "rate_limit_write",
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
    # Annotated types for Pydantic
    "SecurePassword",
    "SanitizedString",
    "SanitizedName",
    "SafeText",
    "SafeUrl",
    "ValidCurrency",
    "ValidUUID",
    "ValidHexColor",
    # Constants
    "ALLOWED_CURRENCIES",
    # Security headers middleware
    "SecurityHeadersMiddleware",
    "get_security_headers_middleware",
    "DEFAULT_HSTS_ENABLED",
    "DEFAULT_CSP_ENABLED",
    "DEFAULT_CSP_REPORT_ONLY",
    # Secrets validation
    "ValidationResult",
    "validate_secrets",
    "ensure_secure_startup",
    "generate_secure_secret",
]
