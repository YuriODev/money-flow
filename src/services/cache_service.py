"""Redis cache service for RAG and general caching.

This module provides a Redis client wrapper for caching embeddings,
search results, and other frequently accessed data.

Features:
- Async Redis operations with connection pooling
- Structured key patterns for different data types
- TTL-based expiration for all cached data
- Graceful degradation if Redis is unavailable
"""

import json
import logging
from typing import Any, ClassVar

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from src.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based cache service for RAG operations.

    Provides async caching with automatic serialization/deserialization
    for embeddings, search results, and conversation context.

    Key Patterns:
        - emb:{model}:{hash} - Embedding vectors (TTL: 1 hour)
        - ctx:{user_id}:{session_id} - Conversation context (TTL: 30 min)
        - search:{type}:{hash} - Search results (TTL: 5 min)
        - analytics:{date} - Daily analytics (TTL: 24 hours)

    Attributes:
        redis: Async Redis client instance.
        pool: Redis connection pool.

    Example:
        >>> cache = await get_cache_service()
        >>> await cache.set("key", {"data": "value"}, ttl=3600)
        >>> data = await cache.get("key")
        >>> {"data": "value"}
    """

    _instance: ClassVar["CacheService | None"] = None
    _pool: ClassVar[ConnectionPool | None] = None

    def __new__(cls) -> "CacheService":
        """Create or return the singleton instance.

        Returns:
            The singleton CacheService instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the cache service.

        Creates a connection pool on first initialization.
        Subsequent calls return the existing instance.
        """
        if getattr(self, "_initialized", False):
            return

        self._redis: redis.Redis | None = None
        self._initialized = True
        logger.info(f"CacheService initialized with URL: {settings.redis_url}")

    async def connect(self) -> None:
        """Establish connection to Redis.

        Creates a connection pool and Redis client.
        Safe to call multiple times.

        Raises:
            ConnectionError: If Redis is unreachable after retries.
        """
        if self._redis is not None:
            return

        try:
            if CacheService._pool is None:
                CacheService._pool = ConnectionPool.from_url(
                    settings.redis_url,
                    max_connections=10,
                    decode_responses=True,
                )

            self._redis = redis.Redis(connection_pool=CacheService._pool)
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            raise ConnectionError(f"Redis connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close Redis connection.

        Cleans up the connection pool. Safe to call multiple times.
        """
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            logger.info("Redis connection closed")

        if CacheService._pool is not None:
            await CacheService._pool.disconnect()
            CacheService._pool = None

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.

        Example:
            >>> value = await cache.get("emb:model:abc123")
        """
        if self._redis is None:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache (must be JSON serializable).
            ttl: Time-to-live in seconds (default: from settings).

        Returns:
            True if successful, False otherwise.

        Example:
            >>> await cache.set("emb:model:abc", [0.1, 0.2, 0.3], ttl=3600)
        """
        if self._redis is None:
            return False

        try:
            serialized = json.dumps(value)
            if ttl is None:
                ttl = settings.rag_cache_ttl

            await self._redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key was deleted, False otherwise.
        """
        if self._redis is None:
            return False

        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key to check.

        Returns:
            True if key exists, False otherwise.
        """
        if self._redis is None:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats including memory usage,
            hit/miss counts, and connection info.

        Example:
            >>> stats = await cache.get_stats()
            >>> stats['used_memory']
            '1.5MB'
        """
        if self._redis is None:
            return {"status": "disconnected"}

        try:
            info = await self._redis.info("memory")
            stats = await self._redis.info("stats")
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "unknown"),
                "used_memory_peak": info.get("used_memory_peak_human", "unknown"),
                "keyspace_hits": stats.get("keyspace_hits", 0),
                "keyspace_misses": stats.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    stats.get("keyspace_hits", 0),
                    stats.get("keyspace_misses", 0),
                ),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage.

        Args:
            hits: Number of cache hits.
            misses: Number of cache misses.

        Returns:
            Hit rate as percentage (0-100).
        """
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "emb:*", "ctx:user1:*").

        Returns:
            Number of keys deleted.

        Warning:
            Use with caution in production. SCAN is used to avoid
            blocking but can still be slow for many keys.
        """
        if self._redis is None:
            return 0

        try:
            deleted = 0
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                if keys:
                    deleted += await self._redis.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            logger.warning(f"Cache clear pattern failed for {pattern}: {e}")
            return 0

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance.

        Primarily for testing purposes.
        """
        cls._instance = None
        cls._pool = None
        logger.info("CacheService reset")


# Singleton instance holder
_cache_service: CacheService | None = None


async def get_cache_service() -> CacheService:
    """Get the singleton CacheService instance.

    Creates and connects the service on first call.

    Returns:
        Connected CacheService instance.

    Example:
        >>> cache = await get_cache_service()
        >>> await cache.set("key", "value")
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService()
        try:
            await _cache_service.connect()
        except ConnectionError:
            logger.warning("Redis not available, caching disabled")

    return _cache_service


async def close_cache_service() -> None:
    """Close the cache service connection.

    Should be called during application shutdown.
    """
    global _cache_service

    if _cache_service is not None:
        await _cache_service.disconnect()
        _cache_service = None
