"""FastAPI Application Entry Point.

This module configures and creates the FastAPI application instance,
including middleware, routers, and lifecycle management.

The application provides:
- REST API for subscription CRUD operations (versioned at /api/v1/)
- Natural language agent interface using Claude Haiku 4.5
- Health check endpoint for container orchestration
- Rate limiting for API protection
- Security headers (XSS, clickjacking, HSTS, CSP)
- Structured logging with request tracing
- API versioning with deprecation support

Access URLs (default):
- API v1: http://localhost:8001/api/v1
- Legacy API: http://localhost:8001/api (deprecated)
- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import agent, analytics, auth, calendar, cards, health, insights, search, subscriptions
from src.api.v1 import v1_router
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.core.metrics import setup_metrics
from src.core.sentry import init_sentry
from src.db.database import init_db
from src.middleware.deprecation import APIVersionMiddleware, DeprecationMiddleware
from src.middleware.exception_handler import setup_exception_handlers
from src.middleware.logging_middleware import RequestLoggingMiddleware
from src.security.headers import SecurityHeadersMiddleware
from src.security.rate_limit import limiter
from src.security.secrets_validator import validate_secrets
from src.services.cache_service import close_cache_service, get_cache_service
from src.services.rag_service import get_rag_service

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)

# Initialize Sentry error tracking (before FastAPI app creation)
init_sentry()


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
    cache = await get_cache_service()

    # Inject cache into RAG service for session persistence and embedding caching
    if settings.rag_enabled:
        rag_service = get_rag_service()
        rag_service.set_cache(cache)
        logger.info("RAG service configured with cache")

    logger.info("Application startup complete")
    yield

    # Shutdown - cleanup connections
    await close_cache_service()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Money Flow API",
    description=(
        "Track subscriptions and recurring payments with an agentic interface.\n\n"
        "## API Versioning\n"
        "The API is versioned. Current version: **v1**\n\n"
        "- Use `/api/v1/` prefix for all endpoints\n"
        "- Legacy `/api/` endpoints are deprecated and will be removed in v2\n"
        "- Set `X-API-Version: 1` header for explicit version selection\n\n"
        "## Authentication\n"
        "Most endpoints require JWT authentication. Include token in header:\n"
        "`Authorization: Bearer <token>`"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "auth", "description": "Authentication and authorization"},
        {"name": "subscriptions", "description": "Subscription CRUD operations"},
        {"name": "calendar", "description": "Calendar and scheduling"},
        {"name": "agent", "description": "AI agent natural language interface"},
        {"name": "search", "description": "Search functionality"},
        {"name": "insights", "description": "Analytics insights"},
        {"name": "analytics", "description": "Usage analytics"},
        {"name": "cards", "description": "Payment card management"},
    ],
)

# Rate limiting - attach limiter to app state
app.state.limiter = limiter


# Set up standardized exception handlers for consistent error responses
setup_exception_handlers(app)

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

# Request logging middleware (added last so it runs first)
# Provides request ID generation, timing, and structured logging
app.add_middleware(RequestLoggingMiddleware)

# API Version middleware - adds version headers to all responses
app.add_middleware(
    APIVersionMiddleware,
    default_version="1",
    supported_versions=["1"],
)

# Deprecation middleware - warns about deprecated /api/* paths
app.add_middleware(
    DeprecationMiddleware,
    sunset_date="2025-06-01",
    deprecated_prefix="/api/",
    new_prefix="/api/v1/",
)

# Include API routers
# Health checks at root level (not versioned)
app.include_router(health.router, tags=["health"])

# Versioned API routes (v1)
app.include_router(v1_router, prefix="/api/v1")

# Legacy routes (deprecated, will be removed in v2)
# These are kept for backward compatibility during migration period
app.include_router(auth.router, prefix="/api/auth", tags=["auth"], deprecated=True)
app.include_router(
    subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"], deprecated=True
)
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"], deprecated=True)
app.include_router(agent.router, prefix="/api/agent", tags=["agent"], deprecated=True)
app.include_router(search.router, prefix="/api/search", tags=["search"], deprecated=True)
app.include_router(insights.router, prefix="/api/insights", tags=["insights"], deprecated=True)
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"], deprecated=True)
app.include_router(cards.router, prefix="/api", tags=["cards"], deprecated=True)

# Set up Prometheus metrics (must be after all routers are added)
setup_metrics(app)


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
