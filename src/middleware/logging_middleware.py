"""Request/Response logging middleware.

This middleware provides comprehensive request/response logging with:
- Unique request ID generation and propagation
- Request timing (latency measurement)
- User context from authentication
- Configurable path exclusions (e.g., health checks)
- Slow request warnings

Usage:
    from src.middleware.logging_middleware import RequestLoggingMiddleware

    app.add_middleware(RequestLoggingMiddleware)
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import bind_request_context, clear_request_context, get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


logger = get_logger(__name__)

# Paths to exclude from request logging (reduce noise)
EXCLUDED_PATHS: set[str] = {
    "/health",
    "/health/live",
    "/health/ready",
    "/metrics",
    "/favicon.ico",
}

# Threshold for slow request warnings (in seconds)
SLOW_REQUEST_THRESHOLD = 1.0


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses.

    Features:
    - Generates unique request IDs for tracing
    - Measures request duration
    - Logs request method, path, status code
    - Adds user context for authenticated requests
    - Warns on slow requests (> 1 second)
    - Excludes health check and metrics endpoints

    Example:
        >>> app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log relevant information.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The HTTP response.
        """
        # Skip logging for excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract user_id from request state if available (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Bind context for all logs in this request
        bind_request_context(request_id=request_id, user_id=user_id)

        # Add request ID to response headers for client-side correlation
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log response
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "content_length": response.headers.get("content-length"),
            }

            # Determine log level based on status and duration
            if response.status_code >= 500:
                logger.error("Request failed", **log_data)
            elif response.status_code >= 400:
                logger.warning("Request client error", **log_data)
            elif duration_ms > SLOW_REQUEST_THRESHOLD * 1000:
                logger.warning("Slow request completed", **log_data)
            else:
                logger.info("Request completed", **log_data)

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request exception",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error=str(e),
            )
            raise
        finally:
            # Clear context to prevent leaking to other requests
            clear_request_context()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxy headers.

        Args:
            request: The HTTP request.

        Returns:
            The client IP address.
        """
        # Check for forwarded header (reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"


__all__ = ["RequestLoggingMiddleware"]
