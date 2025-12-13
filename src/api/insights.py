"""Insights API endpoints for spending analysis and recommendations.

This module provides REST API endpoints for subscription insights,
including spending trends, category breakdowns, renewal predictions,
and optimization recommendations.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.security.input_sanitizer import sanitize_input
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.historical_query_service import (
    get_historical_query_service,
)
from src.services.insights_service import get_insights_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class SpendingTrendResponse(BaseModel):
    """Spending trend for a period."""

    period: str
    total: float
    change: float
    change_percent: float
    subscription_count: int


class CategoryBreakdownResponse(BaseModel):
    """Category spending breakdown."""

    category: str
    total: float
    percentage: float
    subscription_count: int
    subscriptions: list[str]


class RenewalPredictionResponse(BaseModel):
    """Upcoming renewal prediction."""

    subscription_name: str
    subscription_id: str
    renewal_date: str
    amount: float
    days_until: int
    is_annual: bool


class RecommendationResponse(BaseModel):
    """Cancellation/optimization recommendation."""

    subscription_name: str
    subscription_id: str
    reason: str
    potential_savings: float
    confidence: float


class InsightsResponse(BaseModel):
    """Complete insights response."""

    total_monthly: float
    total_yearly: float
    trends: list[SpendingTrendResponse]
    category_breakdown: list[CategoryBreakdownResponse]
    renewal_predictions: list[RenewalPredictionResponse]
    recommendations: list[RecommendationResponse]
    summary: str


class CostComparisonResponse(BaseModel):
    """Cost comparison across time periods."""

    daily: float
    weekly: float
    monthly: float
    quarterly: float
    yearly: float
    subscription_count: int


class HistoricalQueryRequest(BaseModel):
    """Request for historical query."""

    query: str = Field(
        ...,
        description="Natural language query with temporal expression",
        examples=[
            "What did I add last month?",
            "Show subscriptions from January",
            "How much was I spending in 2024?",
        ],
    )


class HistoricalSubscriptionResponse(BaseModel):
    """Historical subscription data."""

    id: str
    name: str
    amount: float
    frequency: str
    category: str | None
    created_at: str
    was_active: bool


class HistoricalQueryResponse(BaseModel):
    """Response for historical query."""

    query: str
    date_range: dict[str, str]
    subscriptions: list[HistoricalSubscriptionResponse]
    total_monthly: float
    subscription_count: int
    summary: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/", response_model=InsightsResponse)
@limiter.limit(rate_limit_get)
async def get_insights(
    request: Request,
    months_back: int = Query(default=6, ge=1, le=24, description="Months of trend data"),
    db: AsyncSession = Depends(get_db),
) -> InsightsResponse:
    """Get comprehensive spending insights.

    Returns spending trends, category breakdown, renewal predictions,
    and optimization recommendations.

    Args:
        months_back: Number of months for trend analysis (1-24).
        db: Database session.

    Returns:
        InsightsResponse with all analysis data.

    Example:
        GET /api/insights?months_back=3

        Response:
        {
            "total_monthly": 150.99,
            "total_yearly": 1811.88,
            "trends": [...],
            "category_breakdown": [...],
            "recommendations": [...],
            "summary": "You're spending £150.99 per month..."
        }
    """
    try:
        service = get_insights_service(db)
        insights = await service.get_insights(months_back=months_back)

        return InsightsResponse(
            total_monthly=float(insights.total_monthly),
            total_yearly=float(insights.total_yearly),
            trends=[
                SpendingTrendResponse(
                    period=t.period,
                    total=float(t.total),
                    change=float(t.change),
                    change_percent=t.change_percent,
                    subscription_count=t.subscription_count,
                )
                for t in insights.trends
            ],
            category_breakdown=[
                CategoryBreakdownResponse(
                    category=c.category,
                    total=float(c.total),
                    percentage=c.percentage,
                    subscription_count=c.subscription_count,
                    subscriptions=c.subscriptions,
                )
                for c in insights.category_breakdown
            ],
            renewal_predictions=[
                RenewalPredictionResponse(
                    subscription_name=r.subscription_name,
                    subscription_id=r.subscription_id,
                    renewal_date=r.renewal_date.isoformat(),
                    amount=float(r.amount),
                    days_until=r.days_until,
                    is_annual=r.is_annual,
                )
                for r in insights.renewal_predictions
            ],
            recommendations=[
                RecommendationResponse(
                    subscription_name=r.subscription_name,
                    subscription_id=r.subscription_id,
                    reason=r.reason,
                    potential_savings=float(r.potential_savings),
                    confidence=r.confidence,
                )
                for r in insights.recommendations
            ],
            summary=insights.summary,
        )

    except Exception as e:
        logger.exception(f"Insights error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@router.get("/cost-comparison", response_model=CostComparisonResponse)
@limiter.limit(rate_limit_get)
async def get_cost_comparison(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CostComparisonResponse:
    """Get cost comparison across time periods.

    Returns spending totals for different time periods
    (daily, weekly, monthly, quarterly, yearly).

    Args:
        db: Database session.

    Returns:
        CostComparisonResponse with period totals.

    Example:
        GET /api/insights/cost-comparison

        Response:
        {
            "daily": 5.03,
            "weekly": 37.75,
            "monthly": 150.99,
            "quarterly": 452.97,
            "yearly": 1811.88,
            "subscription_count": 8
        }
    """
    try:
        service = get_insights_service(db)
        comparison = await service.get_cost_comparison()

        return CostComparisonResponse(
            daily=float(comparison["daily"]),
            weekly=float(comparison["weekly"]),
            monthly=float(comparison["monthly"]),
            quarterly=float(comparison["quarterly"]),
            yearly=float(comparison["yearly"]),
            subscription_count=comparison["subscription_count"],
        )

    except Exception as e:
        logger.exception(f"Cost comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/spending/{start_date}/{end_date}")
@limiter.limit(rate_limit_get)
async def get_spending_by_period(
    request: Request,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get spending breakdown for a specific period.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        db: Database session.

    Returns:
        Dictionary with spending data for the period.

    Example:
        GET /api/insights/spending/2025-01-01/2025-01-31

        Response:
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "days": 31,
            "total": 165.49,
            "by_subscription": [...]
        }
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date",
        )

    try:
        service = get_insights_service(db)
        return await service.get_spending_by_period(start_date, end_date)

    except Exception as e:
        logger.exception(f"Spending period error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/renewals")
@limiter.limit(rate_limit_get)
async def get_upcoming_renewals(
    request: Request,
    days: int = Query(default=30, ge=1, le=365, description="Days ahead to look"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get upcoming subscription renewals.

    Args:
        days: Number of days ahead to check (1-365).
        db: Database session.

    Returns:
        Dictionary with renewal predictions.

    Example:
        GET /api/insights/renewals?days=7

        Response:
        {
            "days_ahead": 7,
            "renewals": [...],
            "total_amount": 45.98,
            "count": 2
        }
    """
    try:
        service = get_insights_service(db)
        insights = await service.get_insights(months_back=1)

        # Filter renewals within the specified days
        renewals = [
            {
                "subscription_name": r.subscription_name,
                "subscription_id": r.subscription_id,
                "renewal_date": r.renewal_date.isoformat(),
                "amount": float(r.amount),
                "days_until": r.days_until,
                "is_annual": r.is_annual,
            }
            for r in insights.renewal_predictions
            if r.days_until <= days
        ]

        total = sum(r["amount"] for r in renewals)

        return {
            "days_ahead": days,
            "renewals": renewals,
            "total_amount": round(total, 2),
            "count": len(renewals),
        }

    except Exception as e:
        logger.exception(f"Renewals error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/recommendations")
