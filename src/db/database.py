"""Database engine and session configuration.

This module configures the async SQLAlchemy engine and session factory
for PostgreSQL (production) or SQLite (development). All database
operations use async/await for non-blocking I/O.

Module-level objects:
    Base: Declarative base class for ORM models.
    engine: Async database engine.
    async_session_maker: Factory for creating async sessions.

Example:
    >>> async with async_session_maker() as session:
    ...     result = await session.execute(select(Subscription))
    ...     subscriptions = result.scalars().all()
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for ORM models.

    All ORM models should inherit from this class to be registered
    with the metadata and support table creation.

    Example:
        >>> class MyModel(Base):
        ...     __tablename__ = "my_table"
        ...     id = mapped_column(Integer, primary_key=True)
    """

    pass


# Create async engine with connection pool
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # SQL logging in debug mode
    future=True,  # SQLAlchemy 2.0 style
)

# Session factory for dependency injection
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined by ORM models that inherit from Base.
    Safe to call multiple times - existing tables are not recreated.

    This function is called during application startup via the
    FastAPI lifespan handler.

    Returns:
        None

    Example:
        >>> await init_db()  # Creates tables if they don't exist
    """
    async with engine.begin() as conn:
        # Import models to register them with Base.metadata
        from src.models import rag, subscription, user  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
