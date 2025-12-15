"""Database engine and session configuration.

This module configures the async SQLAlchemy engine and session factory
for PostgreSQL (production) or SQLite (development). All database
operations use async/await for non-blocking I/O.

Connection Pool Configuration (PostgreSQL only):
    - pool_size: Number of persistent connections in pool (default: 5)
    - max_overflow: Additional connections when pool is full (default: 10)
    - pool_timeout: Seconds to wait for available connection (default: 30)
    - pool_recycle: Recycle connections after N seconds (default: 1800)
    - pool_pre_ping: Verify connections before using (default: True)

Module-level objects:
    Base: Declarative base class for ORM models.
    engine: Async database engine with optimized connection pool.
    async_session_maker: Factory for creating async sessions.

Example:
    >>> async with async_session_maker() as session:
    ...     result = await session.execute(select(Subscription))
    ...     subscriptions = result.scalars().all()
"""

import logging

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import Pool

from src.core.config import settings

logger = logging.getLogger(__name__)


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


def _get_engine_kwargs() -> dict:
    """Build engine kwargs based on database type.

    PostgreSQL gets connection pool optimization settings.
    SQLite uses NullPool (no pooling) as it doesn't support concurrent access.

    Returns:
        dict: Engine configuration kwargs.
    """
    kwargs = {
        "echo": settings.debug,  # SQL logging in debug mode
        "future": True,  # SQLAlchemy 2.0 style
    }

    # Apply connection pool settings only for PostgreSQL
    if "postgresql" in settings.database_url:
        kwargs.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_pool_max_overflow,
                "pool_timeout": settings.db_pool_timeout,
                "pool_recycle": settings.db_pool_recycle,
                "pool_pre_ping": settings.db_pool_pre_ping,
            }
        )
        logger.info(
            "PostgreSQL connection pool configured: "
            f"pool_size={settings.db_pool_size}, "
            f"max_overflow={settings.db_pool_max_overflow}, "
            f"pool_recycle={settings.db_pool_recycle}s"
        )
    else:
        # SQLite doesn't support connection pooling
        from sqlalchemy.pool import NullPool

        kwargs["poolclass"] = NullPool
        logger.info("SQLite database configured with NullPool (no connection pooling)")

    return kwargs


# Create async engine with optimized connection pool
engine = create_async_engine(settings.database_url, **_get_engine_kwargs())


# Pool event listeners for metrics and debugging
@event.listens_for(Pool, "checkout")
def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug(f"Connection checked out from pool: {connection_record}")


@event.listens_for(Pool, "checkin")
def _on_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    logger.debug(f"Connection returned to pool: {connection_record}")


@event.listens_for(Pool, "connect")
def _on_connect(dbapi_conn, connection_record):
    """Log when a new connection is created."""
    logger.info(f"New database connection created: {connection_record}")


@event.listens_for(Pool, "invalidate")
def _on_invalidate(dbapi_conn, connection_record, exception):
    """Log when a connection is invalidated."""
    logger.warning(f"Connection invalidated: {connection_record}, reason: {exception}")


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


def get_pool_status() -> dict:
    """Get current connection pool status for monitoring.

    Returns pool statistics including checked-out connections,
    total connections, and overflow status.

    Returns:
        dict: Pool status metrics with the following keys:
            - pool_size: Configured pool size
            - checked_out: Currently checked out connections
            - checked_in: Available connections in pool
            - overflow: Current overflow connections
            - invalid: Invalid connections count
            - total: Total connections (checked_in + checked_out)

    Example:
        >>> status = get_pool_status()
        >>> print(f"Active: {status['checked_out']}/{status['pool_size']}")
        Active: 3/5
    """
    pool = engine.pool

    # For NullPool (SQLite), return minimal stats
    if not hasattr(pool, "size"):
        return {
            "pool_size": 0,
            "checked_out": 0,
            "checked_in": 0,
            "overflow": 0,
            "invalid": 0,
            "total": 0,
            "pool_type": "NullPool",
        }

    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "checked_in": pool.checkedin(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, "invalidatedcount") else 0,
        "total": pool.checkedin() + pool.checkedout(),
        "pool_type": "QueuePool",
    }
