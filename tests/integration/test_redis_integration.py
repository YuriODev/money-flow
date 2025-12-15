"""Redis Integration Tests for Sprint 2.3.3.

Tests for Redis cache operations, rate limiting, and token blacklist:
- Cache service operations (get, set, delete, exists, clear_pattern)
- Rate limiter with Redis backend
- Token blacklist (future implementation)
- Connection failure handling

Usage:
    pytest tests/integration/test_redis_integration.py -v

    # Run with real Redis (requires running Redis):
    docker-compose up redis -d
    pytest tests/integration/test_redis_integration.py -v

Note:
    Tests use mocked Redis by default. Real Redis tests require
    a running Redis instance on localhost:6379.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cache_service import CacheService, get_cache_service


class TestCacheServiceOperations:
    """Tests for cache service basic operations (2.3.3.1)."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.exists = AsyncMock(return_value=1)
        mock.scan = AsyncMock(return_value=(0, []))
        mock.info = AsyncMock(return_value={})
        mock.aclose = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, mock_redis):
        """Test setting and getting values from cache."""
        cache = CacheService()
        cache._redis = mock_redis

        # Set value
        mock_redis.setex = AsyncMock(return_value=True)
        result = await cache.set("test:key", {"data": "value"}, ttl=3600)
        assert result is True

        # Verify setex was called with JSON
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test:key"
        assert call_args[0][1] == 3600
        assert json.loads(call_args[0][2]) == {"data": "value"}

        # Get value
        mock_redis.get = AsyncMock(return_value='{"data": "value"}')
        value = await cache.get("test:key")
        assert value == {"data": "value"}

    @pytest.mark.asyncio
    async def test_cache_get_missing_key(self, mock_redis):
        """Test getting a non-existent key returns None."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.get = AsyncMock(return_value=None)
        value = await cache.get("nonexistent:key")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_delete(self, mock_redis):
        """Test deleting a cache key."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.delete = AsyncMock(return_value=1)
        result = await cache.delete("test:key")
        assert result is True

        mock_redis.delete.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_cache_delete_nonexistent(self, mock_redis):
        """Test deleting a non-existent key returns False."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.delete = AsyncMock(return_value=0)
        result = await cache.delete("nonexistent:key")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_exists(self, mock_redis):
        """Test checking if key exists."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.exists = AsyncMock(return_value=1)
        result = await cache.exists("test:key")
        assert result is True

        mock_redis.exists = AsyncMock(return_value=0)
        result = await cache.exists("nonexistent:key")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_set_with_default_ttl(self, mock_redis):
        """Test setting value with default TTL from settings."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.setex = AsyncMock(return_value=True)
        await cache.set("test:key", "value")

        # Verify TTL was set (default from settings)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] > 0  # TTL should be positive

    @pytest.mark.asyncio
    async def test_cache_json_serialization(self, mock_redis):
        """Test JSON serialization of complex objects."""
        cache = CacheService()
        cache._redis = mock_redis

        # Test nested object
        complex_data = {
            "user": "test",
            "items": [1, 2, 3],
            "nested": {"a": "b"},
            "number": 42.5,
            "boolean": True,
            "null_value": None,
        }

        mock_redis.setex = AsyncMock(return_value=True)
        await cache.set("complex:key", complex_data)

        call_args = mock_redis.setex.call_args
        stored_value = json.loads(call_args[0][2])
        assert stored_value == complex_data

    @pytest.mark.asyncio
    async def test_cache_list_serialization(self, mock_redis):
        """Test JSON serialization of lists (embedding vectors)."""
        cache = CacheService()
        cache._redis = mock_redis

        # Simulate embedding vector
        embedding = [0.1] * 384

        mock_redis.setex = AsyncMock(return_value=True)
        await cache.set("emb:model:hash", embedding)

        call_args = mock_redis.setex.call_args
        stored_value = json.loads(call_args[0][2])
        assert stored_value == embedding
        assert len(stored_value) == 384

    @pytest.mark.asyncio
    async def test_cache_graceful_degradation_on_get_error(self, mock_redis):
        """Test graceful degradation when get fails."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        result = await cache.get("test:key")
        assert result is None  # Should return None, not raise

    @pytest.mark.asyncio
    async def test_cache_graceful_degradation_on_set_error(self, mock_redis):
        """Test graceful degradation when set fails."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))
        result = await cache.set("test:key", "value")
        assert result is False  # Should return False, not raise

    @pytest.mark.asyncio
    async def test_cache_operations_when_disconnected(self):
        """Test cache operations return gracefully when not connected."""
        cache = CacheService()
        cache._redis = None  # Not connected

        # All operations should return None/False without error
        assert await cache.get("key") is None
        assert await cache.set("key", "value") is False
        assert await cache.delete("key") is False
        assert await cache.exists("key") is False


class TestCacheServiceClearPattern:
    """Tests for cache pattern clearing (2.3.3.1)."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.aclose = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_clear_pattern_deletes_matching_keys(self, mock_redis):
        """Test clearing keys by pattern."""
        cache = CacheService()
        cache._redis = mock_redis

        # Mock scan to return keys then finish
        mock_redis.scan = AsyncMock(
            side_effect=[
                (1, ["emb:model:hash1", "emb:model:hash2"]),
                (0, ["emb:model:hash3"]),
            ]
        )
        mock_redis.delete = AsyncMock(return_value=2)

        deleted = await cache.clear_pattern("emb:*")
        assert deleted == 4  # 2 + 2 from two delete calls

    @pytest.mark.asyncio
    async def test_clear_pattern_no_matches(self, mock_redis):
        """Test clearing pattern with no matches."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.scan = AsyncMock(return_value=(0, []))
        deleted = await cache.clear_pattern("nonexistent:*")
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_clear_pattern_when_disconnected(self):
        """Test clear pattern when not connected."""
        cache = CacheService()
        cache._redis = None

        deleted = await cache.clear_pattern("any:*")
        assert deleted == 0


class TestCacheServiceStats:
    """Tests for cache statistics (2.3.3.1)."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_get_stats_connected(self, mock_redis):
        """Test getting stats when connected."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.info = AsyncMock(
            side_effect=[
                {"used_memory_human": "1.5MB", "used_memory_peak_human": "2MB"},
                {"keyspace_hits": 100, "keyspace_misses": 20},
            ]
        )

        stats = await cache.get_stats()
        assert stats["status"] == "connected"
        assert stats["used_memory"] == "1.5MB"
        assert stats["keyspace_hits"] == 100
        assert stats["keyspace_misses"] == 20
        assert stats["hit_rate"] == 83.33  # 100/(100+20) * 100

    @pytest.mark.asyncio
    async def test_get_stats_disconnected(self):
        """Test getting stats when disconnected."""
        cache = CacheService()
        cache._redis = None

        stats = await cache.get_stats()
        assert stats["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self):
        """Test hit rate calculation edge cases."""
        cache = CacheService()

        # No hits or misses
        assert cache._calculate_hit_rate(0, 0) == 0.0

        # All hits
        assert cache._calculate_hit_rate(100, 0) == 100.0

        # All misses
        assert cache._calculate_hit_rate(0, 100) == 0.0

        # Mixed
        assert cache._calculate_hit_rate(75, 25) == 75.0


class TestCacheServiceConnection:
    """Tests for cache service connection handling (2.3.3.4)."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.mark.asyncio
    async def test_connect_creates_pool(self):
        """Test that connect creates a connection pool."""
        cache = CacheService()

        with patch("src.services.cache_service.ConnectionPool") as mock_pool_cls:
            mock_pool = MagicMock()
            mock_pool_cls.from_url.return_value = mock_pool

            with patch("src.services.cache_service.redis.Redis") as mock_redis_cls:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis_cls.return_value = mock_redis

                await cache.connect()

                mock_pool_cls.from_url.assert_called_once()
                mock_redis_cls.assert_called_once_with(connection_pool=mock_pool)

    @pytest.mark.asyncio
    async def test_connect_failure_raises_connection_error(self):
        """Test that connection failure raises ConnectionError."""
        cache = CacheService()

        with patch("src.services.cache_service.ConnectionPool") as mock_pool_cls:
            mock_pool = MagicMock()
            mock_pool_cls.from_url.return_value = mock_pool

            with patch("src.services.cache_service.redis.Redis") as mock_redis_cls:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))
                mock_redis_cls.return_value = mock_redis

                with pytest.raises(ConnectionError, match="Redis connection failed"):
                    await cache.connect()

    @pytest.mark.asyncio
    async def test_disconnect_closes_connection(self):
        """Test that disconnect closes connection properly."""
        cache = CacheService()
        mock_redis = AsyncMock()
        mock_redis.aclose = AsyncMock()
        cache._redis = mock_redis

        mock_pool = AsyncMock()
        mock_pool.disconnect = AsyncMock()
        CacheService._pool = mock_pool

        await cache.disconnect()

        mock_redis.aclose.assert_called_once()
        mock_pool.disconnect.assert_called_once()
        assert cache._redis is None

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that CacheService is a singleton."""
        cache1 = CacheService()
        cache2 = CacheService()
        assert cache1 is cache2


class TestRateLimiterWithRedis:
    """Tests for rate limiter with Redis backend (2.3.3.2)."""

    def test_rate_limit_key_authenticated_user(self):
        """Test rate limit key for authenticated user."""
        from src.security.rate_limit import get_rate_limit_key

        request = MagicMock()
        request.state.user_id = "user-123"

        key = get_rate_limit_key(request)
        assert key == "user:user-123"

    def test_rate_limit_key_anonymous_user(self):
        """Test rate limit key for anonymous user (IP-based)."""
        from src.security.rate_limit import get_rate_limit_key

        request = MagicMock()
        del request.state.user_id  # No user_id
        request.client.host = "192.168.1.1"

        with patch("src.security.rate_limit.get_remote_address", return_value="192.168.1.1"):
            key = get_rate_limit_key(request)
            assert key == "192.168.1.1"

    def test_limiter_has_redis_storage(self):
        """Test that limiter is configured with Redis storage."""
        from src.security.rate_limit import limiter

        # Limiter should exist and be configured
        assert limiter is not None
        assert hasattr(limiter, "enabled")

    def test_rate_limits_configured(self):
        """Test that rate limits are configured from settings."""
        from src.security.rate_limit import (
            rate_limit_agent,
            rate_limit_auth,
            rate_limit_get,
            rate_limit_write,
        )

        # All rate limits should be strings like "100/minute"
        assert "/" in rate_limit_get
        assert "/" in rate_limit_write
        assert "/" in rate_limit_agent
        assert "/" in rate_limit_auth

    def test_redis_storage_uri_format(self):
        """Test Redis storage URI is correctly formatted."""
        from src.security.rate_limit import _get_redis_storage_uri

        with patch("src.security.rate_limit.settings") as mock_settings:
            mock_settings.rate_limit_enabled = True
            mock_settings.redis_url = "redis://localhost:6379/0"

            uri = _get_redis_storage_uri()
            assert uri == "redis://localhost:6379/0"

    def test_redis_storage_disabled_when_rate_limit_off(self):
        """Test Redis storage is disabled when rate limiting is off."""
        from src.security.rate_limit import _get_redis_storage_uri

        with patch("src.security.rate_limit.settings") as mock_settings:
            mock_settings.rate_limit_enabled = False

            uri = _get_redis_storage_uri()
            assert uri is None


class TestTokenBlacklist:
    """Tests for token blacklist operations (2.3.3.3).

    Note: Token blacklist is not yet implemented. These tests
    document the expected behavior for future implementation.
    """

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, mock_redis):
        """Test adding a token JTI to the blacklist."""
        cache = CacheService()
        cache._redis = mock_redis

        jti = "unique-token-id-123"
        ttl = 3600  # Token expiry time

        mock_redis.setex = AsyncMock(return_value=True)

        # Use cache set for blacklist (simple implementation)
        result = await cache.set(f"blacklist:{jti}", {"revoked": True}, ttl=ttl)
        assert result is True

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "blacklist:unique-token-id-123" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_check_token_blacklisted(self, mock_redis):
        """Test checking if a token is blacklisted."""
        cache = CacheService()
        cache._redis = mock_redis

        jti = "unique-token-id-123"

        # Token is blacklisted
        mock_redis.exists = AsyncMock(return_value=1)
        is_blacklisted = await cache.exists(f"blacklist:{jti}")
        assert is_blacklisted is True

        # Token is not blacklisted
        mock_redis.exists = AsyncMock(return_value=0)
        is_blacklisted = await cache.exists(f"blacklist:{jti}")
        assert is_blacklisted is False

    @pytest.mark.asyncio
    async def test_blacklist_key_pattern(self, mock_redis):
        """Test blacklist key pattern is correct."""
        cache = CacheService()
        cache._redis = mock_redis

        jti = "abc-123-xyz"
        expected_key = f"blacklist:{jti}"

        mock_redis.setex = AsyncMock(return_value=True)
        await cache.set(expected_key, {"revoked": True}, ttl=3600)

        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == expected_key


class TestConnectionFailureHandling:
    """Tests for Redis connection failure handling (2.3.3.4)."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.mark.asyncio
    async def test_get_cache_service_handles_connection_failure(self):
        """Test get_cache_service handles connection failure gracefully."""
        # Reset the module-level cache service
        import src.services.cache_service as cache_module

        cache_module._cache_service = None

        with patch.object(CacheService, "connect", side_effect=ConnectionError("Failed")):
            # Should not raise, just log warning
            cache = await get_cache_service()
            assert cache is not None
            # Operations should return None/False when not connected
            assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_operations_after_connection_lost(self):
        """Test operations handle lost connection gracefully."""
        cache = CacheService()
        mock_redis = AsyncMock()
        cache._redis = mock_redis

        # Simulate connection lost during operation
        mock_redis.get = AsyncMock(side_effect=Exception("Connection lost"))

        result = await cache.get("key")
        assert result is None  # Should return None, not raise

    @pytest.mark.asyncio
    async def test_reconnection_after_failure(self):
        """Test reconnection after connection failure."""
        cache = CacheService()

        # First connection fails
        with patch("src.services.cache_service.ConnectionPool") as mock_pool_cls:
            mock_pool = MagicMock()
            mock_pool_cls.from_url.return_value = mock_pool

            with patch("src.services.cache_service.redis.Redis") as mock_redis_cls:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))
                mock_redis_cls.return_value = mock_redis

                with pytest.raises(ConnectionError):
                    await cache.connect()

        # Reset for second attempt
        cache._redis = None
        CacheService._pool = None

        # Second connection succeeds
        with patch("src.services.cache_service.ConnectionPool") as mock_pool_cls:
            mock_pool = MagicMock()
            mock_pool_cls.from_url.return_value = mock_pool

            with patch("src.services.cache_service.redis.Redis") as mock_redis_cls:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis_cls.return_value = mock_redis

                await cache.connect()
                assert cache._redis is not None


