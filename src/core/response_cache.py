"""Response caching utilities for API endpoints.

Sprint 2.4.4 - Caching Strategy Implementation

Provides decorators and utilities for caching API responses using Redis.
Supports per-user caching with automatic invalidation on mutations.

Key Features:
- User-scoped caching (different users get different cached data)
- Automatic cache invalidation on mutations
- Configurable TTL per endpoint type
- Graceful degradation if Redis unavailable

Cache Key Patterns:
- response:{user_id}:{endpoint}:{hash} - Response cache
- invalidate:{user_id}:{resource} - Invalidation triggers

Example:
    >>> @router.get("/subscriptions")
    >>> @cache_response(ttl=300, resource="subscriptions")
    >>> async def list_subscriptions(...):
    ...     return subscriptions
"""

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Type variables for generic decorator
P = ParamSpec("P")
R = TypeVar("R")

# Cache TTLs by endpoint type (in seconds)
CACHE_TTL_LIST = 60  # 1 minute for list endpoints
CACHE_TTL_SUMMARY = 300  # 5 minutes for summary endpoints
CACHE_TTL_UPCOMING = 120  # 2 minutes for upcoming payments


def _generate_cache_key(
    user_id: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> str:
    """Generate a unique cache key for a response.

    Args:
        user_id: User ID for scoped caching.
        endpoint: Endpoint identifier (e.g., "subscriptions:list").
        params: Query parameters to include in key.

    Returns:
        Cache key string.

    Example:
        >>> _generate_cache_key("user-123", "subscriptions:list", {"is_active": True})
        'response:user-123:subscriptions:list:a1b2c3d4'
    """
    # Create hash of parameters for uniqueness
    params_str = json.dumps(params or {}, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

    return f"response:{user_id}:{endpoint}:{params_hash}"


class ResponseCache:
    """Response cache manager using Redis.

    Provides methods for caching API responses with user-scoped keys
    and automatic invalidation.

    Attributes:
        cache: CacheService instance.

    Example:
        >>> cache = ResponseCache()
        >>> await cache.get_or_set("user-123", "subscriptions:list", fetch_func)
    """

    def __init__(self, cache_service: CacheService | None = None):
        """Initialize ResponseCache.

        Args:
            cache_service: Optional CacheService instance. If not provided,
                          creates a new singleton instance.
        """
        self._cache = cache_service

    @property
    def cache(self) -> CacheService:
        """Get or create cache service instance."""
        if self._cache is None:
            self._cache = CacheService()
        return self._cache

    async def get(
        self,
        user_id: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any | None:
        """Get cached response if available.

        Args:
            user_id: User ID for scoped lookup.
            endpoint: Endpoint identifier.
            params: Query parameters.

        Returns:
            Cached data or None if not found.
        """
        key = _generate_cache_key(user_id, endpoint, params)
        return await self.cache.get(key)

    async def set(
        self,
        user_id: str,
        endpoint: str,
        data: Any,
        params: dict[str, Any] | None = None,
        ttl: int = CACHE_TTL_LIST,
    ) -> bool:
        """Cache a response.

        Args:
            user_id: User ID for scoped caching.
            endpoint: Endpoint identifier.
            data: Data to cache (must be JSON serializable).
            params: Query parameters.
            ttl: Time-to-live in seconds.

        Returns:
            True if cached successfully.
        """
        key = _generate_cache_key(user_id, endpoint, params)
        return await self.cache.set(key, data, ttl=ttl)

    async def invalidate_user_cache(
        self,
        user_id: str,
        resource: str | None = None,
    ) -> int:
        """Invalidate all cached responses for a user.

        Args:
            user_id: User ID whose cache to invalidate.
            resource: Optional resource type to invalidate (e.g., "subscriptions").
                     If not provided, invalidates all user cache.

        Returns:
            Number of keys deleted.
        """
        if resource:
            pattern = f"response:{user_id}:{resource}:*"
        else:
            pattern = f"response:{user_id}:*"

        return await self.cache.clear_pattern(pattern)

    async def get_or_set(
        self,
        user_id: str,
        endpoint: str,
        fetch_func: Callable[[], Awaitable[Any]],
        params: dict[str, Any] | None = None,
        ttl: int = CACHE_TTL_LIST,
    ) -> tuple[Any, bool]:
        """Get cached response or fetch and cache.

        Implements cache-aside pattern: returns cached data if available,
        otherwise calls fetch_func, caches result, and returns.

        Args:
            user_id: User ID for scoped caching.
            endpoint: Endpoint identifier.
            fetch_func: Async function to fetch data if cache miss.
            params: Query parameters.
            ttl: Time-to-live in seconds.

        Returns:
            Tuple of (data, from_cache) where from_cache is True if
            data was served from cache.

        Example:
            >>> data, from_cache = await cache.get_or_set(
            ...     "user-123",
            ...     "subscriptions:list",
            ...     lambda: service.get_all()
            ... )
        """
        # Try cache first
        cached = await self.get(user_id, endpoint, params)
        if cached is not None:
            logger.debug(f"Cache hit for {endpoint}")
            return cached, True

        # Cache miss - fetch data
        logger.debug(f"Cache miss for {endpoint}")
        data = await fetch_func()

        # Cache the result
        await self.set(user_id, endpoint, data, params, ttl)

        return data, False


# Global response cache instance
_response_cache: ResponseCache | None = None


def get_response_cache() -> ResponseCache:
    """Get or create global ResponseCache instance.

    Returns:
        ResponseCache singleton instance.
    """
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache


async def invalidate_subscription_cache(user_id: str) -> int:
    """Invalidate all subscription-related caches for a user.

    Call this after any mutation (create, update, delete) to
    ensure cached data stays fresh.

    Args:
        user_id: User ID whose cache to invalidate.

    Returns:
        Number of cache keys deleted.
    """
    cache = get_response_cache()
    count = 0

    # Invalidate subscription list cache
    count += await cache.invalidate_user_cache(user_id, "subscriptions")

    # Invalidate summary cache
    count += await cache.invalidate_user_cache(user_id, "summary")

    # Invalidate upcoming cache
    count += await cache.invalidate_user_cache(user_id, "upcoming")

    logger.debug(f"Invalidated {count} cache keys for user {user_id}")
    return count


def cache_response(
    endpoint: str,
    ttl: int = CACHE_TTL_LIST,
    include_params: list[str] | None = None,
):
    """Decorator for caching endpoint responses.

    Usage:
        @router.get("/subscriptions")
        @cache_response("subscriptions:list", ttl=60, include_params=["is_active", "category"])
        async def list_subscriptions(
            current_user: User = Depends(get_current_active_user),
            is_active: bool | None = None,
            ...
        ):
            ...

    Args:
        endpoint: Endpoint identifier for cache key.
        ttl: Cache TTL in seconds.
        include_params: List of parameter names to include in cache key.

    Note:
        The decorated function MUST have a `current_user` parameter
        (either as argument or from dependency injection) for user-scoped caching.
    """
    include_params = include_params or []

    def decorator(
        func: Callable[P, Awaitable[R]],
    ) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Get user ID from kwargs (from dependency injection)
            current_user = kwargs.get("current_user")
            if current_user is None:
                # No user context, skip caching
                return await func(*args, **kwargs)

            user_id = str(current_user.id)

            # Build params dict from included parameters
            params = {k: kwargs.get(k) for k in include_params if k in kwargs}

            cache = get_response_cache()

            # Check cache
            cached = await cache.get(user_id, endpoint, params)
            if cached is not None:
                logger.debug(f"Cache hit: {endpoint}")
                return cached

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Convert to JSON-serializable format if needed
            if hasattr(result, "__iter__") and not isinstance(result, (str, dict)):
                # List of Pydantic models
                try:
                    cache_data = [
                        item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                        for item in result
                    ]
                except Exception:
                    cache_data = result
            elif hasattr(result, "model_dump"):
                # Single Pydantic model
                cache_data = result.model_dump(mode="json")
            else:
                cache_data = result

            # Store in cache
            await cache.set(user_id, endpoint, cache_data, params, ttl)

            return result

        return wrapper

    return decorator
