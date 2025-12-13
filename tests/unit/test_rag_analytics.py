"""Tests for RAGAnalyticsService.

Tests cover:
- Query metrics logging
- Aggregated metrics calculation
- Daily reports
- Health assessment
- Query timer
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.rag_analytics import (
    AggregatedMetrics,
    QueryMetrics,
    QueryTimer,
    RAGAnalyticsService,
    get_rag_analytics_service,
)


class TestQueryMetrics:
    """Tests for QueryMetrics dataclass."""

    def test_create_query_metrics(self):
        """Test creating QueryMetrics."""
        metrics = QueryMetrics(
            query_id="q-1",
            user_id="user-1",
            query_type="search",
            embedding_ms=50.0,
            search_ms=30.0,
            total_ms=85.0,
            cache_hit=True,
            results_count=5,
            avg_score=0.85,
        )

        assert metrics.query_id == "q-1"
        assert metrics.user_id == "user-1"
        assert metrics.cache_hit is True
        assert metrics.avg_score == 0.85


class TestAggregatedMetrics:
    """Tests for AggregatedMetrics dataclass."""

    def test_create_aggregated_metrics(self):
        """Test creating AggregatedMetrics."""
        now = datetime.utcnow()
        metrics = AggregatedMetrics(
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_queries=100,
            avg_latency_ms=150.5,
            p95_latency_ms=300.0,
            cache_hit_rate=65.0,
        )

        assert metrics.total_queries == 100
        assert metrics.avg_latency_ms == 150.5
        assert metrics.cache_hit_rate == 65.0


class TestRAGAnalyticsServiceInit:
    """Tests for RAGAnalyticsService initialization."""

    def test_init_sets_db(self):
        """Test that initialization sets database session."""
        mock_db = MagicMock()
        service = RAGAnalyticsService(mock_db)

        assert service.db == mock_db

    def test_get_rag_analytics_service_factory(self):
        """Test factory function creates service."""
        mock_db = MagicMock()
        service = get_rag_analytics_service(mock_db)

        assert isinstance(service, RAGAnalyticsService)


class TestRAGAnalyticsServiceLogQuery:
    """Tests for query logging."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_log_query_adds_to_db(self, mock_db):
        """Test that log_query adds record to database."""
        with patch("src.services.rag_analytics.settings") as mock_settings:
            mock_settings.rag_enabled = True

            service = RAGAnalyticsService(mock_db)
            metrics = QueryMetrics(
                query_id="q-1",
                user_id="user-1",
                query_type="search",
            )

            await service.log_query(metrics)

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_query_skips_when_disabled(self, mock_db):
        """Test that log_query skips when RAG is disabled."""
        with patch("src.services.rag_analytics.settings") as mock_settings:
            mock_settings.rag_enabled = False

            service = RAGAnalyticsService(mock_db)
            metrics = QueryMetrics(
                query_id="q-1",
                user_id="user-1",
                query_type="search",
            )

            await service.log_query(metrics)

            mock_db.add.assert_not_called()


class TestHealthAssessment:
    """Tests for health assessment."""

    def test_assess_health_healthy(self):
        """Test healthy status assessment."""
        mock_db = MagicMock()
        service = RAGAnalyticsService(mock_db)

        now = datetime.utcnow()
        metrics = AggregatedMetrics(
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_queries=100,
            avg_latency_ms=150.0,
            p95_latency_ms=250.0,
            cache_hit_rate=65.0,
            avg_relevance_score=0.8,
        )

        health = service._assess_health(metrics)

        assert health["status"] == "healthy"
        assert len(health["warnings"]) == 0

    def test_assess_health_degraded_latency(self):
        """Test degraded status for high latency."""
        mock_db = MagicMock()
        service = RAGAnalyticsService(mock_db)

        now = datetime.utcnow()
        metrics = AggregatedMetrics(
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_queries=100,
            avg_latency_ms=600.0,  # High latency
            p95_latency_ms=1200.0,  # Very high p95
            cache_hit_rate=65.0,
            avg_relevance_score=0.8,
        )

        health = service._assess_health(metrics)

        assert health["status"] == "degraded"
        assert any("latency" in w.lower() for w in health["warnings"])

    def test_assess_health_low_cache_rate_warning(self):
        """Test warning for low cache hit rate."""
        mock_db = MagicMock()
        service = RAGAnalyticsService(mock_db)

        now = datetime.utcnow()
        metrics = AggregatedMetrics(
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_queries=100,
            avg_latency_ms=150.0,
            p95_latency_ms=250.0,
            cache_hit_rate=20.0,  # Low cache rate
            avg_relevance_score=0.8,
        )

        health = service._assess_health(metrics)

        assert any("cache" in w.lower() for w in health["warnings"])

    def test_assess_health_low_relevance_degraded(self):
        """Test degraded status for low relevance score."""
        mock_db = MagicMock()
        service = RAGAnalyticsService(mock_db)

        now = datetime.utcnow()
        metrics = AggregatedMetrics(
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_queries=100,
            avg_latency_ms=150.0,
            p95_latency_ms=250.0,
            cache_hit_rate=65.0,
            avg_relevance_score=0.3,  # Low relevance
        )

        health = service._assess_health(metrics)

        assert health["status"] == "degraded"
        assert any("relevance" in w.lower() for w in health["warnings"])


class TestQueryTimer:
    """Tests for QueryTimer context manager."""

    @pytest.mark.asyncio
    async def test_query_timer_records_metrics(self):
        """Test that QueryTimer records metrics correctly."""
        async with QueryTimer("search", "user-1") as timer:
            timer.record_embedding(50.0, cache_hit=True)
            timer.record_search(30.0, results=5, avg_score=0.85)

        metrics = timer.get_metrics()

        assert metrics.query_type == "search"
        assert metrics.user_id == "user-1"
        assert metrics.embedding_ms == 50.0
        assert metrics.search_ms == 30.0
        assert metrics.cache_hit is True
        assert metrics.results_count == 5
        assert metrics.avg_score == 0.85

    @pytest.mark.asyncio
    async def test_query_timer_calculates_total_time(self):
        """Test that QueryTimer calculates total time."""
        async with QueryTimer("search", "user-1") as timer:
            pass  # Just timing the context

        metrics = timer.get_metrics()

        assert metrics.total_ms >= 0

    def test_query_timer_generates_unique_id(self):
        """Test that each QueryTimer gets a unique ID."""
        timer1 = QueryTimer("search", "user-1")
        timer2 = QueryTimer("search", "user-1")

        assert timer1.query_id != timer2.query_id


class TestMetricsAggregation:
    """Tests for metrics aggregation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_metrics_empty_period(self, mock_db):
        """Test getting metrics for empty period."""
        mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(all=lambda: []))

        service = RAGAnalyticsService(mock_db)
        now = datetime.utcnow()

        metrics = await service.get_metrics_for_period(
            now - timedelta(hours=1),
            now,
        )

        assert metrics.total_queries == 0
        assert metrics.avg_latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_get_daily_report_structure(self, mock_db):
        """Test daily report has correct structure."""
        mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(all=lambda: []))

        service = RAGAnalyticsService(mock_db)

        report = await service.get_daily_report()

        assert "date" in report
        assert "metrics" in report
        assert "breakdown" in report
        assert "trends" in report
        assert "health" in report
