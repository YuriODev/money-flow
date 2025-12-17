"""Debt interest and payoff calculators.

This module provides calculation functions for debt management features
including interest calculations, payoff projections, and strategy comparisons.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import NamedTuple


class PayoffStrategy(Enum):
    """Debt payoff strategy options."""

    AVALANCHE = "avalanche"  # Highest APR first
    SNOWBALL = "snowball"  # Lowest balance first


@dataclass
class Debt:
    """Represents a single debt."""

    id: str
    name: str
    balance: Decimal
    apr: Decimal  # Annual percentage rate (e.g., 22.9 for 22.9%)
    minimum_payment: Decimal
    debt_type: str = "credit_card"


@dataclass
class PayoffMonth:
    """Payment details for a single month."""

    month_number: int
    debt_name: str
    payment: Decimal
    principal: Decimal
    interest: Decimal
    remaining_balance: Decimal


class PayoffResult(NamedTuple):
    """Result of a payoff calculation."""

    months_to_payoff: int
    total_interest: Decimal
    debt_free_date: date
    schedule: list[PayoffMonth]
    milestones: list[str]


class StrategyComparison(NamedTuple):
    """Comparison between avalanche and snowball strategies."""

    avalanche_months: int
    avalanche_interest: Decimal
    avalanche_date: date
    snowball_months: int
    snowball_interest: Decimal
    snowball_date: date
    interest_saved: Decimal
    months_saved: int
    recommended: PayoffStrategy


def calculate_monthly_interest(balance: Decimal, apr: Decimal) -> Decimal:
    """Calculate monthly interest from annual percentage rate.

    Args:
        balance: Current debt balance.
        apr: Annual percentage rate (e.g., 22.9 for 22.9%).

    Returns:
        Monthly interest amount.

    Example:
        >>> calculate_monthly_interest(Decimal("1000"), Decimal("22.9"))
        Decimal("19.08")
    """
    monthly_rate = apr / Decimal("12") / Decimal("100")
    interest = balance * monthly_rate
    return interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_minimum_viable_payment(balance: Decimal, apr: Decimal) -> Decimal:
    """Calculate minimum payment needed to make progress.

    The minimum viable payment must exceed monthly interest.

    Args:
        balance: Current debt balance.
        apr: Annual percentage rate.

    Returns:
        Minimum payment to reduce principal.
    """
    monthly_interest = calculate_monthly_interest(balance, apr)
    # Add 1% of balance or £10, whichever is greater
    min_principal = max(balance * Decimal("0.01"), Decimal("10"))
    return (monthly_interest + min_principal).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_payoff(
    debts: list[Debt],
    extra_payment: Decimal = Decimal("0"),
    strategy: PayoffStrategy = PayoffStrategy.AVALANCHE,
    start_date: date | None = None,
) -> PayoffResult:
    """Calculate complete payoff schedule for all debts.

    Args:
        debts: List of debts to pay off.
        extra_payment: Additional monthly payment above minimums.
        strategy: Payoff strategy (avalanche or snowball).
        start_date: Starting date for projection.

    Returns:
        PayoffResult with timeline, interest, and schedule.
    """
    if not debts:
        return PayoffResult(
            months_to_payoff=0,
            total_interest=Decimal("0"),
            debt_free_date=start_date or date.today(),
            schedule=[],
            milestones=[],
        )

    start_date = start_date or date.today()

    # Create working copies of balances
    balances = {d.id: d.balance for d in debts}
    total_original = sum(d.balance for d in debts)
    total_minimum = sum(d.minimum_payment for d in debts)

    schedule: list[PayoffMonth] = []
    milestones: list[str] = []
    total_interest = Decimal("0")
    month = 0
    max_months = 600  # 50 year cap

    # Track milestones
    milestone_25 = False
    milestone_50 = False
    milestone_75 = False

    while any(b > 0 for b in balances.values()) and month < max_months:
        month += 1

        # Sort debts by strategy
        active_debts = [d for d in debts if balances[d.id] > 0]
        if strategy == PayoffStrategy.AVALANCHE:
            active_debts.sort(key=lambda d: d.apr, reverse=True)
        else:  # SNOWBALL
            active_debts.sort(key=lambda d: balances[d.id])

        available_extra = extra_payment

        for debt in active_debts:
            if balances[debt.id] <= 0:
                continue

            # Calculate interest
            interest = calculate_monthly_interest(balances[debt.id], debt.apr)
            total_interest += interest

            # Determine payment amount
            # First debt gets extra payment, others get minimum
            if debt.id == active_debts[0].id:
                payment = debt.minimum_payment + available_extra
                available_extra = Decimal("0")
            else:
                payment = debt.minimum_payment

            # Don't overpay
            payment = min(payment, balances[debt.id] + interest)

            # Calculate principal
            principal = payment - interest

            # Update balance
            balances[debt.id] -= principal
            if balances[debt.id] < Decimal("0.01"):
                balances[debt.id] = Decimal("0")
                milestones.append(f"Month {month}: {debt.name} paid off!")

            schedule.append(
                PayoffMonth(
                    month_number=month,
                    debt_name=debt.name,
                    payment=payment.quantize(Decimal("0.01")),
                    principal=principal.quantize(Decimal("0.01")),
                    interest=interest.quantize(Decimal("0.01")),
                    remaining_balance=balances[debt.id].quantize(Decimal("0.01")),
                )
            )

        # Check percentage milestones
        total_remaining = sum(balances.values())
        paid_percentage = (
            (total_original - total_remaining) / total_original * 100
            if total_original > 0
            else 100
        )

        if not milestone_25 and paid_percentage >= 25:
            milestone_25 = True
            milestones.append(f"Month {month}: 25% of debt paid off!")

        if not milestone_50 and paid_percentage >= 50:
            milestone_50 = True
            milestones.append(f"Month {month}: 50% of debt paid off! Halfway there!")

        if not milestone_75 and paid_percentage >= 75:
            milestone_75 = True
            milestones.append(f"Month {month}: 75% of debt paid off!")

    # Calculate debt-free date
    debt_free_date = date(
        start_date.year + month // 12, ((start_date.month - 1 + month) % 12) + 1, 1
    )

    return PayoffResult(
        months_to_payoff=month,
        total_interest=total_interest.quantize(Decimal("0.01")),
        debt_free_date=debt_free_date,
        schedule=schedule,
        milestones=milestones,
    )


def compare_strategies(
    debts: list[Debt],
    extra_payment: Decimal = Decimal("0"),
    start_date: date | None = None,
) -> StrategyComparison:
    """Compare avalanche vs snowball strategies.

    Args:
        debts: List of debts to analyze.
        extra_payment: Additional monthly payment above minimums.
        start_date: Starting date for projection.

    Returns:
        StrategyComparison with both strategies analyzed.
    """
    avalanche = calculate_payoff(debts, extra_payment, PayoffStrategy.AVALANCHE, start_date)
    snowball = calculate_payoff(debts, extra_payment, PayoffStrategy.SNOWBALL, start_date)

    interest_saved = snowball.total_interest - avalanche.total_interest
    months_saved = snowball.months_to_payoff - avalanche.months_to_payoff

    # Recommend avalanche unless snowball is significantly faster
    # (which shouldn't happen mathematically, but might feel faster)
    recommended = PayoffStrategy.AVALANCHE

    return StrategyComparison(
        avalanche_months=avalanche.months_to_payoff,
        avalanche_interest=avalanche.total_interest,
        avalanche_date=avalanche.debt_free_date,
        snowball_months=snowball.months_to_payoff,
        snowball_interest=snowball.total_interest,
        snowball_date=snowball.debt_free_date,
        interest_saved=interest_saved,
        months_saved=months_saved,
        recommended=recommended,
    )


def calculate_windfall_impact(
    debts: list[Debt],
    windfall_amount: Decimal,
    target_debt_id: str | None = None,
    strategy: PayoffStrategy = PayoffStrategy.AVALANCHE,
) -> dict:
    """Calculate impact of a one-time extra payment.

    Args:
        debts: Current list of debts.
        windfall_amount: One-time extra payment amount.
        target_debt_id: Specific debt to apply windfall to.
        strategy: Current payoff strategy.

    Returns:
        Dictionary with impact analysis.
    """
    # Calculate baseline without windfall
    baseline = calculate_payoff(debts, Decimal("0"), strategy)

    # Create modified debts with windfall applied
    modified_debts = []
    for debt in debts:
        if target_debt_id:
            if debt.id == target_debt_id:
                new_balance = max(debt.balance - windfall_amount, Decimal("0"))
            else:
                new_balance = debt.balance
        else:
            # Apply to first debt in strategy order
            sorted_debts = sorted(
                debts,
                key=lambda d: (
                    -d.apr if strategy == PayoffStrategy.AVALANCHE else d.balance
                ),
            )
            if debt.id == sorted_debts[0].id:
                new_balance = max(debt.balance - windfall_amount, Decimal("0"))
            else:
                new_balance = debt.balance

        modified_debts.append(
            Debt(
                id=debt.id,
                name=debt.name,
                balance=new_balance,
                apr=debt.apr,
                minimum_payment=debt.minimum_payment,
                debt_type=debt.debt_type,
            )
        )

    # Calculate with windfall
    with_windfall = calculate_payoff(modified_debts, Decimal("0"), strategy)

    return {
        "windfall_amount": windfall_amount,
        "months_saved": baseline.months_to_payoff - with_windfall.months_to_payoff,
        "interest_saved": baseline.total_interest - with_windfall.total_interest,
        "new_debt_free_date": with_windfall.debt_free_date,
        "original_debt_free_date": baseline.debt_free_date,
    }


def calculate_progress(
    original_debts: list[Debt],
    current_debts: list[Debt],
    start_date: date,
) -> dict:
    """Calculate progress on debt payoff journey.

    Args:
        original_debts: Debts at start of journey.
        current_debts: Current debt balances.
        start_date: When the journey started.

    Returns:
        Dictionary with progress metrics.
    """
    original_total = sum(d.balance for d in original_debts)
    current_total = sum(d.balance for d in current_debts)

    paid_off = original_total - current_total
    percentage = (
        (paid_off / original_total * 100) if original_total > 0 else Decimal("100")
    )

    months_elapsed = (
        (date.today().year - start_date.year) * 12
        + (date.today().month - start_date.month)
    )

    # Count fully paid debts
    current_ids = {d.id for d in current_debts if d.balance > 0}
    original_ids = {d.id for d in original_debts}
    paid_off_debts = [
        d for d in original_debts if d.id in original_ids and d.id not in current_ids
    ]

    return {
        "original_total": original_total,
        "current_total": current_total,
        "total_paid_off": paid_off,
        "percentage_complete": percentage.quantize(Decimal("0.1")),
        "months_elapsed": months_elapsed,
        "debts_paid_off": len(paid_off_debts),
        "debts_remaining": len([d for d in current_debts if d.balance > 0]),
        "monthly_progress": (
            (paid_off / months_elapsed) if months_elapsed > 0 else Decimal("0")
        ),
    }
