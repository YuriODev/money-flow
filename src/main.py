"""FastAPI Application Entry Point.

This module configures and creates the FastAPI application instance,
including middleware, routers, and lifecycle management.

The application provides:
- REST API for subscription CRUD operations
- Natural language agent interface using Claude Haiku 4.5
- Health check endpoint for container orchestration

Access URLs (default):
- API: http://localhost:8001
- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import agent, analytics, auth, calendar, cards, insights, search, subscriptions
from src.core.config import settings
from src.db.database import init_db
from src.services.cache_service import close_cache_service, get_cache_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown.

    Manages application lifecycle events:
    - Startup: Initializes database tables
    - Shutdown: Placeholder for cleanup (connection pools, etc.)

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.

    Example:
        >>> app = FastAPI(lifespan=lifespan)
    """
    # Startup
    await init_db()
    # Initialize cache service (Redis)
    await get_cache_service()
    yield
    # Shutdown - cleanup connections
    await close_cache_service()


app = FastAPI(
    title="Subscription Tracker",
    description="Track subscriptions and recurring payments with an agentic interface",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
