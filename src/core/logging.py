"""Structured logging configuration using structlog.

This module provides centralized logging configuration with:
- JSON formatting for production (machine-parseable)
- Human-readable console output for development
- Request ID and user ID context injection
- Sensitive data redaction
- Environment-aware log levels

Usage:
    from src.core.logging import get_logger, configure_logging

    # At application startup
    configure_logging()

    # In your modules
    logger = get_logger(__name__)
    logger.info("Processing request", user_id="123", action="create")
"""

from __future__ import annotations

import logging
import re
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.core.config import settings

# Context variables for request tracking
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)

# Patterns for sensitive data that should be redacted
SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # API keys and tokens
    (
        re.compile(
            r"(api[_-]?key|token|secret|password|auth)([\"']?\s*[:=]\s*[\"']?)([^\s\"',}]+)", re.I
        ),
        r"\1\2[REDACTED]",
    ),
    # JWT tokens
    (re.compile(r"(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"), "[JWT_REDACTED]"),
    # Email addresses (partial redaction)
    (re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"), r"***@\2"),
    # Credit card numbers
    (re.compile(r"\b(\d{4})[- ]?(\d{4})[- ]?(\d{4})[- ]?(\d{4})\b"), r"\1-****-****-\4"),
    # Bearer tokens
    (re.compile(r"(Bearer\s+)([A-Za-z0-9_-]+)", re.I), r"\1[REDACTED]"),
]


def redact_sensitive_data(value: Any) -> Any:
    """Redact sensitive information from log values.

    Args:
        value: The value to potentially redact.

    Returns:
        The value with sensitive data redacted.
    """
    if not isinstance(value, str):
        return value

    result = value
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_event_dict(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Processor that redacts sensitive data from all event dict values.

    Args:
        logger: The logger instance.
        method_name: The logging method name.
        event_dict: The event dictionary to process.

    Returns:
        Event dictionary with sensitive data redacted.
    """
    return {key: redact_sensitive_data(value) for key, value in event_dict.items()}


def add_request_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add request context (request_id, user_id) to log events.

    Args:
        logger: The logger instance.
        method_name: The logging method name.
        event_dict: The event dictionary to process.

    Returns:
        Event dictionary with request context added.
    """
    request_id = request_id_ctx.get()
    user_id = user_id_ctx.get()

    if request_id and "request_id" not in event_dict:
        event_dict["request_id"] = request_id
    if user_id and "user_id" not in event_dict:
        event_dict["user_id"] = user_id

    return event_dict


def add_service_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add service-level context to log events.

    Args:
        logger: The logger instance.
        method_name: The logging method name.
        event_dict: The event dictionary to process.

    Returns:
        Event dictionary with service context added.
    """
    event_dict["service"] = "money-flow"
    event_dict["environment"] = "development" if settings.debug else "production"
    return event_dict


def get_log_level() -> int:
    """Get the appropriate log level based on environment.

    Returns:
        Logging level constant.
    """
    if settings.debug:
        return logging.DEBUG
    return logging.INFO


def get_processors(json_format: bool = False) -> list[Processor]:
    """Get the list of structlog processors.

    Args:
        json_format: Whether to output JSON format (for production).

    Returns:
        List of processors to apply to log events.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_service_context,
        add_request_context,
        redact_event_dict,
    ]

    if json_format:
        # Production: JSON output
        shared_processors.append(structlog.processors.format_exc_info)
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Console-friendly output
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

    return shared_processors


def configure_logging(json_format: bool | None = None) -> None:
    """Configure structured logging for the application.

    Should be called once at application startup.

    Args:
        json_format: Force JSON format (True) or console format (False).
                    If None, uses JSON in production, console in debug.

    Example:
        >>> configure_logging()  # Auto-detect based on DEBUG setting
        >>> configure_logging(json_format=True)  # Force JSON output
    """
    if json_format is None:
        json_format = not settings.debug

    log_level = get_log_level()
    processors = get_processors(json_format=json_format)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Set log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured structlog BoundLogger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id="123")
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, user_id: str | None = None) -> None:
    """Bind request context for the current async context.

    Call this at the start of request processing to ensure all logs
    within the request include the request_id and user_id.

    Args:
        request_id: Unique identifier for the request.
        user_id: Optional user ID for authenticated requests.

    Example:
        >>> bind_request_context("req-123", user_id="user-456")
        >>> logger.info("Processing")  # Will include request_id and user_id
    """
    request_id_ctx.set(request_id)
    if user_id:
        user_id_ctx.set(user_id)


def clear_request_context() -> None:
    """Clear request context at the end of request processing.

    Call this in request middleware cleanup to prevent context leaking.
    """
    request_id_ctx.set(None)
    user_id_ctx.set(None)


__all__ = [
    "bind_request_context",
    "clear_request_context",
    "configure_logging",
    "get_logger",
    "request_id_ctx",
    "user_id_ctx",
]
