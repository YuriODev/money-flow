"""FastAPI dependencies for dependency injection.

This module provides dependency functions for FastAPI's dependency
injection system. Dependencies handle resource lifecycle including
database sessions with automatic commit/rollback.

The module integrates with the dependency-injector container for
centralized dependency management while maintaining FastAPI's
native Depends() pattern for backward compatibility.

Example:
    >>> @router.get("/items")
    ... async def get_items(db: AsyncSession = Depends(get_db)):
    ...     return await db.execute(select(Item))
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker

if TYPE_CHECKING:
    from src.services.currency_service import CurrencyService
    from src.services.payment_card_service import PaymentCardService
    from src.services.subscription_service import SubscriptionService
    from src.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic transaction management.

    Creates an async database session that automatically commits on
    success or rolls back on exception. The session is closed after
    the request completes.

    Yields:
        AsyncSession: SQLAlchemy async session for database operations.

    Raises:
        Exception: Re-raises any exception after rolling back.

    Example:
        >>> async def endpoint(db: AsyncSession = Depends(get_db)):
        ...     subscription = Subscription(name="Test")
        ...     db.add(subscription)
        ...     # Commits automatically if no exception
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# Service Dependencies
# =============================================================================
# These dependencies provide service instances with database sessions
# injected. They follow the repository pattern where services are
# created per-request with a fresh database session.


async def get_subscription_service(
    db: AsyncSession,
    user_id: str = "default",
) -> "SubscriptionService":
    """Provide a subscription service instance.

    Args:
        db: Database session from get_db dependency.
        user_id: User ID for filtering (from auth).

    Returns:
        SubscriptionService instance.

    Example:
        >>> @router.get("/subscriptions")
        ... async def list_subs(
        ...     service: SubscriptionService = Depends(get_subscription_service)
        ... ):
        ...     return await service.get_all()
    """
    from src.services.subscription_service import SubscriptionService

    return SubscriptionService(db=db, user_id=user_id)


async def get_user_service(db: AsyncSession) -> "UserService":
    """Provide a user service instance.

    Args:
        db: Database session from get_db dependency.

    Returns:
        UserService instance.
    """
    from src.services.user_service import UserService

    return UserService(db=db)


async def get_payment_card_service(db: AsyncSession) -> "PaymentCardService":
    """Provide a payment card service instance.

    Args:
        db: Database session from get_db dependency.

    Returns:
        PaymentCardService instance.
    """
    from src.services.payment_card_service import PaymentCardService

    return PaymentCardService(db=db)


def get_currency_service() -> "CurrencyService":
    """Provide a currency service singleton.

    The currency service is stateless and can be shared
    across requests.

    Returns:
        CurrencyService singleton instance.
    """
    from src.services.currency_service import CurrencyService

    # Use a module-level singleton
    if not hasattr(get_currency_service, "_instance"):
        get_currency_service._instance = CurrencyService()
    return get_currency_service._instance
