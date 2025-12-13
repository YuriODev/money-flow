"""Insights service for spending pattern analysis and recommendations.

This module provides the InsightsService class for analyzing subscription
spending patterns, generating insights, and providing recommendations.

Features:
- Spending trend analysis (month-over-month changes)
- Category breakdown with percentages
- Renewal predictions and upcoming costs
- Cancellation recommendations based on usage patterns
- Cost optimization suggestions
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Frequency, Subscription

logger = logging.getLogger(__name__)


@dataclass
class SpendingTrend:
    """Spending trend data for a time period.

    Attributes:
        period: The period label (e.g., "2025-01", "January 2025").
        total: Total spending in the period.
        change: Change from previous period (can be negative).
        change_percent: Percentage change from previous period.
        subscription_count: Number of active subscriptions.
    """

    period: str
    total: Decimal
    change: Decimal = Decimal("0")
    change_percent: float = 0.0
    subscription_count: int = 0


@dataclass
class CategoryBreakdown:
    """Spending breakdown by category.

    Attributes:
        category: Category name.
        total: Total monthly spending in category.
        percentage: Percentage of total spending.
        subscription_count: Number of subscriptions in category.
        subscriptions: List of subscription names in category.
    """

    category: str
    total: Decimal
    percentage: float
    subscription_count: int
    subscriptions: list[str] = field(default_factory=list)


@dataclass
class RenewalPrediction:
    """Upcoming renewal prediction.

    Attributes:
        subscription_name: Name of the subscription.
        subscription_id: ID of the subscription.
        renewal_date: Expected renewal date.
        amount: Renewal amount.
        days_until: Days until renewal.
        is_annual: Whether this is an annual renewal.
    """

    subscription_name: str
    subscription_id: str
    renewal_date: date
    amount: Decimal
    days_until: int
    is_annual: bool = False


@dataclass
class CancellationRecommendation:
    """Cancellation recommendation based on analysis.

    Attributes:
        subscription_name: Name of the subscription.
        subscription_id: ID of the subscription.
        reason: Reason for recommendation.
        potential_savings: Monthly savings if cancelled.
        confidence: Confidence score (0-1).
    """

    subscription_name: str
    subscription_id: str
    reason: str
    potential_savings: Decimal
    confidence: float


@dataclass
class SpendingInsights:
    """Complete spending insights report.

    Attributes:
        total_monthly: Total monthly spending.
        total_yearly: Total yearly spending.
        trends: List of spending trends by month.
        category_breakdown: Spending by category.
        renewal_predictions: Upcoming renewals.
        recommendations: Cancellation/optimization recommendations.
        summary: Human-readable summary.
    """

    total_monthly: Decimal
    total_yearly: Decimal
    trends: list[SpendingTrend]
    category_breakdown: list[CategoryBreakdown]
    renewal_predictions: list[RenewalPrediction]
    recommendations: list[CancellationRecommendation]
    summary: str


class InsightsService:
    """Service for generating spending insights and recommendations.

    This service analyzes subscription data to provide actionable insights
    including spending trends, category breakdowns, and recommendations.

    Attributes:
        db: Async database session.

    Example:
        >>> service = InsightsService(db_session)
        >>> insights = await service.get_insights()
        >>> print(insights.summary)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the insights service.

        Args:
            db: Async database session.
        """
        self.db = db

    async def get_insights(self, months_back: int = 6) -> SpendingInsights:
        """Generate comprehensive spending insights.

        Analyzes all active subscriptions to generate trends, breakdowns,
        predictions, and recommendations.

        Args:
            months_back: Number of months to analyze for trends (default 6).

        Returns:
            SpendingInsights with all analysis data.

        Example:
            >>> insights = await service.get_insights(months_back=3)
            >>> print(f"Monthly: £{insights.total_monthly}")
        """
        subscriptions = await self._get_active_subscriptions()

        total_monthly = self._calculate_total_monthly(subscriptions)
        total_yearly = total_monthly * 12

        trends = self._analyze_trends(subscriptions, months_back)
        category_breakdown = self._analyze_categories(subscriptions, total_monthly)
        renewal_predictions = self._predict_renewals(subscriptions, days_ahead=30)
        recommendations = self._generate_recommendations(subscriptions)

        summary = self._generate_summary(
            total_monthly=total_monthly,
            trends=trends,
            category_breakdown=category_breakdown,
            recommendations=recommendations,
        )

        return SpendingInsights(
            total_monthly=total_monthly,
            total_yearly=total_yearly,
            trends=trends,
            category_breakdown=category_breakdown,
            renewal_predictions=renewal_predictions,
            recommendations=recommendations,
            summary=summary,
        )

    async def get_spending_by_period(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get spending breakdown for a specific period.

        Args:
            start_date: Start of the analysis period.
            end_date: End of the analysis period.

        Returns:
            Dictionary with spending data for the period.
        """
        subscriptions = await self._get_active_subscriptions()

        # Calculate days in period
        days = (end_date - start_date).days + 1

        # Calculate spending for the period
        total = Decimal("0")
        by_subscription = []

        for sub in subscriptions:
            daily_rate = self._to_daily_amount(sub.amount, sub.frequency)
            period_amount = daily_rate * days
            total += period_amount
            by_subscription.append(
                {
                    "name": sub.name,
                    "amount": round(period_amount, 2),
                    "category": sub.category or "uncategorized",
                }
            )

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "total": round(total, 2),
            "by_subscription": sorted(by_subscription, key=lambda x: x["amount"], reverse=True),
        }

    async def get_cost_comparison(self) -> dict[str, Any]:
        """Compare costs across different time periods.

        Returns:
            Dictionary with cost comparisons (daily, weekly, monthly, yearly).
        """
        subscriptions = await self._get_active_subscriptions()
        total_monthly = self._calculate_total_monthly(subscriptions)

        return {
            "daily": round(total_monthly / 30, 2),
            "weekly": round(total_monthly / 4, 2),
            "monthly": round(total_monthly, 2),
            "quarterly": round(total_monthly * 3, 2),
            "yearly": round(total_monthly * 12, 2),
            "subscription_count": len(subscriptions),
        }

    async def _get_active_subscriptions(self) -> list[Subscription]:
        """Get all active subscriptions.

        Returns:
            List of active Subscription objects.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    def _calculate_total_monthly(self, subscriptions: list[Subscription]) -> Decimal:
        """Calculate total monthly spending.

        Args:
            subscriptions: List of subscriptions to analyze.

        Returns:
            Total monthly spending as Decimal.
        """
        total = Decimal("0")
        for sub in subscriptions:
            total += self._to_monthly_amount(sub.amount, sub.frequency)
        return round(total, 2)

    def _to_monthly_amount(self, amount: Decimal, frequency: Frequency) -> Decimal:
        """Convert amount to monthly equivalent.

        Args:
            amount: The subscription amount.
            frequency: Payment frequency.

        Returns:
            Monthly equivalent amount.
        """
        multipliers = {
            Frequency.DAILY: Decimal("30"),
            Frequency.WEEKLY: Decimal("4.33"),
            Frequency.BIWEEKLY: Decimal("2.17"),
            Frequency.MONTHLY: Decimal("1"),
            Frequency.QUARTERLY: Decimal("0.33"),
            Frequency.YEARLY: Decimal("0.083"),
        }
        multiplier = multipliers.get(frequency, Decimal("1"))
        return amount * multiplier

    def _to_daily_amount(self, amount: Decimal, frequency: Frequency) -> Decimal:
        """Convert amount to daily equivalent.

        Args:
            amount: The subscription amount.
            frequency: Payment frequency.

        Returns:
            Daily equivalent amount.
        """
        divisors = {
            Frequency.DAILY: Decimal("1"),
            Frequency.WEEKLY: Decimal("7"),
            Frequency.BIWEEKLY: Decimal("14"),
            Frequency.MONTHLY: Decimal("30"),
            Frequency.QUARTERLY: Decimal("90"),
            Frequency.YEARLY: Decimal("365"),
        }
        divisor = divisors.get(frequency, Decimal("30"))
        return amount / divisor

    def _analyze_trends(
        self,
        subscriptions: list[Subscription],
        months_back: int,
    ) -> list[SpendingTrend]:
        """Analyze spending trends over time.

        Args:
            subscriptions: List of subscriptions.
            months_back: Number of months to analyze.

        Returns:
            List of SpendingTrend objects.
        """
        trends = []
        today = date.today()

        for i in range(months_back - 1, -1, -1):
            # Calculate the month
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            period_label = month_date.strftime("%Y-%m")

            # Count active subscriptions for that month
            active_count = sum(
                1
                for sub in subscriptions
                if sub.start_date <= month_date
                and (
                    not hasattr(sub, "end_date")
                    or sub.end_date is None
                    or sub.end_date >= month_date
                )
            )

            # Calculate spending (simplified - assumes all current rates)
            total = self._calculate_total_monthly(
                [s for s in subscriptions if s.start_date <= month_date]
            )

            trend = SpendingTrend(
                period=period_label,
                total=total,
                subscription_count=active_count,
            )
            trends.append(trend)

        # Calculate changes
        for i in range(1, len(trends)):
            prev = trends[i - 1].total
            curr = trends[i].total
            trends[i].change = curr - prev
            if prev > 0:
                trends[i].change_percent = float((curr - prev) / prev * 100)

        return trends

    def _analyze_categories(
        self,
        subscriptions: list[Subscription],
        total_monthly: Decimal,
    ) -> list[CategoryBreakdown]:
        """Analyze spending by category.

        Args:
            subscriptions: List of subscriptions.
            total_monthly: Total monthly spending for percentage calculation.

        Returns:
            List of CategoryBreakdown objects, sorted by total descending.
        """
        categories: dict[str, dict] = defaultdict(
            lambda: {"total": Decimal("0"), "subscriptions": [], "count": 0}
        )

        for sub in subscriptions:
            category = sub.category or "uncategorized"
            monthly = self._to_monthly_amount(sub.amount, sub.frequency)
            categories[category]["total"] += monthly
            categories[category]["subscriptions"].append(sub.name)
            categories[category]["count"] += 1

        breakdowns = []
        for category, data in categories.items():
            percentage = float(data["total"] / total_monthly * 100) if total_monthly > 0 else 0
            breakdowns.append(
                CategoryBreakdown(
                    category=category,
                    total=round(data["total"], 2),
                    percentage=round(percentage, 1),
                    subscription_count=data["count"],
                    subscriptions=data["subscriptions"],
                )
            )

        return sorted(breakdowns, key=lambda x: x.total, reverse=True)

    def _predict_renewals(
        self,
        subscriptions: list[Subscription],
        days_ahead: int,
    ) -> list[RenewalPrediction]:
        """Predict upcoming renewals.

        Args:
            subscriptions: List of subscriptions.
            days_ahead: How many days ahead to look.

        Returns:
            List of RenewalPrediction objects, sorted by date.
        """
        predictions = []
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        for sub in subscriptions:
            if sub.next_payment_date and sub.next_payment_date <= cutoff:
                days_until = (sub.next_payment_date - today).days
                predictions.append(
                    RenewalPrediction(
                        subscription_name=sub.name,
                        subscription_id=sub.id,
                        renewal_date=sub.next_payment_date,
                        amount=sub.amount,
                        days_until=max(0, days_until),
                        is_annual=sub.frequency == Frequency.YEARLY,
                    )
                )

        return sorted(predictions, key=lambda x: x.renewal_date)

    def _generate_recommendations(
        self,
        subscriptions: list[Subscription],
    ) -> list[CancellationRecommendation]:
        """Generate cancellation/optimization recommendations.

        Uses heuristics to identify potential savings:
        - Duplicate categories (multiple streaming services)
        - High-cost subscriptions
        - Annual savings opportunities

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of CancellationRecommendation objects.
        """
        recommendations = []

        # Check for duplicate categories
        category_counts: dict[str, list[Subscription]] = defaultdict(list)
        for sub in subscriptions:
            category = sub.category or "uncategorized"
            category_counts[category].append(sub)

        # Flag categories with multiple subscriptions
        for category, subs in category_counts.items():
            if len(subs) > 1 and category != "uncategorized":
                # Recommend reviewing the cheaper options
                sorted_subs = sorted(
                    subs, key=lambda s: self._to_monthly_amount(s.amount, s.frequency)
                )
                for sub in sorted_subs[:-1]:  # All except the most expensive
                    monthly = self._to_monthly_amount(sub.amount, sub.frequency)
                    recommendations.append(
                        CancellationRecommendation(
                            subscription_name=sub.name,
                            subscription_id=sub.id,
                            reason=f"You have {len(subs)} {category} subscriptions. Consider consolidating.",
                            potential_savings=round(monthly, 2),
                            confidence=0.6,
                        )
                    )

        # Flag high-cost subscriptions (>£50/month)
        for sub in subscriptions:
            monthly = self._to_monthly_amount(sub.amount, sub.frequency)
            if monthly > Decimal("50"):
                recommendations.append(
                    CancellationRecommendation(
                        subscription_name=sub.name,
                        subscription_id=sub.id,
                        reason="High monthly cost - verify you're using this regularly.",
                        potential_savings=round(monthly, 2),
                        confidence=0.4,
                    )
                )

        # Sort by potential savings
        return sorted(recommendations, key=lambda x: x.potential_savings, reverse=True)

    def _generate_summary(
        self,
        total_monthly: Decimal,
        trends: list[SpendingTrend],
        category_breakdown: list[CategoryBreakdown],
        recommendations: list[CancellationRecommendation],
    ) -> str:
        """Generate a human-readable summary.

        Args:
            total_monthly: Total monthly spending.
            trends: Spending trends.
            category_breakdown: Category analysis.
            recommendations: Recommendations list.

        Returns:
            Summary string.
        """
        lines = [
            f"💰 You're spending £{total_monthly:.2f} per month (£{total_monthly * 12:.2f}/year).",
        ]

        # Top category
        if category_breakdown:
            top = category_breakdown[0]
            lines.append(
                f"📊 Your top category is '{top.category}' at £{top.total:.2f}/month ({top.percentage:.0f}%)."
            )

        # Trend
        if len(trends) >= 2:
            latest = trends[-1]
            if latest.change > 0:
                lines.append(
                    f"📈 Spending increased by £{latest.change:.2f} ({latest.change_percent:.1f}%) this month."
                )
            elif latest.change < 0:
                lines.append(
                    f"📉 Spending decreased by £{abs(latest.change):.2f} ({abs(latest.change_percent):.1f}%) this month."
                )

        # Recommendations
        if recommendations:
            total_savings = sum(r.potential_savings for r in recommendations)
            lines.append(
                f"💡 Found {len(recommendations)} potential savings totaling £{total_savings:.2f}/month."
            )

        return "\n".join(lines)


def get_insights_service(db: AsyncSession) -> InsightsService:
    """Factory function to get an InsightsService instance.

    Args:
        db: Async database session.

    Returns:
        InsightsService instance.
    """
    return InsightsService(db)
