"""Tests for CacheService.

Tests cover:
- Cache connection and disconnection
- Get, set, delete operations
- Cache statistics
- Pattern-based clearing
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.cache_service import CacheService, get_cache_service


class TestCacheServiceInit:
    """Tests for CacheService initialization."""

    def test_singleton_pattern(self):
        """Test that CacheService follows singleton pattern."""
        CacheService.reset()
        service1 = CacheService()
        service2 = CacheService()

        assert service1 is service2

    def test_reset_clears_instance(self):
        """Test that reset clears the singleton instance."""
        CacheService()  # Create initial instance
        CacheService.reset()
        service2 = CacheService()

        # New instance should be different internal state
        assert service2._initialized


class TestCacheServiceOperations:
    """Tests for cache operations."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value='{"key": "value"}')
        redis.setex = AsyncMock()
        redis.delete = AsyncMock(return_value=1)
        redis.exists = AsyncMock(return_value=1)
        redis.info = AsyncMock(
            return_value={
                "used_memory_human": "1.5MB",
                "used_memory_peak_human": "2MB",
                "keyspace_hits": 100,
                "keyspace_misses": 20,
            }
        )
        redis.scan = AsyncMock(return_value=(0, ["key1", "key2"]))
        redis.ping = AsyncMock()
        return redis

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create a cache service with mock Redis."""
        CacheService.reset()
        service = CacheService()
        service._redis = mock_redis
        return service

    @pytest.mark.asyncio
    async def test_get_returns_deserialized_value(self, cache_service, mock_redis):
        """Test that get returns deserialized JSON value."""
        result = await cache_service.get("test_key")

        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self, cache_service, mock_redis):
        """Test that get returns None for missing key."""
        mock_redis.get.return_value = None

        result = await cache_service.get("missing_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_disconnected(self):
        """Test that get returns None when Redis is disconnected."""
        CacheService.reset()
        service = CacheService()
        service._redis = None

        result = await service.get("any_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_stores_serialized_value(self, cache_service, mock_redis):
        """Test that set stores JSON serialized value."""
        result = await cache_service.set("key", {"data": "value"}, ttl=3600)

        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_returns_false_when_disconnected(self):
        """Test that set returns False when Redis is disconnected."""
        CacheService.reset()
        service = CacheService()
        service._redis = None

        result = await service.set("key", "value")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Test that delete removes a key."""
        result = await cache_service.delete("key")

        assert result is True
        mock_redis.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_exists_checks_key(self, cache_service, mock_redis):
        """Test that exists checks for key existence."""
        result = await cache_service.exists("key")

        assert result is True
        mock_redis.exists.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_get_stats_returns_metrics(self, cache_service, mock_redis):
        """Test that get_stats returns cache metrics."""
        result = await cache_service.get_stats()

        assert result["status"] == "connected"
        assert result["used_memory"] == "1.5MB"
        assert result["hit_rate"] == 83.33  # 100/(100+20)*100


class TestCacheServiceHitRate:
    """Tests for hit rate calculation."""

    def test_hit_rate_with_no_requests(self):
        """Test hit rate calculation with no requests."""
        CacheService.reset()
        service = CacheService()

        rate = service._calculate_hit_rate(0, 0)

        assert rate == 0.0

    def test_hit_rate_with_only_hits(self):
        """Test hit rate calculation with only hits."""
        CacheService.reset()
        service = CacheService()

        rate = service._calculate_hit_rate(100, 0)

        assert rate == 100.0

    def test_hit_rate_with_mixed(self):
        """Test hit rate calculation with mixed hits and misses."""
        CacheService.reset()
        service = CacheService()

        rate = service._calculate_hit_rate(80, 20)

        assert rate == 80.0


class TestCacheServicePatternClear:
    """Tests for pattern-based cache clearing."""

    @pytest.mark.asyncio
    async def test_clear_pattern_deletes_matching_keys(self):
        """Test that clear_pattern deletes matching keys."""
        CacheService.reset()
        service = CacheService()

        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(return_value=(0, ["emb:1", "emb:2"]))
        mock_redis.delete = AsyncMock(return_value=2)
        service._redis = mock_redis

        deleted = await service.clear_pattern("emb:*")

        assert deleted == 2
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_pattern_returns_zero_when_disconnected(self):
        """Test that clear_pattern returns 0 when disconnected."""
        CacheService.reset()
        service = CacheService()
        service._redis = None

        deleted = await service.clear_pattern("*")

        assert deleted == 0


class TestGetCacheService:
    """Tests for the factory function."""

    @pytest.mark.asyncio
    async def test_get_cache_service_returns_instance(self):
        """Test that get_cache_service returns a CacheService instance."""
        CacheService.reset()

        with patch("src.services.cache_service._cache_service", None):
            with patch.object(CacheService, "connect", new_callable=AsyncMock):
                service = await get_cache_service()

                assert isinstance(service, CacheService)
