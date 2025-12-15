"""Unit tests for API versioning middleware.

Tests for:
- DeprecationMiddleware: Deprecation headers for old API paths
- APIVersionMiddleware: Version header handling
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.middleware.deprecation import APIVersionMiddleware, DeprecationMiddleware


class TestDeprecationMiddleware:
    """Tests for DeprecationMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = MagicMock()
        return DeprecationMiddleware(
            app,
            sunset_date="2025-06-01",
            deprecated_prefix="/api/",
            new_prefix="/api/v1/",
        )

    def test_init_sets_sunset_date(self, middleware):
        """Test that sunset date is properly set."""
        assert middleware.sunset_date == "2025-06-01"

    def test_is_deprecated_path_old_api(self, middleware):
        """Test that /api/subscriptions is deprecated."""
        assert middleware._is_deprecated_path("/api/subscriptions") is True

    def test_is_deprecated_path_versioned_api(self, middleware):
        """Test that /api/v1/subscriptions is not deprecated."""
        assert middleware._is_deprecated_path("/api/v1/subscriptions") is False

    def test_is_deprecated_path_health(self, middleware):
        """Test that /health is not deprecated."""
        assert middleware._is_deprecated_path("/health") is False

    def test_is_deprecated_path_docs(self, middleware):
        """Test that /docs is not deprecated."""
        assert middleware._is_deprecated_path("/docs") is False

    def test_is_deprecated_path_metrics(self, middleware):
        """Test that /metrics is not deprecated."""
        assert middleware._is_deprecated_path("/metrics") is False

    def test_is_deprecated_path_non_api(self, middleware):
        """Test that non-API paths are not deprecated."""
        assert middleware._is_deprecated_path("/some/other/path") is False

    @pytest.mark.asyncio
    async def test_dispatch_adds_headers_for_deprecated_path(self, middleware):
        """Test that deprecation headers are added for deprecated paths."""
        request = MagicMock()
        request.url.path = "/api/subscriptions"

        response = MagicMock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert result.headers["Deprecation"] == "true"
        assert "Sunset" in result.headers
        assert "Link" in result.headers
        assert "/api/v1/subscriptions" in result.headers["Link"]

    @pytest.mark.asyncio
    async def test_dispatch_no_headers_for_versioned_path(self, middleware):
        """Test that no deprecation headers are added for versioned paths."""
        request = MagicMock()
        request.url.path = "/api/v1/subscriptions"

        response = MagicMock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert "Deprecation" not in result.headers


class TestAPIVersionMiddleware:
    """Tests for APIVersionMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = MagicMock()
        return APIVersionMiddleware(
            app,
            default_version="1",
            supported_versions=["1"],
        )

    def test_init_sets_default_version(self, middleware):
        """Test that default version is set."""
        assert middleware.default_version == "1"

    def test_init_sets_supported_versions(self, middleware):
        """Test that supported versions are set."""
        assert "1" in middleware.supported_versions

    def test_get_requested_version_default(self, middleware):
        """Test that default version is returned when no header."""
        request = MagicMock()
        request.headers = {}

        version = middleware._get_requested_version(request)

        assert version == "1"

    def test_get_requested_version_from_header(self, middleware):
        """Test that version is extracted from X-API-Version header."""
        request = MagicMock()
        request.headers = {"X-API-Version": "1"}

        version = middleware._get_requested_version(request)

        assert version == "1"

    def test_get_requested_version_invalid_header(self, middleware):
        """Test that default is returned for invalid version header."""
        request = MagicMock()
        request.headers = {"X-API-Version": "99"}

        version = middleware._get_requested_version(request)

        assert version == "1"

    def test_get_requested_version_from_accept_header(self, middleware):
        """Test that version is extracted from Accept header."""
        request = MagicMock()
        request.headers = {
            "Accept": "application/vnd.moneyflow.v1+json",
        }

        version = middleware._get_requested_version(request)

        assert version == "1"

    @pytest.mark.asyncio
    async def test_dispatch_adds_version_headers(self, middleware):
        """Test that version headers are added to response."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock()

        response = MagicMock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert result.headers["X-API-Version"] == "1"
        assert "X-API-Supported-Versions" in result.headers

    @pytest.mark.asyncio
    async def test_dispatch_sets_request_state(self, middleware):
        """Test that API version is set in request state."""
        request = MagicMock()
        request.headers = {}
        request.state = MagicMock()

        response = MagicMock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        await middleware.dispatch(request, call_next)

        assert request.state.api_version == "1"


class TestV1Router:
    """Tests for v1 router configuration."""

    def test_v1_router_exists(self):
        """Test that v1 router can be imported."""
        from src.api.v1 import v1_router

        assert v1_router is not None

    def test_v1_router_has_routes(self):
        """Test that v1 router has routes configured."""
        from src.api.v1 import v1_router

        # Check that routes are registered
        assert len(v1_router.routes) > 0
