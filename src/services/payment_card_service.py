"""Payment Card service for managing payment methods.

This module provides CRUD operations for payment cards and
calculates required balances per card based on subscriptions.
"""

import logging
import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.payment_card import PaymentCard
from src.models.subscription import PaymentHistory, PaymentStatus, Subscription
from src.schemas.payment_card import (
    AllCardsBalanceSummary,
    CardBalanceSummary,
    PaymentCardCreate,
    PaymentCardUpdate,
)

logger = logging.getLogger(__name__)


class PaymentCardService:
    """Service for payment card management.

    Handles CRUD operations for payment cards and calculates
    required balances per card based on linked subscriptions.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the payment card service."""
        self.db = db

    async def create(self, data: PaymentCardCreate) -> PaymentCard:
        """Create a new payment card."""
        card = PaymentCard(
            id=str(uuid.uuid4()),
            name=data.name,
            card_type=data.card_type,
            last_four=data.last_four,
            bank_name=data.bank_name,
            currency=data.currency,
            color=data.color,
            icon_url=data.icon_url,
            notes=data.notes,
            sort_order=data.sort_order,
            funding_card_id=data.funding_card_id,
        )
        self.db.add(card)
        await self.db.flush()
        await self.db.refresh(card)
        logger.info(f"Created payment card: {card.name}")
        return card

    async def get_by_id(self, card_id: str) -> PaymentCard | None:
        """Get a payment card by ID."""
        result = await self.db.execute(
            select(PaymentCard)
            .options(selectinload(PaymentCard.funding_card))
            .where(PaymentCard.id == card_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, is_active: bool | None = None) -> Sequence[PaymentCard]:
        """Get all payment cards, optionally filtered by active status."""
        query = select(PaymentCard).options(selectinload(PaymentCard.funding_card))
        if is_active is not None:
            query = query.where(PaymentCard.is_active == is_active)
        query = query.order_by(PaymentCard.sort_order, PaymentCard.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, card_id: str, data: PaymentCardUpdate) -> PaymentCard | None:
        """Update a payment card."""
        card = await self.get_by_id(card_id)
        if not card:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        await self.db.flush()
        await self.db.refresh(card)
        logger.info(f"Updated payment card: {card.name}")
        return card

    async def delete(self, card_id: str) -> bool:
        """Delete a payment card."""
        card = await self.get_by_id(card_id)
        if not card:
            return False

        await self.db.delete(card)
        await self.db.flush()
        logger.info(f"Deleted payment card: {card.name}")
        return True

    async def get_balance_summary(
        self,
        currency_service=None,
        target_currency: str = "GBP",
    ) -> AllCardsBalanceSummary:
        """Get balance summary for all cards.

        Calculates how much money is needed on each card for this month
        and next month based on linked subscriptions. Also includes
        amounts already paid this month from payment history.

        Cards with a funding_card_id will have their payments aggregated
        to the funding card (e.g., PayPal payments show under Monzo).
        """
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)
        next_month_start = month_start + relativedelta(months=1)
        next_month_end = (next_month_start + relativedelta(months=1)) - relativedelta(days=1)

        # Get all active cards
        cards = await self.get_all(is_active=True)

        # Get all active subscriptions
        result = await self.db.execute(
            select(Subscription).where(Subscription.is_active == True)  # noqa: E712
        )
        subscriptions = result.scalars().all()

        # Get completed payments this month for all subscriptions
        payment_result = await self.db.execute(
            select(PaymentHistory).where(
                and_(
                    PaymentHistory.payment_date >= month_start,
                    PaymentHistory.payment_date <= month_end,
                    PaymentHistory.status == PaymentStatus.COMPLETED,
                )
            )
        )
        payments_this_month = payment_result.scalars().all()

        # Create a map of subscription_id -> total paid this month
        sub_payments_map: dict[str, Decimal] = {}
        for payment in payments_this_month:
            if payment.subscription_id not in sub_payments_map:
                sub_payments_map[payment.subscription_id] = Decimal("0")
            sub_payments_map[payment.subscription_id] += payment.amount

        # Build a map of card_id -> funding_card_id
        funding_map: dict[str, str] = {}
        for card in cards:
            if card.funding_card_id:
                funding_map[card.id] = card.funding_card_id

        # First pass: calculate direct subscriptions for each card
        card_data: dict[str, dict] = {}
        for card in cards:
            card_subs = [s for s in subscriptions if s.card_id == card.id]
            this_month = Decimal("0")
            paid_month = Decimal("0")
            next_month = Decimal("0")
            sub_names: list[str] = []

            for sub in card_subs:
                sub_names.append(sub.name)

                # Calculate payments this month
                this_month_payment = self._calculate_payment_in_range(sub, month_start, month_end)
                next_month_payment = self._calculate_payment_in_range(
                    sub, next_month_start, next_month_end
                )

                # Get paid amount for this subscription
                sub_paid = sub_payments_map.get(sub.id, Decimal("0"))

                # Convert currency if needed
                if currency_service and sub.currency != target_currency:
                    try:
                        if this_month_payment > 0:
                            this_month_payment = await currency_service.convert(
                                this_month_payment, sub.currency, target_currency
                            )
                        if next_month_payment > 0:
                            next_month_payment = await currency_service.convert(
                                next_month_payment, sub.currency, target_currency
                            )
                        if sub_paid > 0:
                            sub_paid = await currency_service.convert(
                                sub_paid, sub.currency, target_currency
                            )
                    except Exception as e:
                        logger.warning(f"Currency conversion failed: {e}")

                this_month += this_month_payment
                paid_month += sub_paid
                next_month += next_month_payment

            card_data[card.id] = {
                "card": card,
                "this_month": this_month,
                "paid_month": paid_month,
                "next_month": next_month,
                "sub_names": sub_names,
                "sub_count": len(card_subs),
                # For funded amounts (from cards that use this as funding card)
                "funded_this_month": Decimal("0"),
                "funded_next_month": Decimal("0"),
                "funded_sub_names": [],
                "funded_sub_count": 0,
            }

        # Second pass: aggregate funded card payments to their funding cards
        for card_id, funding_card_id in funding_map.items():
            if funding_card_id in card_data:
                funded_card = card_data[card_id]
                funding_card = card_data[funding_card_id]

                # Add funded card's payments to funding card's funded totals
                funding_card["funded_this_month"] += funded_card["this_month"]
                funding_card["funded_next_month"] += funded_card["next_month"]
                funding_card["funded_sub_names"].extend(funded_card["sub_names"])
                funding_card["funded_sub_count"] += funded_card["sub_count"]

        # Build summaries (exclude cards with funding_card_id from top-level totals)
        card_summaries: list[CardBalanceSummary] = []
        total_this_month = Decimal("0")
        total_paid_this_month = Decimal("0")
        total_next_month = Decimal("0")

        for card in cards:
            data = card_data[card.id]
            has_funding_card = card.funding_card_id is not None

            # Direct amounts (own subscriptions)
            direct_this = data["this_month"]
            direct_next = data["next_month"]
            paid = data["paid_month"]

            # Funded amounts (from cards using this as funding card)
            funded_this = data["funded_this_month"]
            funded_next = data["funded_next_month"]

            # Total remaining includes both direct and funded
            total_due = direct_this + funded_this
            remaining_month = max(Decimal("0"), total_due - paid)

            card_summaries.append(
                CardBalanceSummary(
                    card_id=card.id,
                    card_name=card.name,
                    bank_name=card.bank_name,
                    color=card.color,
                    icon_url=card.icon_url,
                    currency=target_currency,
                    total_this_month=direct_this,
                    funded_this_month=funded_this,
                    paid_this_month=paid,
                    remaining_this_month=remaining_month,
                    total_next_month=direct_next,
                    funded_next_month=funded_next,
                    subscription_count=data["sub_count"],
                    funded_subscription_count=data["funded_sub_count"],
                    subscriptions=data["sub_names"],
                    funded_subscriptions=data["funded_sub_names"],
                )
            )

            # Only count cards without a funding card in totals (avoid double-counting)
            if not has_funding_card:
                total_this_month += direct_this
                total_paid_this_month += paid
                total_next_month += direct_next

        # Calculate unassigned subscriptions
        unassigned_count = 0
        unassigned_total = Decimal("0")
        unassigned_subs = [s for s in subscriptions if s.card_id is None]
        for sub in unassigned_subs:
            unassigned_count += 1
            payment = self._calculate_payment_in_range(sub, month_start, month_end)
            if currency_service and sub.currency != target_currency:
                try:
                    payment = await currency_service.convert(payment, sub.currency, target_currency)
                except Exception:
                    pass
            unassigned_total += payment

        # Calculate total remaining
        total_remaining = max(Decimal("0"), total_this_month - total_paid_this_month)

        return AllCardsBalanceSummary(
            cards=card_summaries,
            total_all_cards_this_month=total_this_month,
            total_paid_this_month=total_paid_this_month,
            total_remaining_this_month=total_remaining,
            total_all_cards_next_month=total_next_month,
            unassigned_count=unassigned_count,
            unassigned_total=unassigned_total,
        )

    def _calculate_payment_in_range(
        self,
        subscription: Subscription,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Calculate total payment amount for a subscription within a date range."""

        # Check if subscription has ended
        if subscription.end_date and subscription.end_date < start_date:
            return Decimal("0")

        delta = self._get_delta(subscription.frequency, subscription.frequency_interval)
        current = subscription.start_date

        # Move forward to start of range
        while current < start_date:
            current += delta

        # Effective end (respect subscription end_date)
        effective_end = end_date
        if subscription.end_date and subscription.end_date < end_date:
            effective_end = subscription.end_date

        # Count payments in range
        count = 0
        while current <= effective_end:
            count += 1
            current += delta

            # Safety limit for installments
            if subscription.is_installment and subscription.total_installments:
                remaining = subscription.total_installments - subscription.completed_installments
                if count >= remaining:
                    break

        return subscription.amount * count

    def _get_delta(self, frequency, interval: int):
        """Get relativedelta for a frequency and interval."""
        from src.models.subscription import Frequency

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
                return relativedelta(months=interval)
            case _:
                return relativedelta(months=1)
