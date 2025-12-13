"""Integration tests for Analytics API endpoints.

Tests cover:
- Analytics overview endpoint
- Daily report endpoint
- Cache stats endpoint
- System health endpoint
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestAnalyticsOverviewEndpoint:
    """Tests for GET /api/analytics endpoint."""

    def test_analytics_overview_rag_disabled(self, client):
        """Test that overview returns disabled message when RAG is off."""
        with patch("src.api.analytics.settings") as mock_settings:
            mock_settings.rag_enabled = False

            response = client.get("/api/analytics/")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False

    def test_analytics_overview_success(self, client):
        """Test successful analytics overview."""
        mock_report = {
            "metrics": {
                "total_queries": 100,
                "avg_latency_ms": 150.0,
                "cache_hit_rate": 65.0,
            },
            "health": {
                "status": "healthy",
                "warnings": [],
            },
        }

        with (
            patch("src.api.analytics.settings") as mock_settings,
            patch("src.api.analytics.get_rag_analytics_service") as mock_service,
        ):
            mock_settings.rag_enabled = True
            mock_instance = MagicMock()
            mock_instance.get_daily_report = AsyncMock(return_value=mock_report)
            mock_service.return_value = mock_instance

            response = client.get("/api/analytics/")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["daily_summary"]["queries"] == 100


class TestDailyReportEndpoint:
    """Tests for GET /api/analytics/daily endpoint."""

    def test_daily_report_rag_disabled(self, client):
        """Test that daily report returns 503 when RAG is disabled."""
        with patch("src.api.analytics.settings") as mock_settings:
            mock_settings.rag_enabled = False

            response = client.get("/api/analytics/daily")

            assert response.status_code == 503

    def test_daily_report_invalid_date(self, client):
        """Test that invalid date format returns 422 (validation error)."""
        with patch("src.api.analytics.settings") as mock_settings:
            mock_settings.rag_enabled = True

            response = client.get("/api/analytics/daily?date=invalid")

            # FastAPI returns 422 for validation errors (pattern mismatch)
            assert response.status_code == 422

    def test_daily_report_success(self, client):
        """Test successful daily report."""
        mock_report = {
            "date": "2025-01-01",
            "metrics": {
                "total_queries": 100,
                "avg_latency_ms": 150.0,
                "p95_latency_ms": 300.0,
                "cache_hit_rate": 65.0,
                "avg_results_count": 5.0,
                "avg_relevance_score": 0.85,
            },
            "breakdown": {"search": 80, "context": 20},
            "trends": {"latency_change_pct": -5.0, "query_change_pct": 10.0},
            "health": {"status": "healthy", "warnings": [], "thresholds": {}},
        }

        with (
            patch("src.api.analytics.settings") as mock_settings,
            patch("src.api.analytics.get_rag_analytics_service") as mock_service,
        ):
            mock_settings.rag_enabled = True
            mock_instance = MagicMock()
            mock_instance.get_daily_report = AsyncMock(return_value=mock_report)
            mock_service.return_value = mock_instance

            response = client.get("/api/analytics/daily?date=2025-01-01")

            assert response.status_code == 200
            data = response.json()
            assert data["metrics"]["total_queries"] == 100


class TestCacheStatsEndpoint:
    """Tests for GET /api/analytics/cache endpoint."""

    def test_cache_stats_success(self, client):
        """Test successful cache stats retrieval."""
        mock_stats = {
            "status": "connected",
            "used_memory": "1.5MB",
            "used_memory_peak": "2MB",
            "keyspace_hits": 100,
            "keyspace_misses": 20,
            "hit_rate": 83.33,
        }

        with patch("src.api.analytics.get_cache_service") as mock_cache:
            mock_instance = MagicMock()
            mock_instance.get_stats = AsyncMock(return_value=mock_stats)
            mock_cache.return_value = mock_instance

            response = client.get("/api/analytics/cache")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "connected"
            assert data["hit_rate"] == 83.33

    def test_cache_stats_error(self, client):
        """Test cache stats when Redis is unavailable."""
        with patch("src.api.analytics.get_cache_service") as mock_cache:
            mock_cache.side_effect = Exception("Connection refused")

            response = client.get("/api/analytics/cache")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


class TestSystemHealthEndpoint:
    """Tests for GET /api/analytics/health endpoint."""

    def test_system_health_all_healthy(self, client):
        """Test system health when all components are healthy."""
        mock_cache_stats = {
            "status": "connected",
            "hit_rate": 65.0,
        }
        mock_report = {
            "health": {
                "status": "healthy",
                "warnings": [],
            },
        }

        with (
            patch("src.api.analytics.settings") as mock_settings,
            patch("src.api.analytics.get_cache_service") as mock_cache,
            patch("src.api.analytics.get_rag_analytics_service") as mock_service,
        ):
            mock_settings.rag_enabled = True

            mock_cache_instance = MagicMock()
            mock_cache_instance.get_stats = AsyncMock(return_value=mock_cache_stats)
            mock_cache.return_value = mock_cache_instance

            mock_service_instance = MagicMock()
            mock_service_instance.get_daily_report = AsyncMock(return_value=mock_report)
            mock_service.return_value = mock_service_instance

            response = client.get("/api/analytics/health")

            assert response.status_code == 200
            data = response.json()
            assert data["cache_status"] == "connected"
            assert data["rag_health"] == "healthy"

    def test_system_health_cache_disconnected(self, client):
        """Test system health when cache is disconnected."""
        with (
            patch("src.api.analytics.settings") as mock_settings,
            patch("src.api.analytics.get_cache_service") as mock_cache,
        ):
            mock_settings.rag_enabled = False
            mock_cache.side_effect = Exception("Connection refused")

            response = client.get("/api/analytics/health")

            assert response.status_code == 200
            data = response.json()
            assert data["cache_status"] == "error"
            assert len(data["warnings"]) > 0


class TestHourlyBreakdownEndpoint:
    """Tests for GET /api/analytics/hourly endpoint."""

    def test_hourly_breakdown_rag_disabled(self, client):
        """Test that hourly breakdown returns 503 when RAG is disabled."""
        with patch("src.api.analytics.settings") as mock_settings:
            mock_settings.rag_enabled = False

            response = client.get("/api/analytics/hourly")

            assert response.status_code == 503

    def test_hourly_breakdown_success(self, client):
        """Test successful hourly breakdown."""
        mock_hourly = [
            {"hour": 0, "queries": 5, "avg_latency_ms": 100.0, "cache_hit_rate": 60.0},
            {"hour": 1, "queries": 3, "avg_latency_ms": 120.0, "cache_hit_rate": 55.0},
        ]

        with (
            patch("src.api.analytics.settings") as mock_settings,
            patch("src.api.analytics.get_rag_analytics_service") as mock_service,
        ):
            mock_settings.rag_enabled = True
            mock_instance = MagicMock()
            mock_instance.get_hourly_breakdown = AsyncMock(return_value=mock_hourly)
            mock_service.return_value = mock_instance

            response = client.get("/api/analytics/hourly")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["hour"] == 0


class TestCacheClearEndpoint:
    """Tests for DELETE /api/analytics/cache/pattern endpoint."""

    def test_clear_cache_pattern_success(self, client):
        """Test successful cache pattern clearing."""
        with patch("src.api.analytics.get_cache_service") as mock_cache:
            mock_instance = MagicMock()
            mock_instance.clear_pattern = AsyncMock(return_value=5)
            mock_cache.return_value = mock_instance

            response = client.delete("/api/analytics/cache/pattern/emb:*")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["deleted_count"] == 5

    def test_clear_cache_pattern_error(self, client):
        """Test cache pattern clearing with error."""
        with patch("src.api.analytics.get_cache_service") as mock_cache:
            mock_cache.side_effect = Exception("Redis error")

            response = client.delete("/api/analytics/cache/pattern/emb:*")

            assert response.status_code == 500
