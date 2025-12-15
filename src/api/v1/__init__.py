"""API Version 1 Router.

This module aggregates all v1 API routes into a single versioned router.
All routes are prefixed with /api/v1/.

Endpoints:
    /api/v1/auth/* - Authentication endpoints
    /api/v1/subscriptions/* - Subscription CRUD operations
    /api/v1/calendar/* - Calendar and scheduling
    /api/v1/agent/* - AI agent interface
    /api/v1/search/* - Search functionality
    /api/v1/insights/* - Analytics insights
    /api/v1/analytics/* - Usage analytics
    /api/v1/cards/* - Payment card management

Example:
    >>> from src.api.v1 import v1_router
    >>> app.include_router(v1_router, prefix="/api/v1")
"""

from fastapi import APIRouter

from src.api import (
    agent,
    analytics,
    auth,
    calendar,
    cards,
    insights,
    search,
    subscriptions,
)

# Create the v1 router
v1_router = APIRouter()

# Include all API routes under v1
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
v1_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
v1_router.include_router(agent.router, prefix="/agent", tags=["agent"])
v1_router.include_router(search.router, prefix="/search", tags=["search"])
v1_router.include_router(insights.router, prefix="/insights", tags=["insights"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
v1_router.include_router(cards.router, tags=["cards"])

__all__ = ["v1_router"]