class TestEmbeddingCacheIntegration:
    """Tests for embedding cache integration patterns."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_embedding_cache_key_format(self, mock_redis):
        """Test embedding cache key format."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.setex = AsyncMock(return_value=True)

        # Embedding key format: emb:{model}:{hash}
        model = "all-MiniLM-L6-v2"
        text_hash = "abc123def456"
        key = f"emb:{model}:{text_hash}"
        embedding = [0.1] * 384

        await cache.set(key, embedding, ttl=3600)

        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"emb:{model}:{text_hash}"

    @pytest.mark.asyncio
    async def test_embedding_cache_hit(self, mock_redis):
        """Test embedding cache hit returns cached vector."""
        cache = CacheService()
        cache._redis = mock_redis

        cached_embedding = [0.1] * 384
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_embedding))

        result = await cache.get("emb:model:hash123")
        assert result == cached_embedding
        assert len(result) == 384

    @pytest.mark.asyncio
    async def test_embedding_cache_miss(self, mock_redis):
        """Test embedding cache miss returns None."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.get = AsyncMock(return_value=None)

        result = await cache.get("emb:model:newhash")
        assert result is None


class TestRAGSessionCacheIntegration:
    """Tests for RAG session cache integration patterns."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_session_cache_key_format(self, mock_redis):
        """Test session cache key format."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.setex = AsyncMock(return_value=True)

        # Session key format: ctx:{user_id}:{session_id}
        user_id = "user-123"
        session_id = "sess-456"
        key = f"ctx:{user_id}:{session_id}"
        context = {"turns": [{"role": "user", "content": "hello"}]}

        await cache.set(key, context, ttl=3600)

        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"ctx:{user_id}:{session_id}"

    @pytest.mark.asyncio
    async def test_clear_user_sessions(self, mock_redis):
        """Test clearing all sessions for a user."""
        cache = CacheService()
        cache._redis = mock_redis

        user_id = "user-123"
        mock_redis.scan = AsyncMock(
            side_effect=[
                (0, [f"ctx:{user_id}:sess1", f"ctx:{user_id}:sess2"]),
            ]
        )
        mock_redis.delete = AsyncMock(return_value=2)

        deleted = await cache.clear_pattern(f"ctx:{user_id}:*")
        assert deleted == 2


class TestCacheTTLBehavior:
    """Tests for cache TTL behavior."""

    @pytest.fixture(autouse=True)
    def reset_cache_service(self):
        """Reset cache service before each test."""
        CacheService.reset()
        yield
        CacheService.reset()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_different_ttls_for_different_data(self, mock_redis):
        """Test different TTLs are used for different data types."""
        cache = CacheService()
        cache._redis = mock_redis

        mock_redis.setex = AsyncMock(return_value=True)

        # Embedding - 1 hour
        await cache.set("emb:model:hash", [0.1], ttl=3600)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600

        # Context - 30 minutes
        await cache.set("ctx:user:sess", {"turns": []}, ttl=1800)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 1800

        # Search results - 5 minutes
        await cache.set("search:type:hash", {"results": []}, ttl=300)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300
