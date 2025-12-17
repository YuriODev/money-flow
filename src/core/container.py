"""Dependency injection container for Money Flow application.

This module provides a centralized dependency injection container using
the dependency-injector library. It manages the lifecycle of services,
database sessions, and external clients.

The container provides:
- Configuration from environment variables
- Database session factory with connection pooling
- Service factories for business logic
- External client factories (Redis, Qdrant, Anthropic)

Usage:
    from src.core.container import container, init_container

    # Initialize at application startup
    init_container()

    # Use providers in FastAPI endpoints
    @router.get("/items")
    @inject
    async def get_items(
        db: AsyncSession = Depends(Provide[Container.db_session])
    ):
        service = SubscriptionService(db)
        return await service.get_all()
"""

import logging
from typing import Any

from dependency_injector import containers, providers

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Functions (defined before Container to avoid forward references)
# =============================================================================


def provide_db_session_factory() -> Any:
    """Provide the database session factory.

    Returns the async_session_maker from the database module.
    """
    from src.db.database import async_session_maker

    return async_session_maker


def provide_currency_service() -> Any:
    """Create a currency service singleton.

    Returns:
        CurrencyService instance.
    """
    from src.services.currency_service import CurrencyService

    return CurrencyService()


def provide_anthropic_client(api_key: str | None = None) -> Any:
    """Create an Anthropic client singleton.

    Args:
        api_key: Anthropic API key.

    Returns:
        Anthropic client instance or None if API key not configured.
    """
    if not api_key:
        logger.warning("Anthropic API key not configured, returning None")
        return None

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        logger.info("Anthropic client created")
        return client
    except Exception as e:
        logger.error(f"Failed to create Anthropic client: {e}")
        return None


async def provide_redis_client(redis_url: str | None = None) -> Any:
    """Create and yield a Redis client.

    The client is closed when the container shuts down.

    Args:
        redis_url: Redis connection URL.

    Yields:
        Redis client instance or None if Redis is not configured.
    """
    if not redis_url:
        logger.warning("Redis URL not configured, returning None")
        yield None
        return

    client = None
    try:
        import redis.asyncio as redis

        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client created")
        yield client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        yield None
    finally:
        if client:
            await client.close()
            logger.info("Redis client closed")


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for the application.

    This container manages all application dependencies including:
    - Configuration settings
    - Database connections and session factories
    - Service singletons
    - External client connections

    The container uses providers to lazily instantiate dependencies
    and manage their lifecycle.

    Attributes:
        config: Application configuration provider.
        db_session_factory: Async database session factory.
        currency_service: Currency conversion service (singleton).
        anthropic_client: Anthropic API client (singleton).
        redis_client: Redis client (resource with cleanup).

    Example:
        >>> container = Container()
        >>> container.config.from_dict({
        ...     "anthropic_api_key": "sk-...",
        ...     "redis_url": "redis://localhost:6379"
        ... })
        >>> anthropic = container.anthropic_client()
    """

    # Configuration provider - populated from settings
    config = providers.Configuration()

    # ==========================================================================
    # Database
    # ==========================================================================

    # Database session factory - call this to get async_session_maker
    db_session_factory = providers.Singleton(provide_db_session_factory)

    # ==========================================================================
    # Services (Singletons)
    # ==========================================================================

    # Currency service - stateless singleton shared across requests
    currency_service = providers.Singleton(provide_currency_service)

    # ==========================================================================
    # External Clients
    # ==========================================================================

    # Anthropic client (singleton) - created lazily
    anthropic_client = providers.Singleton(
        provide_anthropic_client,
        api_key=config.anthropic_api_key,
    )

    # Redis client (resource) - managed lifecycle with cleanup
    redis_client = providers.Resource(
        provide_redis_client,
        redis_url=config.redis_url,
    )


# =============================================================================
# Container Instance and Initialization
# =============================================================================

# Global container instance
container = Container()


def init_container() -> Container:
    """Initialize the dependency injection container.

    Loads configuration from settings and prepares the container
    for use with the application.

    Returns:
        Configured Container instance.

    Example:
        >>> container = init_container()
        >>> # Container is now ready to use
    """
    from src.core.config import settings

    # Load configuration from Pydantic settings
    container.config.from_dict(
        {
            "anthropic_api_key": settings.anthropic_api_key,
            "redis_url": settings.redis_url,
            "database_url": settings.database_url,
            "environment": settings.sentry_environment,
            "debug": settings.debug,
        }
    )

    logger.info("Dependency injection container initialized")
    return container


def get_container() -> Container:
    """Get the global container instance.

    Returns:
        The global Container instance.
    """
    return container


def reset_container() -> None:
    """Reset the container for testing.

    Clears all singleton instances and resets configuration.
    Useful for test isolation.
    """
    container.reset_singletons()
    logger.info("Container singletons reset")
