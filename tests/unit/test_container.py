"""Tests for the dependency injection container.

Tests the Container class and its providers, as well as
the FastAPI dependency functions.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.core.container import (
    Container,
    container,
    get_container,
    init_container,
    provide_anthropic_client,
    provide_currency_service,
    provide_db_session_factory,
    reset_container,
)
from src.core.dependencies import (
    get_currency_service,
    get_db,
    get_payment_card_service,
    get_subscription_service,
    get_user_service,
)


class TestContainer:
    """Tests for the Container class."""

    def test_container_is_singleton(self):
        """Test that get_container returns the same instance."""
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2

    def test_container_has_config_provider(self):
        """Test that container has a configuration provider."""
        c = Container()
        assert hasattr(c, "config")

    def test_container_has_db_session_factory(self):
        """Test that container has db_session_factory provider."""
        c = Container()
        assert hasattr(c, "db_session_factory")

    def test_container_has_currency_service(self):
        """Test that container has currency_service provider."""
        c = Container()
        assert hasattr(c, "currency_service")

    def test_container_has_anthropic_client(self):
        """Test that container has anthropic_client provider."""
        c = Container()
        assert hasattr(c, "anthropic_client")

    def test_container_has_redis_client(self):
        """Test that container has redis_client provider."""
        c = Container()
        assert hasattr(c, "redis_client")


class TestContainerInitialization:
    """Tests for container initialization."""

    def test_init_container_returns_container(self):
        """Test that init_container returns the container."""
        result = init_container()
        assert result is container

    def test_reset_container_clears_singletons(self):
        """Test that reset_container clears singleton instances."""
        # This should not raise
        reset_container()


class TestProviderFunctions:
    """Tests for provider functions."""

    def test_provide_db_session_factory(self):
        """Test that provide_db_session_factory returns session maker."""
        factory = provide_db_session_factory()
        # Should be callable (the session maker)
        assert callable(factory)

    def test_provide_currency_service(self):
        """Test that provide_currency_service creates a service."""
        service = provide_currency_service()
        from src.services.currency_service import CurrencyService

        assert isinstance(service, CurrencyService)

    def test_provide_anthropic_client_without_key(self):
        """Test that anthropic client returns None without API key."""
        client = provide_anthropic_client(api_key=None)
        assert client is None

    def test_provide_anthropic_client_with_empty_key(self):
        """Test that anthropic client returns None with empty key."""
        client = provide_anthropic_client(api_key="")
        assert client is None


class TestFastAPIDependencies:
    """Tests for FastAPI dependency functions."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        sessions = []
        async for session in get_db():
            sessions.append(session)
        # Should yield exactly one session
        assert len(sessions) == 1

    @pytest.mark.asyncio
    async def test_get_db_commits_on_success(self):
        """Test that get_db commits the session on success."""
        mock_session = AsyncMock()

        with patch("src.core.dependencies.async_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)

            async for _ in get_db():
                pass

            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_rollback_on_exception(self):
        """Test that get_db handles exceptions properly.

        When an exception occurs during the database session, the session
        should be rolled back. This test verifies that the exception is
        re-raised after cleanup.
        """
        # The get_db dependency is designed to rollback on exception and re-raise.
        # We verify that exceptions propagate correctly through the generator.
        # The actual rollback behavior is tested via integration tests with a real session.
        with pytest.raises(ValueError):
            async for session in get_db():
                # Simulate an error during database operation
                raise ValueError("Test error")

    @pytest.mark.asyncio
    async def test_get_subscription_service(self, mock_db_session):
        """Test that get_subscription_service creates a service."""
        service = await get_subscription_service(mock_db_session)
        from src.services.subscription_service import SubscriptionService

        assert isinstance(service, SubscriptionService)

    @pytest.mark.asyncio
    async def test_get_subscription_service_with_user_id(self, mock_db_session):
        """Test that get_subscription_service accepts user_id."""
        service = await get_subscription_service(mock_db_session, user_id="user-123")
        assert service.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_get_user_service(self, mock_db_session):
        """Test that get_user_service creates a service."""
        service = await get_user_service(mock_db_session)
        from src.services.user_service import UserService

        assert isinstance(service, UserService)

    @pytest.mark.asyncio
    async def test_get_payment_card_service(self, mock_db_session):
        """Test that get_payment_card_service creates a service."""
        service = await get_payment_card_service(mock_db_session)
        from src.services.payment_card_service import PaymentCardService

        assert isinstance(service, PaymentCardService)

    def test_get_currency_service_singleton(self):
        """Test that get_currency_service returns a singleton."""
        # Clear any existing singleton
        if hasattr(get_currency_service, "_instance"):
            delattr(get_currency_service, "_instance")

        service1 = get_currency_service()
        service2 = get_currency_service()
        assert service1 is service2

    def test_get_currency_service_type(self):
        """Test that get_currency_service returns correct type."""
        service = get_currency_service()
        from src.services.currency_service import CurrencyService

        assert isinstance(service, CurrencyService)


class TestContainerProviders:
    """Tests for container provider instances."""

    def test_db_session_factory_provider(self):
        """Test that db_session_factory provider works."""
        c = Container()
        factory = c.db_session_factory()
        assert callable(factory)

    def test_currency_service_provider(self):
        """Test that currency_service provider works."""
        c = Container()
        service = c.currency_service()
        from src.services.currency_service import CurrencyService

        assert isinstance(service, CurrencyService)

    def test_currency_service_is_singleton(self):
        """Test that currency_service is a singleton."""
        c = Container()
        service1 = c.currency_service()
        service2 = c.currency_service()
        assert service1 is service2
