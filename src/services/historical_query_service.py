"""Historical query service for temporal subscription queries.

This module provides the HistoricalQueryService class for handling
time-based queries about subscriptions, such as:
- "What did I add last month?"
- "Show subscriptions from January"
- "How much was I spending in 2024?"

Features:
- Temporal expression parsing
- Date range queries
- Historical spending analysis
- Change detection
"""

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    """A date range for historical queries.

    Attributes:
        start: Start date of the range.
        end: End date of the range.
        label: Human-readable label for the range.
    """

    start: date
    end: date
    label: str


@dataclass
class HistoricalSubscription:
    """Subscription data at a point in history.

    Attributes:
        id: Subscription ID.
        name: Subscription name.
        amount: Amount at that time.
        frequency: Payment frequency.
        category: Category.
        created_at: When it was created.
        was_active: Whether it was active in the period.
    """

    id: str
    name: str
    amount: Decimal
    frequency: str
    category: str | None
    created_at: date
    was_active: bool


@dataclass
class HistoricalQueryResult:
    """Result of a historical query.

    Attributes:
        query: Original query string.
        date_range: The resolved date range.
        subscriptions: Matching subscriptions.
        total_monthly: Total monthly spending in period.
        subscription_count: Number of subscriptions.
        summary: Human-readable summary.
    """

    query: str
    date_range: DateRange
    subscriptions: list[HistoricalSubscription]
    total_monthly: Decimal
    subscription_count: int
    summary: str