@limiter.limit(rate_limit_get)
async def get_recommendations(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get optimization recommendations.

    Returns recommendations for potential cost savings,
    including duplicate subscriptions and high-cost items.

    Args:
        db: Database session.

    Returns:
        Dictionary with recommendations.

    Example:
        GET /api/insights/recommendations

        Response:
        {
            "recommendations": [...],
            "total_potential_savings": 25.99,
            "count": 2
        }
    """
    try:
        service = get_insights_service(db)
        insights = await service.get_insights(months_back=1)

        recommendations = [
            {
                "subscription_name": r.subscription_name,
                "subscription_id": r.subscription_id,
                "reason": r.reason,
                "potential_savings": float(r.potential_savings),
                "confidence": r.confidence,
            }
            for r in insights.recommendations
        ]

        total_savings = sum(r["potential_savings"] for r in recommendations)

        return {
            "recommendations": recommendations,
            "total_potential_savings": round(total_savings, 2),
            "count": len(recommendations),
        }

    except Exception as e:
        logger.exception(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/historical", response_model=HistoricalQueryResponse)
@limiter.limit(rate_limit_write)
async def query_historical(
    http_request: Request,
    request: HistoricalQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> HistoricalQueryResponse:
    """Execute a historical query with temporal parsing.

    Parses natural language time expressions and retrieves
    matching subscription data.

    Args:
        request: Query request with natural language query.
        db: Database session.

    Returns:
        HistoricalQueryResponse with matching data.

    Example:
        POST /api/insights/historical
        {"query": "What did I add last month?"}

        Response:
        {
            "query": "What did I add last month?",
            "date_range": {"start": "2025-10-01", "end": "2025-10-31", "label": "last month"},
            "subscriptions": [...],
            "summary": "Added 2 subscription(s) in last month: Netflix, Spotify"
        }
    """
    # Sanitize the natural language query
    sanitization_result = sanitize_input(request.query)
    if not sanitization_result.is_safe:
        logger.warning(f"Blocked historical query: {sanitization_result.blocked_reason}")
        raise HTTPException(
            status_code=400,
            detail="Invalid query. Please rephrase and try again.",
        )

    safe_query = sanitization_result.sanitized_input

    try:
        service = get_historical_query_service(db)
        result = await service.query(safe_query)

        return HistoricalQueryResponse(
            query=result.query,
            date_range={
                "start": result.date_range.start.isoformat(),
                "end": result.date_range.end.isoformat(),
                "label": result.date_range.label,
            },
            subscriptions=[
                HistoricalSubscriptionResponse(
                    id=s.id,
                    name=s.name,
                    amount=float(s.amount),
                    frequency=s.frequency,
                    category=s.category,
                    created_at=s.created_at.isoformat()
                    if isinstance(s.created_at, date)
                    else str(s.created_at),
                    was_active=s.was_active,
                )
                for s in result.subscriptions
            ],
            total_monthly=float(result.total_monthly),
            subscription_count=result.subscription_count,
            summary=result.summary,
        )

    except Exception as e:
        logger.exception(f"Historical query error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
