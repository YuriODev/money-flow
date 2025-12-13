"""FastAPI dependencies for dependency injection.

This module provides dependency functions for FastAPI's dependency
injection system. Dependencies handle resource lifecycle including
database sessions with automatic commit/rollback.

Example:
    >>> @router.get("/items")
    ... async def get_items(db: AsyncSession = Depends(get_db)):
    ...     return await db.execute(select(Item))
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker


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
