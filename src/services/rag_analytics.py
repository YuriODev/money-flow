"""RAG analytics and monitoring service.

This module provides performance tracking and analytics for RAG operations.
It collects metrics on embedding generation, vector search, and cache usage.

Features:
- Query latency tracking
- Cache hit/miss rates
- Search quality metrics
- Usage patterns analysis
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.rag import RAGAnalytics

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single RAG query.

    Attributes:
        query_id: Unique identifier for the query.
        user_id: User who made the query.
        query_type: Type of query (search, context, embed).
        start_time: When the query started.
        embedding_ms: Time spent generating embeddings.
        search_ms: Time spent on vector search.
        total_ms: Total query time.
        cache_hit: Whether cache was used.
        results_count: Number of results returned.
        avg_score: Average relevance score.
    """

    query_id: str
    user_id: str
    query_type: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    embedding_ms: float = 0.0
    search_ms: float = 0.0
    total_ms: float = 0.0
    cache_hit: bool = False
    results_count: int = 0
    avg_score: float = 0.0


@dataclass
class AggregatedMetrics:
    """Aggregated RAG metrics over a time period.

    Attributes:
        period_start: Start of the aggregation period.
        period_end: End of the aggregation period.
        total_queries: Total number of queries.
        avg_latency_ms: Average query latency.
        p95_latency_ms: 95th percentile latency.
        cache_hit_rate: Percentage of cache hits.
        avg_results_count: Average number of results per query.
        avg_relevance_score: Average relevance score.
        queries_by_type: Breakdown of queries by type.
    """

    period_start: datetime
    period_end: datetime
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    cache_hit_rate: float = 0.0
    avg_results_count: float = 0.0
    avg_relevance_score: float = 0.0
    queries_by_type: dict[str, int] = field(default_factory=dict)


class RAGAnalyticsService:
    """Service for tracking and analyzing RAG performance.

    Provides methods for logging query metrics and generating
    aggregated analytics reports.

    Attributes:
        db: Async database session.

    Example:
        >>> service = RAGAnalyticsService(db)
        >>> await service.log_query(metrics)
        >>> report = await service.get_daily_report()
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the analytics service.

        Args:
            db: Async database session.
        """
        self.db = db

    async def log_query(self, metrics: QueryMetrics) -> None:
        """Log metrics for a RAG query.

        Args:
            metrics: QueryMetrics object with timing and result data.
        """
        if not settings.rag_enabled:
            return

        try:
            analytics = RAGAnalytics(
                user_id=metrics.user_id,
                query=metrics.query_type,  # Store query type as query
                resolved_query=f"query_id:{metrics.query_id}",  # Store query ID in resolved_query
                embedding_latency_ms=int(metrics.embedding_ms),
                search_latency_ms=int(metrics.search_ms),
                total_latency_ms=int(metrics.total_ms),
                cache_hit=metrics.cache_hit,
                relevant_history_count=metrics.results_count,
                avg_relevance_score=metrics.avg_score,
            )
            self.db.add(analytics)
            await self.db.commit()
            logger.debug(f"Logged RAG query metrics: {metrics.query_id}")
        except Exception as e:
            logger.warning(f"Failed to log RAG metrics: {e}")
            await self.db.rollback()

    async def get_metrics_for_period(
        self,
        start: datetime,
        end: datetime,
        user_id: str | None = None,
    ) -> AggregatedMetrics:
        """Get aggregated metrics for a time period.

        Args:
            start: Start of the period.
            end: End of the period.
            user_id: Optional user ID to filter by.

        Returns:
            AggregatedMetrics with aggregated statistics.
        """
        try:
            query = select(RAGAnalytics).where(
                RAGAnalytics.created_at >= start,
                RAGAnalytics.created_at <= end,
            )

            if user_id:
                query = query.where(RAGAnalytics.user_id == user_id)

            result = await self.db.execute(query)
            records = list(result.scalars().all())

            if not records:
                return AggregatedMetrics(period_start=start, period_end=end)

            # Calculate aggregates - use correct model field names
            latencies = [r.total_latency_ms or 0 for r in records]
            cache_hits = sum(1 for r in records if r.cache_hit)

            # Sort for percentile calculation
            latencies.sort()
            p95_idx = int(len(latencies) * 0.95)

            # Count by type (stored in query field)
            type_counts: dict[str, int] = {}
            for r in records:
                query_type = r.query or "unknown"
                type_counts[query_type] = type_counts.get(query_type, 0) + 1

            return AggregatedMetrics(
                period_start=start,
                period_end=end,
                total_queries=len(records),
                avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
                p95_latency_ms=latencies[p95_idx]
                if p95_idx < len(latencies)
                else (latencies[-1] if latencies else 0),
                cache_hit_rate=(cache_hits / len(records) * 100) if records else 0,
                avg_results_count=sum(r.relevant_history_count or 0 for r in records)
                / len(records),
                avg_relevance_score=sum(float(r.avg_relevance_score or 0) for r in records)
                / len(records),
                queries_by_type=type_counts,
            )

        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            return AggregatedMetrics(period_start=start, period_end=end)

    async def get_daily_report(
        self,
        date: datetime | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a daily performance report.

        Args:
            date: Date to report on (default: today).
            user_id: Optional user ID to filter by.

        Returns:
            Dictionary with daily metrics and trends.
        """
        if date is None:
            date = datetime.utcnow()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Get today's metrics
        today_metrics = await self.get_metrics_for_period(day_start, day_end, user_id)

        # Get yesterday's metrics for comparison
        yesterday_start = day_start - timedelta(days=1)
        yesterday_metrics = await self.get_metrics_for_period(yesterday_start, day_start, user_id)

        # Calculate trends
        latency_change = 0.0
        if yesterday_metrics.avg_latency_ms > 0:
            latency_change = (
                (today_metrics.avg_latency_ms - yesterday_metrics.avg_latency_ms)
                / yesterday_metrics.avg_latency_ms
                * 100
            )

        query_change = 0.0
        if yesterday_metrics.total_queries > 0:
            query_change = (
                (today_metrics.total_queries - yesterday_metrics.total_queries)
                / yesterday_metrics.total_queries
                * 100
            )

        return {
            "date": day_start.isoformat(),
            "metrics": {
                "total_queries": today_metrics.total_queries,
                "avg_latency_ms": round(today_metrics.avg_latency_ms, 2),
                "p95_latency_ms": round(today_metrics.p95_latency_ms, 2),
                "cache_hit_rate": round(today_metrics.cache_hit_rate, 2),
                "avg_results_count": round(today_metrics.avg_results_count, 2),
                "avg_relevance_score": round(today_metrics.avg_relevance_score, 3),
            },
            "breakdown": today_metrics.queries_by_type,
            "trends": {
                "latency_change_pct": round(latency_change, 2),
                "query_change_pct": round(query_change, 2),
            },
            "health": self._assess_health(today_metrics),
        }

    def _assess_health(self, metrics: AggregatedMetrics) -> dict[str, Any]:
        """Assess the health of RAG operations.

        Args:
            metrics: Current metrics to assess.

        Returns:
            Health assessment with status and warnings.
        """
        warnings = []
        status = "healthy"

        # Check latency
        if metrics.avg_latency_ms > 500:
            warnings.append("High average latency (>500ms)")
            status = "degraded"
        elif metrics.avg_latency_ms > 300:
            warnings.append("Elevated latency (>300ms)")

        # Check p95 latency
        if metrics.p95_latency_ms > 1000:
            warnings.append("High p95 latency (>1000ms)")
            status = "degraded"

        # Check cache hit rate
        if metrics.cache_hit_rate < 30 and metrics.total_queries > 10:
            warnings.append("Low cache hit rate (<30%)")

        # Check relevance scores
        if metrics.avg_relevance_score < 0.5 and metrics.total_queries > 10:
            warnings.append("Low average relevance score (<0.5)")
            status = "degraded"

        return {
            "status": status,
            "warnings": warnings,
            "thresholds": {
                "target_latency_ms": 300,
                "target_cache_hit_rate": 60,
                "target_relevance_score": 0.7,
            },
        }

    async def get_hourly_breakdown(
        self,
        date: datetime | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get hourly breakdown of metrics for a day.

        Args:
            date: Date to report on (default: today).
            user_id: Optional user ID to filter by.

        Returns:
            List of hourly metric dictionaries.
        """
        if date is None:
            date = datetime.utcnow()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        hourly_data = []

        for hour in range(24):
            hour_start = day_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)

            metrics = await self.get_metrics_for_period(hour_start, hour_end, user_id)

            hourly_data.append(
                {
                    "hour": hour,
                    "queries": metrics.total_queries,
                    "avg_latency_ms": round(metrics.avg_latency_ms, 2),
                    "cache_hit_rate": round(metrics.cache_hit_rate, 2),
                }
            )

        return hourly_data


