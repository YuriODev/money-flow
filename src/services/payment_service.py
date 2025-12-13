"""Payment tracking and history service.

This module provides comprehensive payment tracking functionality including
recording payments, retrieving payment history, and analyzing payment patterns.

All database operations are async for non-blocking I/O.
"""

import logging
import uuid
from collections import Counter
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from src.services.currency_service import CurrencyService

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import (
    Frequency,
    PaymentHistory,
    PaymentStatus,
    PaymentType,
    Subscription,
)
from src.schemas.subscription import CalendarEvent

logger = logging.getLogger(__name__)


class NextPaymentInfo(NamedTuple):
    """Information about the next payment for a subscription.

    Attributes:
        next_payment_date: Date of the next payment.
        days_until_payment: Number of days until the payment.
        payment_amount: Amount to be paid.
        currency: Currency code for the payment.
        payment_status: Status label (overdue, due_soon, upcoming).
        installment_info: For installments, shows "X of Y" format.
        remaining_payments: Number of payments remaining (installments only).
        total_cost_remaining: Total cost of remaining payments (installments only).
    """

    next_payment_date: date
    days_until_payment: int
    payment_amount: Decimal
    currency: str
    payment_status: str
    installment_info: str | None
    remaining_payments: int | None
    total_cost_remaining: Decimal | None


class PaymentPatternAnalysis(NamedTuple):
    """Analysis of payment patterns for a subscription.

    Attributes:
        total_payments: Total number of recorded payments.
        on_time_percentage: Percentage of payments completed on time.
        average_amount: Average payment amount.
        typical_payment_day: Most common day of month for payments.
        cost_trend: Trend direction (increasing, decreasing, stable).
    """

    total_payments: int
    on_time_percentage: float
    average_amount: Decimal
    typical_payment_day: int | None
    cost_trend: str


