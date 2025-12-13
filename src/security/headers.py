"""Security headers middleware for FastAPI.

This module provides middleware that adds security headers to all HTTP responses.
These headers help protect against common web vulnerabilities like XSS, clickjacking,
MIME type sniffing, and more.

Sprint 1.2.4 - Security Headers

Headers Added:
    - X-Content-Type-Options: nosniff (prevent MIME type sniffing)
    - X-Frame-Options: DENY (prevent clickjacking)
    - X-XSS-Protection: 1; mode=block (legacy XSS protection)
    - Strict-Transport-Security: max-age=... (enforce HTTPS)
    - Content-Security-Policy: ... (prevent XSS/injection)
    - Referrer-Policy: strict-origin-when-cross-origin (control referrer info)
    - Permissions-Policy: ... (control browser features)
    - Cache-Control: no-store (prevent sensitive data caching)

Example:
    >>> from fastapi import FastAPI
    >>> from src.security.headers import SecurityHeadersMiddleware
    >>>
    >>> app = FastAPI()
    >>> app.add_middleware(SecurityHeadersMiddleware)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.config import settings

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all HTTP responses.

    This middleware adds various security headers to protect against common
    web vulnerabilities. Headers are configurable based on environment.

    Attributes:
        hsts_enabled: Whether to enable HSTS (HTTPS enforcement).
        hsts_max_age: HSTS max-age in seconds (default: 1 year).
        csp_enabled: Whether to enable Content-Security-Policy.
        csp_report_only: Use report-only CSP (for testing).

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> app.add_middleware(
        ...     SecurityHeadersMiddleware,
        ...     hsts_enabled=True,
        ...     csp_enabled=True
        ... )
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        csp_enabled: bool = True,
        csp_report_only: bool = False,
    ) -> None:
        """Initialize security headers middleware.

        Args:
            app: ASGI application to wrap.
            hsts_enabled: Enable HSTS header (disable in dev with HTTP).
            hsts_max_age: HSTS max-age in seconds.
            csp_enabled: Enable Content-Security-Policy header.
            csp_report_only: Use CSP in report-only mode.
        """
        super().__init__(app)
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age = hsts_max_age
        self.csp_enabled = csp_enabled
        self.csp_report_only = csp_report_only

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in chain.

        Returns:
            Response with security headers added.
        """
        response: Response = await call_next(request)

        # Always add these headers
        self._add_basic_headers(response)

        # Conditionally add HSTS (only in production with HTTPS)
        if self.hsts_enabled and not settings.debug:
            self._add_hsts_header(response)

        # Conditionally add CSP
        if self.csp_enabled:
            self._add_csp_header(response)

        # Add cache control for API responses (prevent caching sensitive data)
        if request.url.path.startswith("/api/"):
            self._add_api_cache_headers(response)

        return response

    def _add_basic_headers(self, response: Response) -> None:
        """Add basic security headers that should always be present.

        Args:
            response: Response to add headers to.
        """
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking - deny framing from any origin
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (most modern browsers ignore this)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information sent to other origins
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features/APIs
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Prevent DNS prefetching
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Prevent download sniffing in IE
        response.headers["X-Download-Options"] = "noopen"

        # Prevent browser from detecting file types
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    def _add_hsts_header(self, response: Response) -> None:
        """Add HSTS header to enforce HTTPS.

        Args:
            response: Response to add header to.
        """
        # Strict-Transport-Security tells browsers to only use HTTPS
        # includeSubDomains extends this to all subdomains
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains"
        )

    def _add_csp_header(self, response: Response) -> None:
        """Add Content-Security-Policy header.

        This CSP is configured for a typical API backend:
        - default-src 'self': Only allow resources from same origin
        - script-src 'self': Only allow scripts from same origin
        - style-src 'self' 'unsafe-inline': Allow inline styles for Swagger UI
        - img-src 'self' data: https:: Allow images from self, data URIs, HTTPS
        - font-src 'self': Only allow fonts from same origin
        - object-src 'none': Disallow plugins (Flash, Java, etc.)
        - base-uri 'self': Restrict base tag to same origin
        - form-action 'self': Restrict form submissions to same origin
        - frame-ancestors 'none': Same as X-Frame-Options: DENY

        Args:
            response: Response to add header to.
        """
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # For Swagger UI
            "style-src 'self' 'unsafe-inline'",  # For Swagger UI
            "img-src 'self' data: https:",
            "font-src 'self' https://fonts.gstatic.com",  # For web fonts
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
        ]

        csp_value = "; ".join(csp_directives)

        if self.csp_report_only:
            response.headers["Content-Security-Policy-Report-Only"] = csp_value
        else:
            response.headers["Content-Security-Policy"] = csp_value

    def _add_api_cache_headers(self, response: Response) -> None:
        """Add cache control headers for API responses.

        Prevents caching of sensitive API data.

        Args:
            response: Response to add headers to.
        """
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"


def get_security_headers_middleware() -> type[SecurityHeadersMiddleware]:
    """Get the security headers middleware class.

    Returns:
        SecurityHeadersMiddleware class configured based on settings.

    Example:
        >>> middleware_class = get_security_headers_middleware()
        >>> app.add_middleware(middleware_class)
    """
    return SecurityHeadersMiddleware


# Default configuration based on environment
DEFAULT_HSTS_ENABLED = not settings.debug
DEFAULT_CSP_ENABLED = True
DEFAULT_CSP_REPORT_ONLY = settings.debug  # Report-only in development


__all__ = [
    "SecurityHeadersMiddleware",
    "get_security_headers_middleware",
    "DEFAULT_HSTS_ENABLED",
    "DEFAULT_CSP_ENABLED",
    "DEFAULT_CSP_REPORT_ONLY",
]