class HistoricalQueryService:
    """Service for handling temporal subscription queries.

    Parses natural language time expressions and retrieves historical
    subscription data.

    Attributes:
        db: Async database session.

    Example:
        >>> service = HistoricalQueryService(db_session)
        >>> result = await service.query("What did I add last month?")
        >>> print(result.summary)
    """

    # Temporal patterns for parsing
    TEMPORAL_PATTERNS = [
        # Relative patterns
        (r"last\s+month", "last_month"),
        (r"this\s+month", "this_month"),
        (r"last\s+week", "last_week"),
        (r"this\s+week", "this_week"),
        (r"last\s+year", "last_year"),
        (r"this\s+year", "this_year"),
        (r"yesterday", "yesterday"),
        (r"today", "today"),
        (r"(\d+)\s+days?\s+ago", "days_ago"),
        (r"(\d+)\s+weeks?\s+ago", "weeks_ago"),
        (r"(\d+)\s+months?\s+ago", "months_ago"),
        # Month names
        (r"in\s+(january|jan)", "january"),
        (r"in\s+(february|feb)", "february"),
        (r"in\s+(march|mar)", "march"),
        (r"in\s+(april|apr)", "april"),
        (r"in\s+(may)", "may"),
        (r"in\s+(june|jun)", "june"),
        (r"in\s+(july|jul)", "july"),
        (r"in\s+(august|aug)", "august"),
        (r"in\s+(september|sep|sept)", "september"),
        (r"in\s+(october|oct)", "october"),
        (r"in\s+(november|nov)", "november"),
        (r"in\s+(december|dec)", "december"),
        # Year patterns
        (r"in\s+(\d{4})", "year"),
        # Quarter patterns
        (r"q1|first\s+quarter", "q1"),
        (r"q2|second\s+quarter", "q2"),
        (r"q3|third\s+quarter", "q3"),
        (r"q4|fourth\s+quarter", "q4"),
    ]

    MONTH_NUMBERS = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the historical query service.

        Args:
            db: Async database session.
        """
        self.db = db

    async def query(self, query_text: str) -> HistoricalQueryResult:
        """Execute a historical query.

        Parses the query for temporal expressions and retrieves
        matching subscription data.

        Args:
            query_text: Natural language query.

        Returns:
            HistoricalQueryResult with matching data.

        Example:
            >>> result = await service.query("What did I add in January?")
            >>> for sub in result.subscriptions:
            ...     print(sub.name)
        """
        # Parse temporal expression
        date_range = self._parse_temporal_expression(query_text)

        # Determine query type
        query_type = self._detect_query_type(query_text)

        # Execute appropriate query
        if query_type == "added":
            subscriptions = await self._get_subscriptions_added(date_range)
        elif query_type == "cancelled":
            subscriptions = await self._get_subscriptions_cancelled(date_range)
        elif query_type == "spending":
            subscriptions = await self._get_subscriptions_active(date_range)
        else:
            subscriptions = await self._get_subscriptions_active(date_range)

        # Calculate totals
        total_monthly = self._calculate_monthly_total(subscriptions)

        # Generate summary
        summary = self._generate_summary(
            query_type=query_type,
            date_range=date_range,
            subscriptions=subscriptions,
            total_monthly=total_monthly,
        )

        return HistoricalQueryResult(
            query=query_text,
            date_range=date_range,
            subscriptions=subscriptions,
            total_monthly=total_monthly,
            subscription_count=len(subscriptions),
            summary=summary,
        )

    def _parse_temporal_expression(self, text: str) -> DateRange:
        """Parse temporal expression from text.

        Args:
            text: Text containing temporal expression.

        Returns:
            DateRange for the parsed expression.
        """
        text_lower = text.lower()
        today = date.today()

        for pattern, expr_type in self.TEMPORAL_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return self._resolve_temporal_expression(expr_type, match, today)

        # Default to this month if no temporal expression found
        return self._get_month_range(today.year, today.month, "this month")

    def _resolve_temporal_expression(
        self,
        expr_type: str,
        match: re.Match,
        today: date,
    ) -> DateRange:
        """Resolve a temporal expression to a date range.

        Args:
            expr_type: Type of expression (e.g., "last_month").
            match: Regex match object.
            today: Today's date.

        Returns:
            DateRange for the expression.
        """
        if expr_type == "today":
            return DateRange(start=today, end=today, label="today")

        elif expr_type == "yesterday":
            yesterday = today - timedelta(days=1)
            return DateRange(start=yesterday, end=yesterday, label="yesterday")

        elif expr_type == "this_week":
            start = today - timedelta(days=today.weekday())
            return DateRange(start=start, end=today, label="this week")

        elif expr_type == "last_week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return DateRange(start=start, end=end, label="last week")

        elif expr_type == "this_month":
            return self._get_month_range(today.year, today.month, "this month")

        elif expr_type == "last_month":
            last_month = today.replace(day=1) - timedelta(days=1)
            return self._get_month_range(last_month.year, last_month.month, "last month")

        elif expr_type == "this_year":
            start = date(today.year, 1, 1)
            return DateRange(start=start, end=today, label="this year")

        elif expr_type == "last_year":
            start = date(today.year - 1, 1, 1)
            end = date(today.year - 1, 12, 31)
            return DateRange(start=start, end=end, label=str(today.year - 1))

        elif expr_type == "days_ago":
            days = int(match.group(1))
            target = today - timedelta(days=days)
            return DateRange(start=target, end=target, label=f"{days} days ago")

        elif expr_type == "weeks_ago":
            weeks = int(match.group(1))
            start = today - timedelta(weeks=weeks)
            return DateRange(start=start, end=start + timedelta(days=6), label=f"{weeks} weeks ago")

        elif expr_type == "months_ago":
            months = int(match.group(1))
            target = today - relativedelta(months=months)
            return self._get_month_range(target.year, target.month, f"{months} months ago")

        elif expr_type == "year":
            year = int(match.group(1))
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            return DateRange(start=start, end=end, label=str(year))

        elif expr_type in self.MONTH_NUMBERS or expr_type in [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]:
            month_num = self.MONTH_NUMBERS.get(expr_type, 1)
            # Assume current year unless month is in future
            year = today.year
            if month_num > today.month:
                year -= 1
            return self._get_month_range(year, month_num, expr_type.capitalize())

        elif expr_type.startswith("q"):
            quarter = int(expr_type[1])
            year = today.year
            start_month = (quarter - 1) * 3 + 1
            start = date(year, start_month, 1)
            end = start + relativedelta(months=3) - timedelta(days=1)
            return DateRange(start=start, end=end, label=f"Q{quarter} {year}")

        # Default
        return self._get_month_range(today.year, today.month, "this month")

    def _get_month_range(self, year: int, month: int, label: str) -> DateRange:
        """Get date range for a specific month.

        Args:
            year: Year.
            month: Month number (1-12).
            label: Label for the range.

        Returns:
            DateRange for the month.
        """
        start = date(year, month, 1)
        # Get last day of month
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return DateRange(start=start, end=end, label=label)

    def _detect_query_type(self, text: str) -> str:
        """Detect the type of historical query.

        Args:
            text: Query text.

        Returns:
            Query type: "added", "cancelled", "spending", or "active".
        """
        text_lower = text.lower()

        if any(word in text_lower for word in ["add", "added", "create", "new", "subscribe"]):
            return "added"
        elif any(word in text_lower for word in ["cancel", "cancelled", "remove", "deleted"]):
            return "cancelled"
        elif any(word in text_lower for word in ["spend", "spending", "cost", "paid", "pay"]):
            return "spending"
        else:
            return "active"

    async def _get_subscriptions_added(self, date_range: DateRange) -> list[HistoricalSubscription]:
        """Get subscriptions added in a date range.

        Args:
            date_range: The date range to query.

        Returns:
            List of subscriptions added in the range.
        """
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.created_at >= date_range.start,
                    Subscription.created_at <= date_range.end,
                )
            )
        )
        subscriptions = result.scalars().all()

        return [
            HistoricalSubscription(
                id=sub.id,
                name=sub.name,
                amount=sub.amount,
                frequency=sub.frequency.value,
                category=sub.category,
                created_at=sub.created_at.date()
                if hasattr(sub.created_at, "date")
                else sub.created_at,
                was_active=sub.is_active,
            )
            for sub in subscriptions
        ]

    async def _get_subscriptions_cancelled(
        self, date_range: DateRange
    ) -> list[HistoricalSubscription]:
        """Get subscriptions cancelled in a date range.

        Note: This requires tracking cancellation dates, which we don't
        currently have. Returns inactive subscriptions as approximation.

        Args:
            date_range: The date range to query.

        Returns:
            List of inactive subscriptions.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.is_active == False)  # noqa: E712
        )
        subscriptions = result.scalars().all()

        return [
            HistoricalSubscription(
                id=sub.id,
                name=sub.name,
                amount=sub.amount,
                frequency=sub.frequency.value,
                category=sub.category,
                created_at=sub.created_at.date()
                if hasattr(sub.created_at, "date")
                else sub.created_at,
                was_active=False,
            )
            for sub in subscriptions
        ]

    async def _get_subscriptions_active(
        self, date_range: DateRange
    ) -> list[HistoricalSubscription]:
        """Get subscriptions that were active in a date range.

        Args:
            date_range: The date range to query.

        Returns:
            List of subscriptions active in the range.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.start_date <= date_range.end)
        )
        subscriptions = result.scalars().all()

        return [
            HistoricalSubscription(
                id=sub.id,
                name=sub.name,
                amount=sub.amount,
                frequency=sub.frequency.value,
                category=sub.category,
                created_at=sub.created_at.date()
                if hasattr(sub.created_at, "date")
                else sub.created_at,
                was_active=sub.is_active,
            )
            for sub in subscriptions
            if sub.start_date <= date_range.end
        ]

    def _calculate_monthly_total(self, subscriptions: list[HistoricalSubscription]) -> Decimal:
        """Calculate total monthly spending.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            Total monthly spending.
        """

        total = Decimal("0")
        multipliers = {
            "daily": Decimal("30"),
            "weekly": Decimal("4.33"),
            "biweekly": Decimal("2.17"),
            "monthly": Decimal("1"),
            "quarterly": Decimal("0.33"),
            "yearly": Decimal("0.083"),
        }

        for sub in subscriptions:
            if sub.was_active:
                multiplier = multipliers.get(sub.frequency, Decimal("1"))
                total += sub.amount * multiplier

        return round(total, 2)

    def _generate_summary(
        self,
        query_type: str,
        date_range: DateRange,
        subscriptions: list[HistoricalSubscription],
        total_monthly: Decimal,
    ) -> str:
        """Generate human-readable summary.

        Args:
            query_type: Type of query.
            date_range: Date range queried.
            subscriptions: Matching subscriptions.
            total_monthly: Total monthly spending.

        Returns:
            Summary string.
        """
        count = len(subscriptions)

        if query_type == "added":
            if count == 0:
                return f"📭 No subscriptions were added in {date_range.label}."
            names = ", ".join(sub.name for sub in subscriptions[:5])
            if count > 5:
                names += f" and {count - 5} more"
            return f"📥 Added {count} subscription(s) in {date_range.label}: {names}"

        elif query_type == "cancelled":
            if count == 0:
                return f"📭 No subscriptions were cancelled in {date_range.label}."
            names = ", ".join(sub.name for sub in subscriptions[:5])
            return f"🗑️ Cancelled {count} subscription(s): {names}"

        elif query_type == "spending":
            if count == 0:
                return f"📭 No active subscriptions in {date_range.label}."
            return f"💰 In {date_range.label}, you were spending £{total_monthly:.2f}/month across {count} subscription(s)."

        else:
            if count == 0:
                return f"📭 No subscriptions found for {date_range.label}."
            return f"📋 Found {count} subscription(s) for {date_range.label}, totaling £{total_monthly:.2f}/month."


def get_historical_query_service(db: AsyncSession) -> HistoricalQueryService:
    """Factory function to get a HistoricalQueryService instance.

    Args:
        db: Async database session.

    Returns:
        HistoricalQueryService instance.
    """
    return HistoricalQueryService(db)