class QueryTimer:
    """Context manager for timing RAG queries.

    Example:
        >>> async with QueryTimer("search", "user-1") as timer:
        ...     # Do embedding
        ...     timer.record_embedding(50.0)
        ...     # Do search
        ...     timer.record_search(30.0, results=5, avg_score=0.8)
        >>> metrics = timer.get_metrics()
    """

    def __init__(self, query_type: str, user_id: str) -> None:
        """Initialize the timer.

        Args:
            query_type: Type of query being timed.
            user_id: User making the query.
        """
        import uuid

        self.query_id = str(uuid.uuid4())
        self.query_type = query_type
        self.user_id = user_id
        self.start_time = datetime.utcnow()
        self._start = time.perf_counter()
        self.embedding_ms = 0.0
        self.search_ms = 0.0
        self.cache_hit = False
        self.results_count = 0
        self.avg_score = 0.0

    def record_embedding(self, ms: float, cache_hit: bool = False) -> None:
        """Record embedding generation time.

        Args:
            ms: Time in milliseconds.
            cache_hit: Whether cache was used.
        """
        self.embedding_ms = ms
        self.cache_hit = cache_hit

    def record_search(
        self,
        ms: float,
        results: int = 0,
        avg_score: float = 0.0,
    ) -> None:
        """Record search time and results.

        Args:
            ms: Time in milliseconds.
            results: Number of results returned.
            avg_score: Average relevance score.
        """
        self.search_ms = ms
        self.results_count = results
        self.avg_score = avg_score

    def get_metrics(self) -> QueryMetrics:
        """Get the complete query metrics.

        Returns:
            QueryMetrics object with all recorded data.
        """
        total_ms = (time.perf_counter() - self._start) * 1000
        return QueryMetrics(
            query_id=self.query_id,
            user_id=self.user_id,
            query_type=self.query_type,
            start_time=self.start_time,
            embedding_ms=self.embedding_ms,
            search_ms=self.search_ms,
            total_ms=total_ms,
            cache_hit=self.cache_hit,
            results_count=self.results_count,
            avg_score=self.avg_score,
        )

    async def __aenter__(self) -> "QueryTimer":
        """Enter the context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the context manager."""
        pass


def get_rag_analytics_service(db: AsyncSession) -> RAGAnalyticsService:
    """Get a RAGAnalyticsService instance.

    Args:
        db: Async database session.

    Returns:
        RAGAnalyticsService instance.
    """
    return RAGAnalyticsService(db)
