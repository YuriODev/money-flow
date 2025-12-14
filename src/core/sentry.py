"""Sentry error tracking configuration.

This module provides centralized Sentry initialization with:
- Automatic FastAPI/Starlette integration
- User context attachment
- Request ID correlation
- Environment-aware configuration
- PII filtering

Usage:
    from src.core.sentry import init_sentry

    # At application startup
    init_sentry()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.config import settings
from src.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def init_sentry() -> None:
    """Initialize Sentry error tracking.

    This function should be called once at application startup,
    before any other code runs. It configures Sentry with:
    - DSN from settings
    - Environment-specific settings
    - FastAPI integration
    - Performance monitoring
    - PII scrubbing

    If SENTRY_DSN is not set, Sentry is disabled silently.

    Example:
        >>> init_sentry()
        >>> # Sentry is now active (if DSN is configured)
    """
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        # Performance monitoring
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        # Integrations
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        # Data scrubbing - remove sensitive data
        send_default_pii=False,
        # Attach stack traces to messages
        attach_stacktrace=True,
        # Include local variables in stack traces (development only)
        include_local_variables=settings.debug,
        # Custom before_send hook for additional filtering
        before_send=_filter_event,
        # Custom before_breadcrumb hook
        before_breadcrumb=_filter_breadcrumb,
    )

    logger.info(
        "Sentry initialized",
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )


def _filter_event(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Filter and modify events before sending to Sentry.

    Args:
        event: The Sentry event dictionary.
        hint: Additional information about the event.

    Returns:
        The filtered event, or None to drop the event.
    """
    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["service"] = "money-flow"

    # Filter out specific exception types that we don't want to track
    if "exception" in event:
        exc_info = hint.get("exc_info")
        if exc_info:
            exc_type = exc_info[0]
            # Don't track cancelled tasks or client disconnects
            if exc_type and exc_type.__name__ in ("CancelledError", "ClientDisconnect"):
                return None

    # Scrub sensitive data from request body
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = _scrub_sensitive_data(event["request"]["data"])

    return event


def _filter_breadcrumb(crumb: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Filter and modify breadcrumbs before adding to event.

    Args:
        crumb: The breadcrumb dictionary.
        hint: Additional information about the breadcrumb.

    Returns:
        The filtered breadcrumb, or None to drop it.
    """
    # Filter out health check breadcrumbs (noise)
    if crumb.get("category") == "httplib" and "/health" in crumb.get("data", {}).get("url", ""):
        return None

    return crumb


def _scrub_sensitive_data(data: Any) -> Any:
    """Scrub sensitive data from event data.

    Args:
        data: The data to scrub.

    Returns:
        Scrubbed data with sensitive fields redacted.
    """
    if not isinstance(data, dict):
        return data

    sensitive_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "authorization",
        "credit_card",
        "card_number",
        "cvv",
        "ssn",
    }

    scrubbed = {}
    for key, value in data.items():
        if any(s in key.lower() for s in sensitive_keys):
            scrubbed[key] = "[REDACTED]"
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_sensitive_data(value)
        else:
            scrubbed[key] = value

    return scrubbed


def set_user_context(user_id: str, email: str | None = None) -> None:
    """Set the current user context for Sentry events.

    Call this after user authentication to attach user info
    to all subsequent Sentry events in the request.

    Args:
        user_id: The unique user identifier.
        email: Optional user email address.

    Example:
        >>> set_user_context("user-123", email="user@example.com")
    """
    try:
        import sentry_sdk

        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": email,
            }
        )
    except ImportError:
        pass


def capture_exception(error: Exception, **context: Any) -> None:
    """Capture an exception and send to Sentry with additional context.

    Use this for exceptions that are handled but should still be tracked.

    Args:
        error: The exception to capture.
        **context: Additional context to attach to the event.

    Example:
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     capture_exception(e, operation="risky", user_id="123")
        ...     # Handle the error gracefully
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)
    except ImportError:
        pass


def capture_message(message: str, level: str = "info", **context: Any) -> None:
    """Capture a message and send to Sentry.

    Use this for important events that aren't exceptions.

    Args:
        message: The message to capture.
        level: Log level (debug, info, warning, error, fatal).
        **context: Additional context to attach.

    Example:
        >>> capture_message("User exceeded rate limit", level="warning", user_id="123")
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        pass


__all__ = [
    "capture_exception",
    "capture_message",
    "init_sentry",
    "set_user_context",
]
