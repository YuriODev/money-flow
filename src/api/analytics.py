"""Analytics API endpoints.

This module provides REST API endpoints for RAG analytics and monitoring,
including performance metrics, cache statistics, and health checks.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.dependencies import get_db
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.cache_service import get_cache_service
from src.services.rag_analytics import get_rag_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class MetricsResponse(BaseModel):
    """Response model for aggregated metrics."""

    total_queries: int
    avg_latency_ms: float
    p95_latency_ms: float
    cache_hit_rate: float
    avg_results_count: float
    avg_relevance_score: float


class HealthResponse(BaseModel):
    """Response model for health assessment."""

    status: str
    warnings: list[str]
    thresholds: dict[str, float]


class DailyReportResponse(BaseModel):
    """Response model for daily report."""

    date: str
    metrics: MetricsResponse
    breakdown: dict[str, int]
    trends: dict[str, float]
    health: HealthResponse


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    status: str
    used_memory: str = ""
    used_memory_peak: str = ""
    keyspace_hits: int = 0
    keyspace_misses: int = 0
    hit_rate: float = 0.0
    error: str | None = None


class SystemHealthResponse(BaseModel):
    """Response model for overall system health."""

    rag_enabled: bool
    cache_status: str
    rag_health: str
    warnings: list[str]


class HourlyDataPoint(BaseModel):
    """Response model for hourly data point."""

    hour: int
    queries: int
    avg_latency_ms: float
    cache_hit_rate: float


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/", response_model=dict[str, Any])
@limiter.limit(rate_limit_get)
async def get_analytics_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get overview of RAG analytics.

    Returns a summary of key metrics and system health.

    Returns:
        Dictionary with overview data including:
        - enabled: Whether RAG is enabled
        - daily_summary: Today's metrics summary
        - health: Current health status
    """
    if not settings.rag_enabled:
        return {
            "enabled": False,
            "message": "RAG analytics is not enabled",
        }

    service = get_rag_analytics_service(db)
    daily = await service.get_daily_report()

    return {
        "enabled": True,
        "daily_summary": {
            "queries": daily["metrics"]["total_queries"],
            "avg_latency_ms": daily["metrics"]["avg_latency_ms"],
            "cache_hit_rate": daily["metrics"]["cache_hit_rate"],
        },
        "health": daily["health"]["status"],
        "warnings": daily["health"]["warnings"],
    }


@router.get("/daily", response_model=DailyReportResponse)
@limiter.limit(rate_limit_get)
async def get_daily_report(
    request: Request,
    date: str | None = Query(
        None,
        description="Date in YYYY-MM-DD format (default: today)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    user_id: str | None = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get detailed daily analytics report.

    Provides comprehensive metrics for a specific day including
    query counts, latencies, cache performance, and health assessment.

    Args:
        date: Date to report on (YYYY-MM-DD format).
        user_id: Optional user ID to filter by.

    Returns:
        DailyReportResponse with full daily metrics.
    """
    if not settings.rag_enabled:
        raise HTTPException(
            status_code=503,
            detail="RAG analytics is not enabled",
        )

    report_date = None
    if date:
        try:
            report_date = datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

    service = get_rag_analytics_service(db)
    report = await service.get_daily_report(date=report_date, user_id=user_id)

    return report


@router.get("/hourly", response_model=list[HourlyDataPoint])
@limiter.limit(rate_limit_get)
async def get_hourly_breakdown(
    request: Request,
    date: str | None = Query(
        None,
        description="Date in YYYY-MM-DD format (default: today)",
    ),
    user_id: str | None = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get hourly breakdown of metrics.

    Provides hour-by-hour metrics for a specific day,
    useful for identifying usage patterns and peak times.

    Args:
        date: Date to report on (YYYY-MM-DD format).
        user_id: Optional user ID to filter by.

    Returns:
        List of hourly metric data points.
    """
    if not settings.rag_enabled:
        raise HTTPException(
            status_code=503,
            detail="RAG analytics is not enabled",
        )

    report_date = None
    if date:
        try:
            report_date = datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

    service = get_rag_analytics_service(db)
    return await service.get_hourly_breakdown(date=report_date, user_id=user_id)


@router.get("/cache", response_model=CacheStatsResponse)
@limiter.limit(rate_limit_get)
async def get_cache_stats(request: Request) -> dict[str, Any]:
    """Get Redis cache statistics.

    Returns current cache health and performance metrics
    including memory usage and hit rates.

    Returns:
        CacheStatsResponse with cache statistics.
    """
    try:
        cache = await get_cache_service()
        stats = await cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/health", response_model=SystemHealthResponse)
@limiter.limit(rate_limit_get)
async def get_system_health(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get overall RAG system health.

    Provides a comprehensive health check of all RAG components
    including cache, vector store, and query performance.

    Returns:
        SystemHealthResponse with health status and warnings.
    """
    warnings = []
    cache_status = "disconnected"
    rag_health = "unknown"

    # Check cache
    try:
        cache = await get_cache_service()
        stats = await cache.get_stats()
        cache_status = stats.get("status", "unknown")

        if cache_status == "connected":
            hit_rate = stats.get("hit_rate", 0)
            if hit_rate < 30:
                warnings.append(f"Low cache hit rate: {hit_rate}%")
    except Exception as e:
        cache_status = "error"
        warnings.append(f"Cache error: {str(e)}")

    # Check RAG performance
    if settings.rag_enabled:
        try:
            service = get_rag_analytics_service(db)
            report = await service.get_daily_report()
            rag_health = report.get("health", {}).get("status", "unknown")
            warnings.extend(report.get("health", {}).get("warnings", []))
        except Exception as e:
            rag_health = "error"
            warnings.append(f"RAG analytics error: {str(e)}")
    else:
        rag_health = "disabled"

    return {
        "rag_enabled": settings.rag_enabled,
        "cache_status": cache_status,
        "rag_health": rag_health,
        "warnings": warnings,
    }


@router.delete("/cache/pattern/{pattern}")
@limiter.limit(rate_limit_write)
async def clear_cache_pattern(request: Request, pattern: str) -> dict[str, Any]:
    """Clear cache keys matching a pattern.

    Use with caution - this deletes cached data.

    Args:
        pattern: Redis key pattern to match (e.g., "emb:*").

    Returns:
        Dictionary with count of deleted keys.
    """
    try:
        cache = await get_cache_service()
        deleted = await cache.clear_pattern(pattern)
        return {
            "success": True,
            "pattern": pattern,
            "deleted_count": deleted,
        }
    except Exception as e:
        logger.error(f"Failed to clear cache pattern: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}",
        )
