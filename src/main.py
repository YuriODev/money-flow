"""FastAPI Application Entry Point.

This module configures and creates the FastAPI application instance,
including middleware, routers, and lifecycle management.

The application provides:
- REST API for subscription CRUD operations
- Natural language agent interface using Claude Haiku 4.5
- Health check endpoint for container orchestration
- Rate limiting for API protection
- Security headers (XSS, clickjacking, HSTS, CSP)

Access URLs (default):
- API: http://localhost:8001
- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api import agent, analytics, auth, calendar, cards, insights, search, subscriptions
from src.core.config import settings
from src.db.database import init_db
from src.security.headers import SecurityHeadersMiddleware
from src.security.rate_limit import limiter
from src.security.secrets_validator import validate_secrets
from src.services.cache_service import close_cache_service, get_cache_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown.

    Manages application lifecycle events:
    - Startup: Validates secrets, initializes database tables
    - Shutdown: Cleanup connections

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.

    Example:
        >>> app = FastAPI(lifespan=lifespan)
    """
    # Startup
    # Validate secrets configuration (logs warnings, blocks in production if invalid)
    secrets_result = validate_secrets()
    if not secrets_result.is_valid and not settings.debug:
        raise RuntimeError(
            "Security validation failed. Fix configuration errors or set DEBUG=true. "
            f"Errors: {'; '.join(secrets_result.errors)}"
        )

    await init_db()
    # Initialize cache service (Redis)
    await get_cache_service()

    logger.info("Application startup complete")
    yield

    # Shutdown - cleanup connections
    await close_cache_service()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Subscription Tracker",
    description="Track subscriptions and recurring payments with an agentic interface",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting - attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware (XSS, clickjacking, HSTS, CSP)
# Note: Must be added before CORS middleware to ensure headers are applied
app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_enabled=not settings.debug,  # Only enable HSTS in production
    csp_enabled=True,
    csp_report_only=settings.debug,  # Report-only in development
)


# CORS middleware for frontend communication
# Security hardened: No wildcards in production, specific methods and headers only
def _validate_cors_origins(origins: list[str]) -> list[str]:
    """Validate CORS origins for security."""
    validated = []
    for origin in origins:
        # Block wildcards in production mode
        if "*" in origin and not settings.debug:
            logger.warning(f"Blocked wildcard CORS origin in production: {origin}")
            continue
        validated.append(origin)
    return validated


app.add_middleware(
    CORSMiddleware,
    allow_origins=_validate_cors_origins(settings.cors_origins),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    max_age=settings.cors_max_age,
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(cards.router, prefix="/api", tags=["cards"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration.

    Used by Docker, Kubernetes, and load balancers to verify
    the application is running and ready to accept requests.

    Returns:
        Dictionary with status key indicating health.

    Example:
        GET /health
        Response: {"status": "healthy"}
    """
    return {"status": "healthy"}


def run() -> None:
    """Run the application with uvicorn development server.

    Starts the FastAPI application using uvicorn with settings
    from environment configuration. Enables hot-reload in debug mode.

    Returns:
        None (runs until interrupted).

    Example:
        >>> run()  # Starts server on configured host:port
    """
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
