"""Health check endpoints for container orchestration.

This module provides comprehensive health check endpoints:
- /health - Simple liveness probe
- /health/live - Kubernetes liveness probe
- /health/ready - Kubernetes readiness probe (checks dependencies)

Usage:
    from src.api.health import router
    app.include_router(router)
"""

from __future__ import annotations

import asyncio
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from src.core.config import settings
from src.core.logging import get_logger
from src.db.database import async_session_maker

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status for a single component."""

    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Complete health check response."""

    status: HealthStatus
    version: str = "0.1.0"
    checks: dict[str, ComponentHealth] = {}


router = APIRouter(tags=["health"])


async def check_database() -> ComponentHealth:
    """Check database connectivity and response time.

    Returns:
        ComponentHealth with database status.
    """
    import time

    start = time.perf_counter()
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("Database health check failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            message=str(e),
        )


async def check_redis() -> ComponentHealth:
    """Check Redis connectivity and response time.

    Returns:
        ComponentHealth with Redis status.
    """
    import time

    from src.services.cache_service import get_cache_service

    start = time.perf_counter()
    try:
        cache = await get_cache_service()
        if cache._client is None:
            return ComponentHealth(
                status=HealthStatus.DEGRADED,
                message="Redis not connected (caching disabled)",
            )

        # Ping Redis
        await cache._client.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("Redis health check failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.DEGRADED,
            latency_ms=round(latency_ms, 2),
            message=str(e),
        )


async def check_qdrant() -> ComponentHealth:
    """Check Qdrant vector database connectivity.

    Returns:
        ComponentHealth with Qdrant status.
    """
    import time

    if not settings.rag_enabled:
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            message="RAG disabled (Qdrant not required)",
        )

    start = time.perf_counter()
    try:
        # Dynamic import since qdrant is optional
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=5.0,
        )
        # Simple health check - list collections
        client.get_collections()
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except ImportError:
        return ComponentHealth(
            status=HealthStatus.DEGRADED,
            message="Qdrant client not installed (RAG features disabled)",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("Qdrant health check failed", error=str(e))
        return ComponentHealth(
            status=HealthStatus.DEGRADED,
            latency_ms=round(latency_ms, 2),
            message=str(e),
        )


async def check_anthropic() -> ComponentHealth:
    """Check Anthropic API connectivity.

    This is a lightweight check that just verifies the API key is set.
    We don't make actual API calls to avoid consuming credits.

    Returns:
        ComponentHealth with Anthropic API status.
    """
    if not settings.anthropic_api_key:
        return ComponentHealth(
            status=HealthStatus.DEGRADED,
            message="Anthropic API key not configured",
        )

    # Just verify the key is set - we don't want to make API calls for health checks
    return ComponentHealth(
        status=HealthStatus.HEALTHY,
        message="API key configured",
    )


@router.get("/health", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint for container orchestration.

    This is a fast, lightweight check that always returns healthy
    if the application is running. Use /health/ready for dependency checks.

    Returns:
        Dictionary with status key.

    Example:
        GET /health
        Response: {"status": "healthy"}
    """
    return {"status": "healthy"}


@router.get("/health/live", response_model=dict[str, str])
async def liveness_probe() -> dict[str, str]:
    """Kubernetes liveness probe endpoint.

    Returns healthy if the application process is alive and responding.
    This check should be fast and not depend on external services.

    Returns:
        Dictionary with status key.

    Example:
        GET /health/live
        Response: {"status": "healthy"}
    """
    return {"status": "healthy"}


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_probe() -> HealthResponse:
    """Kubernetes readiness probe endpoint.

    Checks all dependencies (database, Redis, Qdrant, Claude API)
    and returns overall health status. The application is considered:
    - HEALTHY: All critical services (database) are up
    - DEGRADED: Optional services (Redis, Qdrant) are down
    - UNHEALTHY: Critical services (database) are down

    Returns:
        HealthResponse with detailed component status.

    Example:
        GET /health/ready
        Response: {
            "status": "healthy",
            "version": "0.1.0",
            "checks": {
                "database": {"status": "healthy", "latency_ms": 5.2},
                "redis": {"status": "healthy", "latency_ms": 1.1},
                ...
            }
        }
    """
    # Run all health checks concurrently
    db_check, redis_check, qdrant_check, anthropic_check = await asyncio.gather(
        check_database(),
        check_redis(),
        check_qdrant(),
        check_anthropic(),
    )

    checks: dict[str, ComponentHealth] = {
        "database": db_check,
        "redis": redis_check,
        "qdrant": qdrant_check,
        "anthropic": anthropic_check,
    }

    # Determine overall status
    # Database is critical - if it's down, we're unhealthy
    if db_check.status == HealthStatus.UNHEALTHY:
        overall_status = HealthStatus.UNHEALTHY
    # If any service is degraded, we're degraded
    elif any(c.status == HealthStatus.DEGRADED for c in checks.values()):
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return HealthResponse(
        status=overall_status,
        checks=checks,
    )


__all__ = ["router"]
