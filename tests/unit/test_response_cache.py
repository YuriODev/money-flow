"""Tests for Response Cache utilities (Sprint 2.4.4).

Tests for API response caching functionality:
- Cache key generation
- Get/set operations
- User-scoped caching
- Cache invalidation
- Get-or-set pattern
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.response_cache import (
    ResponseCache,
    _generate_cache_key,
    get_response_cache,
    invalidate_subscription_cache,
)


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_generate_key_basic(self):
        """Test basic cache key generation."""
        key = _generate_cache_key("user-123", "subscriptions:list")
        assert key.startswith("response:user-123:subscriptions:list:")
        assert len(key) > len("response:user-123:subscriptions:list:")

    def test_generate_key_with_params(self):
        """Test cache key includes params hash."""
        key1 = _generate_cache_key("user-123", "subscriptions:list", {"is_active": True})
        key2 = _generate_cache_key("user-123", "subscriptions:list", {"is_active": False})

        # Different params should produce different keys
        assert key1 != key2

    def test_generate_key_param_order_independent(self):
        """Test cache key is same regardless of param order."""
        key1 = _generate_cache_key("user-123", "subscriptions:list", {"a": 1, "b": 2})
        key2 = _generate_cache_key("user-123", "subscriptions:list", {"b": 2, "a": 1})

        # Same params in different order should produce same key
        assert key1 == key2

    def test_generate_key_different_users(self):
        """Test different users get different cache keys."""
        key1 = _generate_cache_key("user-123", "subscriptions:list")
        key2 = _generate_cache_key("user-456", "subscriptions:list")

        assert key1 != key2
        assert "user-123" in key1
        assert "user-456" in key2

    def test_generate_key_different_endpoints(self):
        """Test different endpoints get different cache keys."""
        key1 = _generate_cache_key("user-123", "subscriptions:list")
        key2 = _generate_cache_key("user-123", "subscriptions:summary")

        assert key1 != key2


class TestResponseCache:
    """Tests for ResponseCache class."""

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.clear_pattern = AsyncMock(return_value=0)
        return mock

    @pytest.fixture
    def response_cache(self, mock_cache_service):
        """Create ResponseCache with mocked cache service."""
        return ResponseCache(cache_service=mock_cache_service)

    @pytest.mark.asyncio
    async def test_get_returns_cached_data(self, response_cache, mock_cache_service):
        """Test get returns cached data when available."""
        mock_cache_service.get = AsyncMock(return_value={"data": "cached"})

        result = await response_cache.get("user-123", "subscriptions:list")

        assert result == {"data": "cached"}
        mock_cache_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self, response_cache, mock_cache_service):
        """Test get returns None on cache miss."""
        mock_cache_service.get = AsyncMock(return_value=None)

        result = await response_cache.get("user-123", "subscriptions:list")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_caches_data(self, response_cache, mock_cache_service):
        """Test set stores data in cache."""
        data = {"subscriptions": [1, 2, 3]}

        result = await response_cache.set("user-123", "subscriptions:list", data, ttl=60)

        assert result is True
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[1]["ttl"] == 60

    @pytest.mark.asyncio
    async def test_set_with_params(self, response_cache, mock_cache_service):
        """Test set includes params in cache key."""
        await response_cache.set(
            "user-123",
            "subscriptions:list",
            {"data": []},
            params={"is_active": True},
        )

        call_args = mock_cache_service.set.call_args
        key = call_args[0][0]
        assert "user-123" in key
        assert "subscriptions:list" in key

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_all(self, response_cache, mock_cache_service):
        """Test invalidating all cache for a user."""
        mock_cache_service.clear_pattern = AsyncMock(return_value=5)

        count = await response_cache.invalidate_user_cache("user-123")

        assert count == 5
        mock_cache_service.clear_pattern.assert_called_once_with("response:user-123:*")

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_resource(self, response_cache, mock_cache_service):
        """Test invalidating specific resource cache for a user."""
        mock_cache_service.clear_pattern = AsyncMock(return_value=3)

        count = await response_cache.invalidate_user_cache("user-123", resource="subscriptions")

        assert count == 3
        mock_cache_service.clear_pattern.assert_called_once_with(
            "response:user-123:subscriptions:*"
        )


class TestGetOrSet:
    """Tests for get_or_set pattern."""

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def response_cache(self, mock_cache_service):
        """Create ResponseCache with mocked cache service."""
        return ResponseCache(cache_service=mock_cache_service)

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, response_cache, mock_cache_service):
        """Test get_or_set returns cached data without calling fetch."""
        cached_data = {"subscriptions": [1, 2, 3]}
        mock_cache_service.get = AsyncMock(return_value=cached_data)

        fetch_func = AsyncMock(return_value={"fresh": "data"})

        data, from_cache = await response_cache.get_or_set(
            "user-123", "subscriptions:list", fetch_func
        )

        assert data == cached_data
        assert from_cache is True
        fetch_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, response_cache, mock_cache_service):
        """Test get_or_set fetches and caches on miss."""
        mock_cache_service.get = AsyncMock(return_value=None)
        fresh_data = {"subscriptions": [4, 5, 6]}
        fetch_func = AsyncMock(return_value=fresh_data)

        data, from_cache = await response_cache.get_or_set(
            "user-123", "subscriptions:list", fetch_func
        )

        assert data == fresh_data
        assert from_cache is False
        fetch_func.assert_called_once()
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_with_params(self, response_cache, mock_cache_service):
        """Test get_or_set with query parameters."""
        mock_cache_service.get = AsyncMock(return_value=None)
        fetch_func = AsyncMock(return_value=[])

        await response_cache.get_or_set(
            "user-123",
            "subscriptions:list",
            fetch_func,
            params={"is_active": True},
            ttl=120,
        )

        # Verify params are passed to get
        get_call = mock_cache_service.get.call_args
        key = get_call[0][0]
        assert "user-123" in key

        # Verify TTL is passed to set
        set_call = mock_cache_service.set.call_args
        assert set_call[1]["ttl"] == 120


class TestInvalidateSubscriptionCache:
    """Tests for subscription cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidates_all_subscription_caches(self, monkeypatch):
        """Test that all subscription-related caches are invalidated."""
        mock_cache_service = MagicMock()
        mock_cache_service.clear_pattern = AsyncMock(return_value=2)

        # Create ResponseCache with mocked service
        response_cache = ResponseCache(cache_service=mock_cache_service)

        # Patch the global cache
        monkeypatch.setattr("src.core.response_cache._response_cache", response_cache)

        await invalidate_subscription_cache("user-123")

        # Should invalidate subscriptions, summary, and upcoming (3 calls)
        assert mock_cache_service.clear_pattern.call_count == 3
        calls = mock_cache_service.clear_pattern.call_args_list
        patterns = [call[0][0] for call in calls]
        assert any("subscriptions" in p for p in patterns)
        assert any("summary" in p for p in patterns)
        assert any("upcoming" in p for p in patterns)


class TestGetResponseCache:
    """Tests for get_response_cache singleton."""

    def test_returns_singleton(self):
        """Test that get_response_cache returns same instance."""
        # Reset singleton
        import src.core.response_cache as module

        module._response_cache = None

        cache1 = get_response_cache()
        cache2 = get_response_cache()

        assert cache1 is cache2


class TestCacheTTLConstants:
    """Tests for TTL constants."""

    def test_ttl_values_reasonable(self):
        """Test TTL values are within reasonable bounds."""
        from src.core.response_cache import (
            CACHE_TTL_LIST,
            CACHE_TTL_SUMMARY,
            CACHE_TTL_UPCOMING,
        )

        # List should be short (stale data is noticeable)
        assert 30 <= CACHE_TTL_LIST <= 300

        # Summary can be longer (calculated data)
        assert 60 <= CACHE_TTL_SUMMARY <= 600

        # Upcoming should be fresh (time-sensitive)
        assert 30 <= CACHE_TTL_UPCOMING <= 300
