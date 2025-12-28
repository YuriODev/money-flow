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
    ai_settings,
    analytics,
    auth,
    banks,
    calendar,
    cards,
    categories,
    currencies,
    export_history,
    icons,
    insights,
    search,
    statement_import,
    subscriptions,
    users,
    webhooks,
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
v1_router.include_router(categories.router, tags=["categories"])
v1_router.include_router(users.router, prefix="/users", tags=["users"])
v1_router.include_router(export_history.router, tags=["exports"])
v1_router.include_router(icons.router, prefix="/icons", tags=["icons"])
v1_router.include_router(ai_settings.router, prefix="/ai", tags=["ai-settings"])
v1_router.include_router(currencies.router, prefix="/currencies", tags=["currencies"])
v1_router.include_router(banks.router, tags=["banks"])
v1_router.include_router(statement_import.router, tags=["statement-import"])
v1_router.include_router(webhooks.router, tags=["webhooks"])

__all__ = ["v1_router"]