class PaymentService:
    """Service for payment tracking and history management.

    Handles recording payments, retrieving payment history, analyzing
    payment patterns, and generating calendar events. Supports both
    regular subscriptions and installment payments.

    Attributes:
        db: Async database session for operations.

    Example:
        >>> async with get_db() as session:
        ...     service = PaymentService(session)
        ...     payment = await service.record_payment(
        ...         subscription_id="uuid-string",
        ...         payment_date=date.today(),
        ...         amount=Decimal("15.99"),
        ...     )
        ...     print(f"Recorded payment: {payment.id}")
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the payment service.

        Args:
            db: Async database session for performing database operations.
        """
        self.db = db

    async def record_payment(
        self,
        subscription_id: str,
        payment_date: date,
        amount: Decimal,
        status: PaymentStatus = PaymentStatus.COMPLETED,
        payment_method: str | None = None,
        notes: str | None = None,
    ) -> PaymentHistory:
        """Record a payment for a subscription.

        Creates a payment history record and updates the subscription's
        last_payment_date. For installment payments, automatically increments
        completed_installments and marks subscription inactive when fully paid.

        Args:
            subscription_id: UUID of the subscription.
            payment_date: Date of the payment.
            amount: Payment amount.
            status: Payment status (default: completed).
            payment_method: Optional payment method used.
            notes: Optional notes about this payment.

        Returns:
            The newly created PaymentHistory record.

        Raises:
            ValueError: If subscription not found.

        Example:
            >>> payment = await service.record_payment(
            ...     subscription_id="uuid-string",
            ...     payment_date=date.today(),
            ...     amount=Decimal("15.99"),
            ...     payment_method="credit_card",
            ... )
        """
        logger.info(
            f"[Payment] Recording payment: subscription_id={subscription_id}, "
            f"date={payment_date}, amount={amount}, status={status}"
        )

        # Get subscription
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.error(f"[Payment] Subscription {subscription_id} not found")
            raise ValueError(f"Subscription {subscription_id} not found")

        logger.info(f"[Payment] Found subscription: {subscription.name}")

        # Determine installment number for installment payments
        installment_number = None
        if subscription.is_installment:
            installment_number = subscription.completed_installments + 1

        # Create payment record
        payment = PaymentHistory(
            id=str(uuid.uuid4()),
            subscription_id=subscription_id,
            payment_date=payment_date,
            amount=amount,
            currency=subscription.currency,
            status=status,
            payment_method=payment_method or subscription.payment_method,
            installment_number=installment_number,
            notes=notes,
        )
        self.db.add(payment)

        # Update subscription
        subscription.last_payment_date = payment_date

        if subscription.is_installment and status == PaymentStatus.COMPLETED:
            subscription.completed_installments += 1

            # Check if fully paid
            if (
                subscription.total_installments
                and subscription.completed_installments >= subscription.total_installments
            ):
                subscription.is_active = False
                existing_notes = subscription.notes or ""
                subscription.notes = existing_notes + "\n✓ Fully paid off"
                logger.info(f"Installment subscription {subscription.name} fully paid")

        # Calculate next payment date
        subscription.next_payment_date = self._calculate_next_payment(
            subscription.start_date,
            subscription.frequency,
            subscription.frequency_interval,
        )

        await self.db.flush()
        await self.db.refresh(payment)

        logger.info(
            f"[Payment] Successfully recorded: {subscription.name}, "
            f"{amount} {subscription.currency} on {payment_date}, "
            f"payment_id={payment.id}"
        )
        return payment

    async def delete_payment(
        self,
        subscription_id: str,
        payment_date: date,
    ) -> None:
        """Delete a payment record (unmark as paid).

        Removes the payment history record for a specific subscription and date.
        For installment payments, decrements the completed_installments count.

        Args:
            subscription_id: UUID of the subscription.
            payment_date: Date of the payment to delete.

        Raises:
            ValueError: If payment not found.

        Example:
            >>> await service.delete_payment("uuid-string", date(2025, 1, 15))
        """
        logger.info(
            f"[Payment] Deleting payment: subscription_id={subscription_id}, date={payment_date}"
        )

        # Find all payment records for this subscription and date
        result = await self.db.execute(
            select(PaymentHistory).where(
                and_(
                    PaymentHistory.subscription_id == subscription_id,
                    PaymentHistory.payment_date == payment_date,
                    PaymentHistory.status == PaymentStatus.COMPLETED,
                )
            )
        )
        payments = result.scalars().all()

        if not payments:
            logger.error(f"[Payment] Payment not found for {subscription_id} on {payment_date}")
            raise ValueError(
                f"Payment not found for subscription {subscription_id} on {payment_date}"
            )

        # Get the subscription to update installment count if needed
        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()

        if subscription and subscription.is_installment:
            # Decrement completed installments (only once, regardless of duplicate records)
            if subscription.completed_installments > 0:
                subscription.completed_installments -= 1
                logger.info(
                    f"[Payment] Decremented installments for {subscription.name}: "
                    f"now {subscription.completed_installments}"
                )
            # Reactivate if it was marked fully paid
            if (
                not subscription.is_active
                and subscription.notes
                and "✓ Fully paid off" in subscription.notes
            ):
                subscription.is_active = True
                subscription.notes = subscription.notes.replace("\n✓ Fully paid off", "")

        # Delete all payment records for this date (handles duplicates)
        for payment in payments:
            await self.db.delete(payment)
        await self.db.flush()

        logger.info(
            f"[Payment] Successfully deleted {len(payments)} payment(s) for {subscription_id} on {payment_date}"
        )

    async def get_payment_history(
        self,
        subscription_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[PaymentHistory]:
        """Get payment history for a subscription.

        Retrieves payment records ordered by payment date descending.

        Args:
            subscription_id: UUID of the subscription.
            limit: Maximum number of records to return (default: 50).
            offset: Number of records to skip (default: 0).

        Returns:
            Sequence of PaymentHistory records.

        Example:
            >>> history = await service.get_payment_history("uuid-string")
            >>> for payment in history:
            ...     print(f"{payment.payment_date}: {payment.amount}")
        """
        result = await self.db.execute(
            select(PaymentHistory)
            .where(PaymentHistory.subscription_id == subscription_id)
            .order_by(PaymentHistory.payment_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all_payment_history(
        self,
        limit: int = 100,
        status: PaymentStatus | None = None,
    ) -> Sequence[PaymentHistory]:
        """Get payment history across all subscriptions.

        Args:
            limit: Maximum number of records to return (default: 100).
            status: Optional filter by payment status.

        Returns:
            Sequence of PaymentHistory records.

        Example:
            >>> history = await service.get_all_payment_history(status=PaymentStatus.FAILED)
        """
        query = select(PaymentHistory).order_by(PaymentHistory.payment_date.desc())

        if status:
            query = query.where(PaymentHistory.status == status)

        result = await self.db.execute(query.limit(limit))
        return result.scalars().all()

    async def get_next_payment_info(self, subscription_id: str) -> NextPaymentInfo:
        """Get comprehensive next payment information.

        Provides detailed information about the next payment including
        status, installment info, and remaining costs.

        Args:
            subscription_id: UUID of the subscription.

        Returns:
            NextPaymentInfo with all payment details.

        Raises:
            ValueError: If subscription not found.

        Example:
            >>> info = await service.get_next_payment_info("uuid-string")
            >>> print(f"Next payment: {info.next_payment_date}")
            >>> print(f"Status: {info.payment_status}")
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        today = date.today()
        days_until = (subscription.next_payment_date - today).days

        # Determine status
        status = "upcoming"
        if days_until < 0:
            status = "overdue"
        elif days_until <= subscription.reminder_days:
            status = "due_soon"

        # Installment info
        installment_info = None
        remaining_payments = None
        total_cost_remaining = None

        if subscription.is_installment and subscription.total_installments:
            remaining = subscription.total_installments - subscription.completed_installments
            installment_info = (
                f"{subscription.completed_installments + 1} of {subscription.total_installments}"
            )
            remaining_payments = remaining
            total_cost_remaining = subscription.amount * remaining

        return NextPaymentInfo(
            next_payment_date=subscription.next_payment_date,
            days_until_payment=days_until,
            payment_amount=subscription.amount,
            currency=subscription.currency,
            payment_status=status,
            installment_info=installment_info,
            remaining_payments=remaining_payments,
            total_cost_remaining=total_cost_remaining,
        )

    async def get_payment_pattern_analysis(
        self,
        subscription_id: str,
    ) -> PaymentPatternAnalysis:
        """Analyze payment patterns for a subscription.

        Returns insights about payment history including consistency,
        average amounts, and timing patterns.

        Args:
            subscription_id: UUID of the subscription.

        Returns:
            PaymentPatternAnalysis with detailed insights.

        Example:
            >>> analysis = await service.get_payment_pattern_analysis("uuid-string")
            >>> print(f"On-time rate: {analysis.on_time_percentage}%")
        """
        history = await self.get_payment_history(subscription_id, limit=100)

        if not history:
            return PaymentPatternAnalysis(
                total_payments=0,
                on_time_percentage=0.0,
                average_amount=Decimal("0"),
                typical_payment_day=None,
                cost_trend="stable",
            )

        # Calculate metrics
        total_payments = len(history)
        completed_payments = sum(1 for p in history if p.status == PaymentStatus.COMPLETED)
        on_time_percentage = (
            (completed_payments / total_payments * 100) if total_payments > 0 else 0.0
        )
        average_amount = sum(p.amount for p in history) / total_payments

        # Find most common payment day
        payment_days = [p.payment_date.day for p in history]
        day_counts = Counter(payment_days)
        typical_day = day_counts.most_common(1)[0][0] if day_counts else None

        # Determine cost trend (compare first half to second half)
        cost_trend = "stable"
        if len(history) >= 4:
            mid = len(history) // 2
            recent_avg = sum(p.amount for p in history[:mid]) / mid
            older_avg = sum(p.amount for p in history[mid:]) / (len(history) - mid)
            if recent_avg > older_avg * Decimal("1.1"):
                cost_trend = "increasing"
            elif recent_avg < older_avg * Decimal("0.9"):
                cost_trend = "decreasing"

        return PaymentPatternAnalysis(
            total_payments=total_payments,
            on_time_percentage=round(on_time_percentage, 1),
            average_amount=round(average_amount, 2),
            typical_payment_day=typical_day,
            cost_trend=cost_trend,
        )

    async def get_calendar_events(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:
        """Get payment events for a date range (calendar view).

        Generates calendar events for all active subscriptions within
        the specified date range. Handles recurring payments.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.

        Returns:
            List of CalendarEvent objects for the date range.

        Example:
            >>> events = await service.get_calendar_events(
            ...     date(2025, 1, 1),
            ...     date(2025, 1, 31),
            ... )
            >>> for event in events:
            ...     print(f"{event.payment_date}: {event.name} - {event.amount}")
        """
        print(f"[Calendar] Getting events for {start_date} to {end_date}", flush=True)

        # Get all active subscriptions
        result = await self.db.execute(
            select(Subscription).where(Subscription.is_active == True)  # noqa: E712
        )
        subscriptions = result.scalars().all()
        print(f"[Calendar] Found {len(subscriptions)} active subscriptions", flush=True)

        # Get all completed payments in the date range to check which are already paid
        payments_result = await self.db.execute(
            select(PaymentHistory).where(
                and_(
                    PaymentHistory.payment_date >= start_date,
                    PaymentHistory.payment_date <= end_date,
                    PaymentHistory.status == PaymentStatus.COMPLETED,
                )
            )
        )
        completed_payments = payments_result.scalars().all()
        print(f"[Calendar] Found {len(completed_payments)} completed payments in range", flush=True)
        for p in completed_payments:
            print(f"  - Payment: sub_id={p.subscription_id}, date={p.payment_date}", flush=True)

        # Build a set of (subscription_id, payment_date) for quick lookup
        paid_payments: set[tuple[str, date]] = {
            (p.subscription_id, p.payment_date) for p in completed_payments
        }
        print(f"[Calendar] Paid payments set has {len(paid_payments)} entries", flush=True)

        events: list[CalendarEvent] = []

        for sub in subscriptions:
            # ONE_TIME payments only appear once on their payment date, not recurring
            if sub.payment_type == PaymentType.ONE_TIME:
                # Only include if the single payment date is within range
                if start_date <= sub.next_payment_date <= end_date:
                    today = date.today()
                    days_until = (sub.next_payment_date - today).days
                    status = "upcoming"
                    if days_until < 0:
                        status = "overdue"
                    elif days_until <= sub.reminder_days:
                        status = "due_soon"

                    is_paid = (sub.id, sub.next_payment_date) in paid_payments
                    logger.debug(
                        f"[Calendar] ONE_TIME Event: {sub.name} on {sub.next_payment_date}, "
                        f"sub.id={sub.id}, is_paid={is_paid}"
                    )
                    events.append(
                        CalendarEvent(
                            id=sub.id,
                            name=sub.name,
                            amount=sub.amount,
                            currency=sub.currency,
                            payment_date=sub.next_payment_date,
                            color=sub.color,
                            icon_url=sub.icon_url,
                            category=sub.category,
                            is_installment=False,
                            installment_number=None,
                            total_installments=None,
                            status=status,
                            card_id=sub.card_id,
                            is_paid=is_paid,
                        )
                    )
                continue

            # Find all payment dates within the range for recurring payments
            payment_dates = self._get_payment_dates_in_range(
                subscription=sub,
                start_date=start_date,
                end_date=end_date,
            )

            for payment_date in payment_dates:
                # Calculate installment number for this date
                installment_num = None
                if sub.is_installment and sub.installment_start_date:
                    # Calculate how many payments since start
                    installment_num = self._calculate_installment_number(sub, payment_date)

                # Determine status for this payment
                today = date.today()
                days_until = (payment_date - today).days
                status = "upcoming"
                if days_until < 0:
                    status = "overdue"
                elif days_until <= sub.reminder_days:
                    status = "due_soon"

                is_paid = (sub.id, payment_date) in paid_payments
                logger.debug(
                    f"[Calendar] Event: {sub.name} on {payment_date}, "
                    f"sub.id={sub.id}, is_paid={is_paid}, "
                    f"lookup_key=({sub.id}, {payment_date})"
                )
                events.append(
                    CalendarEvent(
                        id=sub.id,
                        name=sub.name,
                        amount=sub.amount,
                        currency=sub.currency,
                        payment_date=payment_date,
                        color=sub.color,
                        icon_url=sub.icon_url,
                        category=sub.category,
                        is_installment=sub.is_installment,
                        installment_number=installment_num,
                        total_installments=sub.total_installments,
                        status=status,
                        card_id=sub.card_id,
                        is_paid=is_paid,
                    )
                )

        # Sort by date
        events.sort(key=lambda e: e.payment_date)
        logger.info(f"[Calendar] Returning {len(events)} events")
        return events

    async def get_monthly_summary(
        self,
        year: int,
        month: int,
    ) -> dict:
        """Get payment summary for a specific month.

        Aggregates payment data for the specified month including
        totals, counts, and status breakdown.

        Args:
            year: Year to query.
            month: Month to query (1-12).

        Returns:
            Dictionary with monthly payment statistics.

        Example:
            >>> summary = await service.get_monthly_summary(2025, 1)
            >>> print(f"Total paid: {summary['total_paid']}")
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Get payment history for the month
        result = await self.db.execute(
            select(PaymentHistory).where(
                and_(
                    PaymentHistory.payment_date >= start_date,
                    PaymentHistory.payment_date <= end_date,
                )
            )
        )
        payments = result.scalars().all()

        # Calculate statistics
        total_paid = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        total_pending = sum(p.amount for p in payments if p.status == PaymentStatus.PENDING)
        total_failed = sum(p.amount for p in payments if p.status == PaymentStatus.FAILED)

        # Count by status
        status_counts = Counter(p.status for p in payments)

        return {
            "year": year,
            "month": month,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_failed": total_failed,
            "payment_count": len(payments),
            "completed_count": status_counts.get(PaymentStatus.COMPLETED, 0),
            "pending_count": status_counts.get(PaymentStatus.PENDING, 0),
            "failed_count": status_counts.get(PaymentStatus.FAILED, 0),
        }

    def _get_payment_dates_in_range(
        self,
        subscription: Subscription,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """Get all payment dates for a subscription within a date range.

        Args:
            subscription: The subscription to check.
            start_date: Start of the date range.
            end_date: End of the date range.

        Returns:
            List of payment dates within the range.
        """
        dates: list[date] = []
        delta = self._get_delta(subscription.frequency, subscription.frequency_interval)

        # Start from the subscription start date
        current = subscription.start_date

        # Move forward until we're at or past start_date
        while current < start_date:
            current += delta

        # Determine the effective end date (respect subscription end_date if set)
        effective_end = end_date
        if subscription.end_date and subscription.end_date < end_date:
            effective_end = subscription.end_date

        # Collect all dates until effective end date
        while current <= effective_end:
            dates.append(current)
            current += delta

            # Safety limit for installment payments
            if subscription.is_installment and subscription.total_installments:
                if len(dates) >= subscription.total_installments:
                    break

        return dates

    def _calculate_installment_number(
        self,
        subscription: Subscription,
        payment_date: date,
    ) -> int:
        """Calculate which installment number a payment date corresponds to.

        Args:
            subscription: The subscription.
            payment_date: The date to calculate for.

        Returns:
            The installment number (1-based).
        """
        if not subscription.installment_start_date:
            return 1

        delta = self._get_delta(subscription.frequency, subscription.frequency_interval)
        current = subscription.installment_start_date
        installment = 1

        while current < payment_date:
            current += delta
            installment += 1

        return installment

    def _calculate_next_payment(
        self,
        start: date,
        frequency: Frequency,
        interval: int,
    ) -> date:
        """Calculate the next payment date from start date.

        Args:
            start: The subscription start date.
            frequency: Payment frequency.
            interval: Frequency interval.

        Returns:
            The next payment date (always in the future or today).
        """
        today = date.today()
        next_date = start
        delta = self._get_delta(frequency, interval)

        while next_date < today:
            next_date += delta

        return next_date

    def _get_delta(self, frequency: Frequency, interval: int) -> relativedelta:
        """Get relativedelta for a frequency and interval.

        Args:
            frequency: Payment frequency enum value.
            interval: Multiplier for the frequency.

        Returns:
            relativedelta object for the specified frequency.
        """
        match frequency:
            case Frequency.DAILY:
                return relativedelta(days=interval)
            case Frequency.WEEKLY:
                return relativedelta(weeks=interval)
            case Frequency.BIWEEKLY:
                return relativedelta(weeks=2 * interval)
            case Frequency.MONTHLY:
                return relativedelta(months=interval)
            case Frequency.QUARTERLY:
                return relativedelta(months=3 * interval)
            case Frequency.YEARLY:
                return relativedelta(years=interval)
            case Frequency.CUSTOM:
                # CUSTOM uses interval as months (e.g., interval=6 for every 6 months)
                return relativedelta(months=interval)

    async def get_monthly_payments_summary(
        self,
        currency: str = "GBP",
        currency_service: "CurrencyService | None" = None,
    ) -> dict:
        """Get unified monthly payments summary for current and next month.

        Calculates total payments due, amount paid, and remaining for current month,
        as well as total due for next month. All amounts are converted to the
        requested display currency.

        This is the unified source of truth for monthly payment totals used by
        both the Calendar and Cards dashboard components.

        Args:
            currency: Target currency for totals (default: GBP).
            currency_service: Optional currency service for conversion.

        Returns:
            Dictionary with:
                - current_month_total: Total due this month
                - current_month_paid: Amount paid this month
                - current_month_remaining: Remaining this month
                - next_month_total: Total due next month
                - payment_count_this_month: Number of payments this month
                - payment_count_next_month: Number of payments next month
                - currency: Target currency code

        Example:
            >>> summary = await service.get_monthly_payments_summary("USD")
            >>> print(f"Due this month: {summary['current_month_total']}")
        """
        from src.services.currency_service import CurrencyService

        today = date.today()

        # Calculate current month date range
        current_month_start = date(today.year, today.month, 1)
        if today.month == 12:
            current_month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            next_month_start = date(today.year + 1, 1, 1)
            next_month_end = date(today.year + 1, 2, 1) - timedelta(days=1)
        else:
            current_month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            next_month_start = date(today.year, today.month + 1, 1)
            if today.month + 1 == 12:
                next_month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                next_month_end = date(today.year, today.month + 2, 1) - timedelta(days=1)

        # Get calendar events for both months
        current_month_events = await self.get_calendar_events(
            current_month_start, current_month_end
        )
        next_month_events = await self.get_calendar_events(next_month_start, next_month_end)

        # Initialize currency service if not provided
        if currency_service is None:
            currency_service = CurrencyService()

        # Helper to convert and sum amounts
        async def sum_amounts(
            events: list[CalendarEvent],
            filter_paid: bool | None = None,
        ) -> Decimal:
            total = Decimal("0")
            for event in events:
                # Filter by paid status if specified
                if filter_paid is not None and event.is_paid != filter_paid:
                    continue

                amount = event.amount
                # Convert to target currency if needed
                if event.currency != currency:
                    amount = await currency_service.convert(amount, event.currency, currency)
                total += amount
            return total

        # Calculate totals
        current_month_total = await sum_amounts(current_month_events)
        current_month_paid = await sum_amounts(current_month_events, filter_paid=True)
        current_month_remaining = current_month_total - current_month_paid
        next_month_total = await sum_amounts(next_month_events)

        # Count payments
        payment_count_this_month = len(current_month_events)
        payment_count_next_month = len(next_month_events)

        return {
            "current_month_total": current_month_total.quantize(Decimal("0.01")),
            "current_month_paid": current_month_paid.quantize(Decimal("0.01")),
            "current_month_remaining": current_month_remaining.quantize(Decimal("0.01")),
            "next_month_total": next_month_total.quantize(Decimal("0.01")),
            "payment_count_this_month": payment_count_this_month,
            "payment_count_next_month": payment_count_next_month,
            "currency": currency,
        }
