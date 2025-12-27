"""Subscription business logic service.

This module provides the core business logic for subscription management,
including CRUD operations, payment date calculations, and spending analytics.

All database operations are async for non-blocking I/O. RAG integration
provides semantic search over subscription notes.
"""

import logging
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.exceptions import SubscriptionNotFoundError
from src.models.subscription import Frequency, PaymentMode, PaymentType, Subscription
from src.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionSummary,
    SubscriptionUpdate,
)
from src.services.rag_service import get_rag_service

if TYPE_CHECKING:
    from src.services.currency_service import CurrencyService

logger = logging.getLogger(__name__)

# Re-export for backwards compatibility
__all__ = ["SubscriptionService", "SubscriptionNotFoundError"]


class SubscriptionService:
    """Service for subscription CRUD operations and analytics.

    This service provides all business logic for managing subscriptions,
    including creating, reading, updating, and deleting subscriptions,
    as well as calculating payment dates and spending summaries.

    All database operations use async/await for non-blocking I/O.

    Attributes:
        db: Async database session for operations.

    Example:
        >>> async with get_db() as session:
        ...     service = SubscriptionService(session)
        ...     subscription = await service.create(SubscriptionCreate(
        ...         name="Netflix",
        ...         amount=Decimal("15.99"),
        ...         currency="GBP",
        ...         frequency=Frequency.MONTHLY,
        ...         start_date=date.today(),
        ...     ))
        ...     print(subscription.name)
        'Netflix'
    """

    def __init__(self, db: AsyncSession, user_id: str = "default") -> None:
        """Initialize the subscription service.

        Args:
            db: Async database session for performing database operations.
                The session should be provided by dependency injection.
            user_id: User ID for RAG note indexing (default: "default").

        Example:
            >>> from src.db.database import get_db
            >>> async with get_db() as session:
            ...     service = SubscriptionService(session, user_id="user-123")
        """
        self.db = db
        self.user_id = user_id
        self._rag = None  # Lazy loaded

    def _get_rag(self):
        """Get RAG service (lazy loaded).

        Returns:
            RAG service instance if RAG is enabled, None otherwise.
        """
        if self._rag is None and settings.rag_enabled:
            self._rag = get_rag_service()
        return self._rag

    async def _index_note(self, subscription_id: str, note: str | None) -> None:
        """Index a subscription note for semantic search.

        Args:
            subscription_id: The subscription's ID.
            note: The note content to index.
        """
        rag = self._get_rag()
        if rag and note:
            try:
                await rag.index_note(
                    user_id=self.user_id,
                    subscription_id=subscription_id,
                    note=note,
                )
            except Exception as e:
                logger.warning(f"Failed to index note for {subscription_id}: {e}")

    async def create(self, data: SubscriptionCreate) -> Subscription:
        """Create a new subscription.

        Creates a new subscription record in the database with automatically
        calculated next payment date based on the start date and frequency.

        Args:
            data: Subscription creation data including name, amount, currency,
                frequency, and start date.

        Returns:
            The newly created Subscription object with generated ID and
            calculated next_payment_date.

        Raises:
            sqlalchemy.exc.IntegrityError: If database constraints are violated.

        Example:
            >>> data = SubscriptionCreate(
            ...     name="Spotify",
            ...     amount=Decimal("9.99"),
            ...     currency="GBP",
            ...     frequency=Frequency.MONTHLY,
            ...     start_date=date(2025, 1, 1),
            ... )
            >>> subscription = await service.create(data)
            >>> print(subscription.id)
            'uuid-string'
        """
        next_payment = self._calculate_next_payment(
            data.start_date, data.frequency, data.frequency_interval
        )

        subscription_data = data.model_dump()
        # Set user_id if not "default"
        if self.user_id and self.user_id != "default":
            subscription_data["user_id"] = self.user_id
        subscription = Subscription(
            **subscription_data,
            next_payment_date=next_payment,
        )
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription)

        # Index note for semantic search
        if data.notes:
            await self._index_note(subscription.id, data.notes)

        logger.info(f"Created subscription: {subscription.name} ({subscription.id})")
        return subscription

    async def get_by_id(self, subscription_id: str) -> Subscription | None:
        """Get a subscription by its ID.

        Args:
            subscription_id: UUID string of the subscription to retrieve.

        Returns:
            The Subscription object if found, None otherwise.

        Example:
            >>> subscription = await service.get_by_id("uuid-string")
            >>> if subscription:
            ...     print(subscription.name)
        """
        query = select(Subscription).where(Subscription.id == subscription_id)
        # Filter by user_id if not "default"
        if self.user_id and self.user_id != "default":
            query = query.where(Subscription.user_id == self.user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Subscription | None:
        """Get a subscription by name (case-insensitive partial match).

        Searches for subscriptions where the name contains the search term.
        Useful for natural language command processing.

        Args:
            name: Subscription name or partial name to search for.

        Returns:
            The first matching Subscription object, or None if not found.

        Example:
            >>> # Find "Netflix" by partial name
            >>> sub = await service.get_by_name("net")
            >>> print(sub.name)
            'Netflix'
        """
        query = select(Subscription).where(Subscription.name.ilike(f"%{name}%"))
        # Filter by user_id if not "default"
        if self.user_id and self.user_id != "default":
            query = query.where(Subscription.user_id == self.user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: bool | None = None,
        category: str | None = None,
        payment_type: PaymentType | None = None,
        payment_mode: PaymentMode | None = None,
        include_card: bool = False,
        include_relationships: bool = False,
    ) -> Sequence[Subscription]:
        """Get all subscriptions/payments with optional filters.

        Retrieves payments from the database with optional filtering
        by active status, category, payment type, and/or payment mode.
        Results are ordered by next payment date (ascending).

        Automatically updates stale next_payment_date values for
        recurring payments where the date is in the past.

        Args:
            is_active: Filter by active status. If None, returns all
                payments regardless of status.
            category: Filter by subcategory name. If None, returns all categories.
            payment_type: Filter by payment type (subscription, debt, etc.).
                If None, returns all payment types. (DEPRECATED - use payment_mode)
            payment_mode: Filter by payment mode (recurring, one_time, debt, savings).
                If None, returns all payment modes.
            include_card: If True, eagerly load the payment_card relationship
                to avoid N+1 queries when accessing subscription.payment_card.
            include_relationships: If True, eagerly load all relationships
                (payment_card, category_rel, payment_history) for PDF reports
                and other use cases that need full data without lazy loading.

        Returns:
            Sequence of Subscription objects matching the filters,
            ordered by next_payment_date.

        Note:
            Uses composite indexes for optimal query performance:
            - ix_subscriptions_user_active_next_payment (user_id, is_active, next_payment_date)
            - ix_subscriptions_user_payment_type_active (user_id, payment_type, is_active)
            - ix_subscriptions_user_category (user_id, category)
            - ix_subscriptions_payment_mode (payment_mode)

        Example:
            >>> # Get all active subscriptions
            >>> active = await service.get_all(is_active=True)
            >>> print(len(active))

            >>> # Get entertainment subscriptions
            >>> entertainment = await service.get_all(category="entertainment")

            >>> # Get all debt payments (new way)
            >>> debts = await service.get_all(payment_mode=PaymentMode.DEBT)

            >>> # Get subscriptions with card info (avoids N+1)
            >>> subs = await service.get_all(is_active=True, include_card=True)
        """
        query = select(Subscription)

        # Eager load all relationships if requested (for PDF reports, etc.)
        if include_relationships:
            query = query.options(
                selectinload(Subscription.payment_card),
                selectinload(Subscription.category_rel),
                selectinload(Subscription.payment_history),
            )
        # Eager load payment_card if requested
        elif include_card:
            query = query.options(selectinload(Subscription.payment_card))

        conditions = []
        # Always filter by user_id if not "default" - uses composite index
        if self.user_id and self.user_id != "default":
            conditions.append(Subscription.user_id == self.user_id)
        if is_active is not None:
            conditions.append(Subscription.is_active == is_active)
        if category:
            conditions.append(Subscription.category == category)
        if payment_type is not None:
            conditions.append(Subscription.payment_type == payment_type)
        if payment_mode is not None:
            conditions.append(Subscription.payment_mode == payment_mode)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query.order_by(Subscription.next_payment_date))
        subscriptions = list(result.scalars().all())

        # Auto-advance next_payment_date for subscriptions where it's in the past
        # Also auto-deactivate subscriptions that have passed their end_date
        today = date.today()
        updated = False
        for sub in subscriptions:
            # Auto-deactivate if end_date has passed
            if sub.end_date and sub.end_date < today and sub.is_active:
                sub.is_active = False
                updated = True
                continue

            if sub.next_payment_date < today and sub.is_active:
                new_date = self._calculate_next_payment(
                    sub.start_date, sub.frequency, sub.frequency_interval
                )
                if new_date != sub.next_payment_date:
                    sub.next_payment_date = new_date
                    updated = True

        if updated:
            await self.db.flush()

        return subscriptions

    async def update(
        self,
        subscription_id: str,
        data: SubscriptionUpdate,
    ) -> Subscription | None:
        """Update an existing subscription.

        Updates a subscription with the provided data. If frequency or
        start_date are changed, the next_payment_date is automatically
        recalculated.

        Args:
            subscription_id: UUID of the subscription to update.
            data: Update data. Only fields that are set will be updated.

        Returns:
            The updated Subscription object, or None if not found.

        Example:
            >>> update_data = SubscriptionUpdate(amount=Decimal("19.99"))
            >>> updated = await service.update("uuid-string", update_data)
            >>> if updated:
            ...     print(f"New amount: {updated.amount}")
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)

        # Recalculate next payment if frequency changed
        if "frequency" in update_data or "start_date" in update_data:
            subscription.next_payment_date = self._calculate_next_payment(
                subscription.start_date,
                subscription.frequency,
                subscription.frequency_interval,
            )

        await self.db.flush()
        await self.db.refresh(subscription)

        # Re-index note if it was updated
        if "notes" in update_data:
            await self._index_note(subscription.id, subscription.notes)

        logger.info(f"Updated subscription: {subscription.name} ({subscription.id})")
        return subscription

    async def delete(self, subscription_id: str) -> bool:
        """Delete a subscription.

        Permanently removes a subscription from the database.

        Args:
            subscription_id: UUID of the subscription to delete.

        Returns:
            True if the subscription was deleted, False if not found.

        Example:
            >>> deleted = await service.delete("uuid-string")
            >>> if deleted:
            ...     print("Subscription deleted successfully")
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False

        await self.db.delete(subscription)
        logger.info(f"Deleted subscription: {subscription.name} ({subscription_id})")
        return True

    async def get_summary(
        self,
        currency_service: "CurrencyService | None" = None,
        display_currency: str | None = None,
        payment_type: PaymentType | None = None,
    ) -> SubscriptionSummary:
        """Get spending summary for all active subscriptions/payments.

        Calculates comprehensive spending analytics including total monthly
        and yearly costs, breakdown by category and payment type, and
        upcoming payments. All amounts are converted to the display currency.

        Args:
            currency_service: Optional currency service for conversion.
                If not provided, amounts are summed without conversion.
            display_currency: Currency to convert all amounts to.
                Defaults to settings.default_currency (GBP).
            payment_type: Optional filter for specific payment type.
                If None, includes all payment types.

        Returns:
            SubscriptionSummary object containing:
            - total_monthly: Total monthly spending (all payments normalized)
            - total_yearly: Total yearly spending
            - active_count: Number of active payments
            - by_category: Dict mapping subcategory names to monthly amounts
            - by_payment_type: Dict mapping payment types to monthly amounts
            - upcoming_week: List of payments due in the next 7 days
            - total_debt: Sum of all remaining debt balances
            - total_savings_target: Sum of all savings goals
            - total_current_saved: Sum of all current savings

        Example:
            >>> summary = await service.get_summary()
            >>> print(f"Monthly: £{summary.total_monthly}")
            >>> print(f"Yearly: £{summary.total_yearly}")
            >>> print(f"Total debt: £{summary.total_debt}")
            >>> for ptype, amount in summary.by_payment_type.items():
            ...     print(f"  {ptype}: £{amount}")
        """
        subscriptions = await self.get_all(is_active=True, payment_type=payment_type)
        target_currency = display_currency or settings.default_currency

        total_monthly = Decimal("0")
        by_category: dict[str, Decimal] = {}
        by_payment_type: dict[str, Decimal] = {}
        by_payment_mode: dict[str, Decimal] = {}
        total_debt = Decimal("0")
        total_savings_target = Decimal("0")
        total_current_saved = Decimal("0")

        for sub in subscriptions:
            # Skip ONE_TIME payments from monthly calculations
            # They are one-off costs, not recurring
            is_one_time = sub.payment_type == PaymentType.ONE_TIME

            monthly = self._to_monthly_amount(sub.amount, sub.frequency, sub.frequency_interval)

            # Convert to display currency if currency service provided
            if currency_service and sub.currency != target_currency:
                try:
                    monthly = await currency_service.convert(monthly, sub.currency, target_currency)
                except Exception as e:
                    logger.warning(f"Currency conversion failed for {sub.name}: {e}")
                    # Fall back to unconverted amount

            # Only add to monthly total if it's a recurring payment
            if not is_one_time:
                total_monthly += monthly

            # Group by category (subcategory) - include one-time for tracking
            cat = sub.category or "Uncategorized"
            by_category[cat] = by_category.get(cat, Decimal("0")) + (
                Decimal("0") if is_one_time else monthly
            )

            # Group by payment type (deprecated) - show one-time as total amount, not monthly
            ptype = sub.payment_type.value
            if is_one_time:
                # For one-time, show the actual amount, not monthly equivalent
                amount_to_show = sub.amount
                if currency_service and sub.currency != target_currency:
                    try:
                        amount_to_show = await currency_service.convert(
                            amount_to_show, sub.currency, target_currency
                        )
                    except Exception:
                        pass
                by_payment_type[ptype] = by_payment_type.get(ptype, Decimal("0")) + amount_to_show
            else:
                by_payment_type[ptype] = by_payment_type.get(ptype, Decimal("0")) + monthly

            # Group by payment mode (new) - show one-time as total amount, not monthly
            pmode = sub.payment_mode.value if sub.payment_mode else PaymentMode.RECURRING.value
            if is_one_time:
                by_payment_mode[pmode] = by_payment_mode.get(pmode, Decimal("0")) + amount_to_show
            else:
                by_payment_mode[pmode] = by_payment_mode.get(pmode, Decimal("0")) + monthly

            # Track debt totals - fall back to total_owed if remaining_balance not set
            if sub.payment_type == PaymentType.DEBT:
                # Prefer remaining_balance, fall back to total_owed
                debt_balance = sub.remaining_balance or sub.total_owed
                if debt_balance:
                    if currency_service and sub.currency != target_currency:
                        try:
                            debt_balance = await currency_service.convert(
                                debt_balance, sub.currency, target_currency
                            )
                        except Exception:
                            pass  # Use unconverted
                    total_debt += debt_balance
                elif sub.total_owed is None and sub.remaining_balance is None:
                    logger.warning(f"Debt '{sub.name}' ({sub.id}) has no balance information set")

            # Track savings totals with validation
            if sub.payment_type == PaymentType.SAVINGS:
                # Warn if savings goal has no target
                if not sub.target_amount:
                    logger.warning(f"Savings goal '{sub.name}' ({sub.id}) has no target_amount set")
                else:
                    target = sub.target_amount
                    if currency_service and sub.currency != target_currency:
                        try:
                            target = await currency_service.convert(
                                target, sub.currency, target_currency
                            )
                        except Exception:
                            pass
                    total_savings_target += target

                # Handle current_saved - default to 0 if not set
                saved = sub.current_saved or Decimal("0")
                if currency_service and sub.currency != target_currency:
                    try:
                        saved = await currency_service.convert(saved, sub.currency, target_currency)
                    except Exception:
                        pass
                total_current_saved += saved

                # Warn if current_saved exceeds target_amount (over-saved)
                if (
                    sub.target_amount
                    and sub.current_saved
                    and sub.current_saved > sub.target_amount
                ):
                    logger.info(
                        f"Savings goal '{sub.name}' ({sub.id}) has exceeded target: "
                        f"{sub.current_saved} > {sub.target_amount}"
                    )

        # Get upcoming week - payments due from today through next 7 days
        # Note: today's date uses local timezone; consider UTC for consistency
        today = date.today()
        week_later = today + timedelta(days=7)
        # Include payments due from today (inclusive) through week_later (inclusive)
        # Filter to only recurring payments - exclude one-time and fully completed installments
        upcoming = [
            s
            for s in subscriptions
            if today <= s.next_payment_date <= week_later
            and s.payment_type != PaymentType.ONE_TIME
            and not (
                s.is_installment
                and s.total_installments
                and s.completed_installments >= s.total_installments
            )
        ]

        return SubscriptionSummary(
            total_monthly=round(total_monthly, 2),
            total_yearly=round(total_monthly * 12, 2),
            active_count=len(subscriptions),
            by_category={k: round(v, 2) for k, v in by_category.items()},
            by_payment_type={k: round(v, 2) for k, v in by_payment_type.items()},
            by_payment_mode={k: round(v, 2) for k, v in by_payment_mode.items()},
            upcoming_week=[SubscriptionResponse.model_validate(s) for s in upcoming],
            currency=target_currency,
            total_debt=round(total_debt, 2),
            total_savings_target=round(total_savings_target, 2),
            total_current_saved=round(total_current_saved, 2),
        )

    async def get_upcoming(self, days: int = 7) -> Sequence[Subscription]:
        """Get subscriptions with payments due in the next N days.

        Args:
            days: Number of days to look ahead (default: 7).

        Returns:
            Sequence of subscriptions due within the specified period,
            ordered by next_payment_date.

        Note:
            Uses the ix_subscriptions_user_active_next_payment index for
            optimal query performance when filtering by user_id, is_active,
            and next_payment_date.

        Example:
            >>> upcoming = await service.get_upcoming(days=30)
            >>> for sub in upcoming:
            ...     print(f"{sub.name}: {sub.next_payment_date}")
        """
        today = date.today()
        end_date = today + timedelta(days=days)

        conditions = [
            Subscription.is_active == True,  # noqa: E712
            Subscription.next_payment_date >= today,
            Subscription.next_payment_date <= end_date,
        ]

        # Filter by user_id if not "default" - uses composite index
        if self.user_id and self.user_id != "default":
            conditions.insert(0, Subscription.user_id == self.user_id)

        result = await self.db.execute(
            select(Subscription).where(and_(*conditions)).order_by(Subscription.next_payment_date)
        )
        return result.scalars().all()

    def _calculate_next_payment(
        self,
        start: date,
        frequency: Frequency,
        interval: int,
    ) -> date:
        """Calculate the next payment date from start date.

        Iterates forward from the start date using the specified frequency
        and interval until reaching a future date.

        Args:
            start: The subscription start date.
            frequency: Payment frequency (DAILY, WEEKLY, MONTHLY, etc.).
            interval: Number of frequency periods between payments
                (e.g., 2 for "every 2 weeks").

        Returns:
            The next payment date (always in the future or today).

        Example:
            >>> # Monthly subscription starting Jan 1
            >>> next_date = service._calculate_next_payment(
            ...     date(2025, 1, 1),
            ...     Frequency.MONTHLY,
            ...     1
            ... )
        """
        today = date.today()
        next_date = start

        delta = self._get_delta(frequency, interval)

        while next_date < today:
            next_date += delta

        return next_date

    def _get_delta(self, frequency: Frequency, interval: int) -> relativedelta:
        """Get relativedelta for a frequency and interval.

        Maps frequency enum values to appropriate relativedelta objects
        for date arithmetic.

        Args:
            frequency: Payment frequency enum value.
            interval: Multiplier for the frequency.

        Returns:
            relativedelta object for the specified frequency.

        Example:
            >>> delta = service._get_delta(Frequency.WEEKLY, 2)
            >>> # Returns relativedelta(weeks=2)
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
                return relativedelta(days=interval)

    def _to_monthly_amount(
        self,
        amount: Decimal,
        frequency: Frequency,
        interval: int,
    ) -> Decimal:
        """Convert a subscription amount to its monthly equivalent.

        Normalizes amounts from different frequencies to monthly for
        comparison and summation. Uses accurate conversion factors:
        - Daily: 365.25/12 = 30.4375 days per month (accounts for leap years)
        - Weekly: 52.1775/12 = 4.348125 weeks per month
        - Biweekly: 26.08875/12 = 2.174 biweeks per month

        Args:
            amount: The subscription amount per payment.
            frequency: Payment frequency.
            interval: Frequency interval.

        Returns:
            Equivalent monthly amount as Decimal.

        Example:
            >>> # £120 yearly = £10 monthly
            >>> monthly = service._to_monthly_amount(
            ...     Decimal("120"),
            ...     Frequency.YEARLY,
            ...     1
            ... )
            >>> print(monthly)
            Decimal('10')
        """
        # Use more accurate conversion factors based on average days per year (365.25)
        # This accounts for leap years and provides consistent calculations
        days_per_month = Decimal("30.4375")  # 365.25 / 12
        weeks_per_month = Decimal("4.348125")  # 52.1775 / 12
        biweeks_per_month = Decimal("2.174063")  # 26.08875 / 12

        match frequency:
            case Frequency.DAILY:
                return amount * days_per_month / interval
            case Frequency.WEEKLY:
                return amount * weeks_per_month / interval
            case Frequency.BIWEEKLY:
                return amount * biweeks_per_month / interval
            case Frequency.MONTHLY:
                return amount / interval
            case Frequency.QUARTERLY:
                return amount / (3 * interval)
            case Frequency.YEARLY:
                return amount / (12 * interval)
            case Frequency.CUSTOM:
                # CUSTOM uses interval as months (e.g., every 6 months)
                return amount / interval
