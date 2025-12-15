"""API Deprecation Warning Middleware.

This module provides middleware for handling deprecated API endpoints.
It adds deprecation headers to responses when old API paths are used.

Headers added:
    Deprecation: true
    Sunset: <date when old API will be removed>
    Link: <link to new API version>

Example:
    >>> from src.middleware.deprecation import DeprecationMiddleware
    >>> app.add_middleware(DeprecationMiddleware, sunset_date="2025-06-01")
"""

from collections.abc import Callable
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import get_logger

logger = get_logger(__name__)


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Middleware to add deprecation warnings for old API paths.

    Detects requests to deprecated /api/* paths (not /api/v1/*) and adds
    deprecation headers to inform clients they should migrate.

    Attributes:
        sunset_date: ISO date when deprecated API will be removed.
        deprecated_prefix: URL prefix for deprecated routes.
        new_prefix: URL prefix for new versioned routes.

    Example:
        >>> app.add_middleware(
        ...     DeprecationMiddleware,
        ...     sunset_date="2025-06-01",
        ... )
    """

    def __init__(
        self,
        app: Callable,
        sunset_date: str = "2025-06-01",
        deprecated_prefix: str = "/api/",
        new_prefix: str = "/api/v1/",
    ) -> None:
        """Initialize the deprecation middleware.

        Args:
            app: The ASGI application.
            sunset_date: ISO date when deprecated API will be removed.
            deprecated_prefix: URL prefix for deprecated routes.
            new_prefix: URL prefix for new versioned routes.
        """
        super().__init__(app)
        self.sunset_date = sunset_date
        self.deprecated_prefix = deprecated_prefix
        self.new_prefix = new_prefix
        self._sunset_datetime = datetime.fromisoformat(sunset_date)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add deprecation headers if needed.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response with deprecation headers if using deprecated path.
        """
        response = await call_next(request)

        # Check if request is to deprecated API path
        path = request.url.path
        if self._is_deprecated_path(path):
            self._add_deprecation_headers(response, path)

        return response

    def _is_deprecated_path(self, path: str) -> bool:
        """Check if the path is deprecated.

        A path is deprecated if it starts with /api/ but not /api/v1/.
        Health endpoints and metrics are excluded.

        Args:
            path: The request URL path.

        Returns:
            True if the path is deprecated.
        """
        # Skip non-API paths
        if not path.startswith(self.deprecated_prefix):
            return False

        # Skip already versioned paths
        if path.startswith(self.new_prefix):
            return False

        # Skip health and metrics endpoints
        excluded = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if any(path.startswith(exc) or path == exc for exc in excluded):
            return False

        return True

    def _add_deprecation_headers(self, response: Response, path: str) -> None:
        """Add deprecation headers to the response.

        Args:
            response: The HTTP response to modify.
            path: The deprecated request path.
        """
        # Standard deprecation headers
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = self._sunset_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Link to new API version
        new_path = path.replace(self.deprecated_prefix, self.new_prefix, 1)
        response.headers["Link"] = f'<{new_path}>; rel="successor-version"'

        # Custom header with migration info
        response.headers["X-API-Deprecation-Info"] = (
            f"This endpoint is deprecated. Please migrate to {self.new_prefix}. "
            f"This endpoint will be removed after {self.sunset_date}."
        )

        logger.warning(
            "Deprecated API endpoint accessed",
            path=path,
            new_path=new_path,
            sunset_date=self.sunset_date,
        )


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API version headers.

    Supports version selection via headers:
    - X-API-Version: 1 (explicit version)
    - Accept: application/vnd.moneyflow.v1+json

    Attributes:
        default_version: Default API version when not specified.
        supported_versions: List of supported API versions.

    Example:
        >>> app.add_middleware(
        ...     APIVersionMiddleware,
        ...     default_version="1",
        ...     supported_versions=["1"],
        ... )
    """

    def __init__(
        self,
        app: Callable,
        default_version: str = "1",
        supported_versions: list[str] | None = None,
    ) -> None:
        """Initialize the API version middleware.

        Args:
            app: The ASGI application.
            default_version: Default API version when not specified.
            supported_versions: List of supported API versions.
        """
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = supported_versions or ["1"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle version headers.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response with API version header.
        """
        # Extract version from headers
        version = self._get_requested_version(request)

        # Store version in request state for route handlers
        request.state.api_version = version

        response = await call_next(request)

        # Add version to response headers
        response.headers["X-API-Version"] = version
        response.headers["X-API-Supported-Versions"] = ", ".join(self.supported_versions)

        return response

    def _get_requested_version(self, request: Request) -> str:
        """Extract requested API version from headers.

        Checks in order:
        1. X-API-Version header
        2. Accept header (application/vnd.moneyflow.v{N}+json)
        3. Default version

        Args:
            request: The incoming HTTP request.

        Returns:
            The requested API version string.
        """
        # Check X-API-Version header
        version_header = request.headers.get("X-API-Version")
        if version_header and version_header in self.supported_versions:
            return version_header

        # Check Accept header for vendor MIME type
        accept_header = request.headers.get("Accept", "")
        if "application/vnd.moneyflow.v" in accept_header:
            # Extract version from "application/vnd.moneyflow.v1+json"
            try:
                version_part = accept_header.split("vnd.moneyflow.v")[1]
                version = version_part.split("+")[0]
                if version in self.supported_versions:
                    return version
            except (IndexError, ValueError):
                pass

        return self.default_version
