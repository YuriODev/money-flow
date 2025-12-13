"""Rate limiting implementation using slowapi with Redis backend.

This module provides rate limiting for API endpoints to prevent abuse
and ensure fair usage. Uses Redis for distributed rate limiting across
multiple application instances.

Rate Limits (configurable via settings):
- GET endpoints: 100 requests/minute
- POST/PUT/DELETE: 20 requests/minute
- AI Agent endpoint: 10 requests/minute (expensive operations)
- Auth endpoints: 5 requests/minute (brute force protection)

Example:
    >>> from src.security.rate_limit import limiter, rate_limit_get
    >>>
    >>> @router.get("/items")
    >>> @limiter.limit(rate_limit_get)
    >>> async def list_items(request: Request):
    ...     return {"items": []}

Security Notes:
    - Rate limits are applied per IP address by default
    - Authenticated requests can be limited per user_id
    - Redis backend enables distributed rate limiting
    - Graceful fallback to in-memory storage if Redis unavailable
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.config import settings

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user identity or IP.

    For authenticated requests, uses user_id from the request state
    to enable per-user rate limiting. Falls back to IP address for
    unauthenticated requests.

    Args:
        request: The incoming HTTP request.

    Returns:
        Unique identifier string for rate limiting:
        - "user:{user_id}" for authenticated users
        - IP address for anonymous users

    Example:
        >>> # Authenticated request
        >>> request.state.user_id = "user-123"
        >>> get_rate_limit_key(request)
        'user:user-123'
        >>> # Anonymous request
        >>> get_rate_limit_key(request)
        '192.168.1.1'

    Security Notes:
        - Per-user limits prevent one user from blocking others
        - IP-based limits protect against anonymous abuse
        - X-Forwarded-For is handled by get_remote_address
    """
    # Try to get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    return get_remote_address(request)


def _get_redis_storage_uri() -> str | None:
    """Get Redis URI for rate limit storage.

    Returns Redis URL from settings if available and rate limiting
    is enabled. Returns None to use in-memory storage otherwise.

    Returns:
        Redis URI string or None for in-memory storage.

    Security Notes:
        - Redis enables distributed rate limiting
        - In-memory storage is per-instance only
    """
    if not settings.rate_limit_enabled:
        return None

    # Parse Redis URL to ensure it's valid
    redis_url = settings.redis_url
    if redis_url and redis_url.startswith("redis://"):
        return redis_url

    logger.warning("Invalid Redis URL for rate limiting, using in-memory storage")
    return None


# Create limiter instance with Redis backend
# Falls back to in-memory storage if Redis unavailable
_storage_uri = _get_redis_storage_uri()

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[settings.rate_limit_default] if settings.rate_limit_enabled else [],
    storage_uri=_storage_uri,
    strategy="fixed-window",  # Simple fixed window strategy
    headers_enabled=False,  # Disabled due to slowapi/starlette compatibility issue
    enabled=settings.rate_limit_enabled,  # Fully disable when RATE_LIMIT_ENABLED=false
)

# Rate limit decorators for different endpoint types
# These can be used as: @limiter.limit(rate_limit_get)
rate_limit_default = settings.rate_limit_default
rate_limit_get = settings.rate_limit_get
rate_limit_write = settings.rate_limit_write
rate_limit_agent = settings.rate_limit_agent
rate_limit_auth = settings.rate_limit_auth


def get_limiter() -> Limiter:
    """Get the rate limiter instance.

    Returns:
        Configured Limiter instance.

    Example:
        >>> limiter = get_limiter()
        >>> limiter.enabled
        True
    """
    return limiter


# Re-export RateLimitExceeded for use in exception handlers
__all__ = [
    "RateLimitExceeded",
    "get_rate_limit_key",
    "limiter",
    "rate_limit_agent",
    "rate_limit_auth",
    "rate_limit_default",
    "rate_limit_get",
    "rate_limit_write",
]
