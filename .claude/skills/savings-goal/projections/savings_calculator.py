"""Savings goal calculators and projections.

This module provides calculation functions for savings goal management
including contribution calculations, achievement projections, and milestone tracking.
"""

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_UP, Decimal
from enum import Enum
from typing import NamedTuple

from dateutil.relativedelta import relativedelta


class ContributionFrequency(Enum):
    """Contribution frequency options."""

    WEEKLY = "weekly"
    BI_WEEKLY = "bi-weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class SavingsGoal:
    """Represents a savings goal."""

    id: str
    name: str
    target_amount: Decimal
    current_saved: Decimal
    contribution_amount: Decimal
    frequency: ContributionFrequency = ContributionFrequency.MONTHLY
    target_date: date | None = None
    start_date: date = field(default_factory=date.today)
    category: str = "general"


@dataclass
class Contribution:
    """Represents a single contribution."""

    date: date
    amount: Decimal
    goal_id: str


class ProjectionResult(NamedTuple):
    """Result of a savings projection."""

    achievement_date: date | None
    months_remaining: int
    on_track: bool
    required_contribution: Decimal
    total_contributions_needed: int


class ContributionScenario(NamedTuple):
    """A contribution scenario."""

    name: str
    contribution: Decimal
    achievement_date: date
    months_to_goal: int
    is_current: bool


class Milestone(NamedTuple):
    """A savings milestone."""

    percentage: int
    amount: Decimal
    achieved: bool
    achieved_date: date | None
    projected_date: date | None


def calculate_progress(goal: SavingsGoal) -> dict:
    """Calculate progress on a savings goal.

    Args:
        goal: The savings goal.

    Returns:
        Dictionary with progress metrics.
    """
    remaining = goal.target_amount - goal.current_saved
    percentage = (
        (goal.current_saved / goal.target_amount * 100)
        if goal.target_amount > 0
        else Decimal("100")
    )

    return {
        "target_amount": goal.target_amount,
        "current_saved": goal.current_saved,
        "remaining": max(remaining, Decimal("0")),
        "percentage": percentage.quantize(Decimal("0.1")),
        "is_complete": goal.current_saved >= goal.target_amount,
    }


def _periods_per_year(frequency: ContributionFrequency) -> int:
    """Get number of contribution periods per year."""
    periods = {
        ContributionFrequency.WEEKLY: 52,
        ContributionFrequency.BI_WEEKLY: 26,
        ContributionFrequency.MONTHLY: 12,
        ContributionFrequency.QUARTERLY: 4,
    }
    return periods.get(frequency, 12)


def _days_per_period(frequency: ContributionFrequency) -> float:
    """Get average days per contribution period."""
    days = {
        ContributionFrequency.WEEKLY: 7,
        ContributionFrequency.BI_WEEKLY: 14,
        ContributionFrequency.MONTHLY: 30.44,
        ContributionFrequency.QUARTERLY: 91.31,
    }
    return days.get(frequency, 30.44)


def calculate_required_contribution(
    target_amount: Decimal,
    current_saved: Decimal,
    target_date: date,
    frequency: ContributionFrequency = ContributionFrequency.MONTHLY,
    round_to: Decimal = Decimal("5"),
) -> Decimal:
    """Calculate required contribution to meet target date.

    Args:
        target_amount: Goal amount.
        current_saved: Current savings.
        target_date: Target achievement date.
        frequency: Contribution frequency.
        round_to: Round up to nearest amount (default £5).

    Returns:
        Required contribution amount per period.
    """
    remaining = target_amount - current_saved

    if remaining <= 0:
        return Decimal("0")

    days_until_target = (target_date - date.today()).days

    if days_until_target <= 0:
        return remaining  # Lump sum needed immediately

    days_per_period = _days_per_period(frequency)
    periods = Decimal(str(days_until_target / days_per_period))

    if periods <= 0:
        return remaining

    contribution = remaining / periods

    # Round up to nearest increment
    if round_to > 0:
        contribution = (contribution / round_to).quantize(
            Decimal("1"), rounding=ROUND_UP
        ) * round_to

    return contribution.quantize(Decimal("0.01"))


def project_achievement_date(
    target_amount: Decimal,
    current_saved: Decimal,
    contribution: Decimal,
    frequency: ContributionFrequency = ContributionFrequency.MONTHLY,
) -> date | None:
    """Project when goal will be achieved.

    Args:
        target_amount: Goal amount.
        current_saved: Current savings.
        contribution: Contribution amount per period.
        frequency: Contribution frequency.

    Returns:
        Projected achievement date, or None if never achievable.
    """
    remaining = target_amount - current_saved

    if remaining <= 0:
        return date.today()

    if contribution <= 0:
        return None  # Will never achieve

    periods_needed = math.ceil(float(remaining / contribution))

    if frequency == ContributionFrequency.WEEKLY:
        return date.today() + timedelta(weeks=periods_needed)
    elif frequency == ContributionFrequency.BI_WEEKLY:
        return date.today() + timedelta(weeks=periods_needed * 2)
    elif frequency == ContributionFrequency.QUARTERLY:
        return date.today() + relativedelta(months=periods_needed * 3)
    else:  # MONTHLY
        return date.today() + relativedelta(months=periods_needed)


def generate_scenarios(
    goal: SavingsGoal,
    accelerated_multiplier: Decimal = Decimal("1.5"),
    comfortable_multiplier: Decimal = Decimal("0.75"),
) -> list[ContributionScenario]:
    """Generate contribution scenarios for a goal.

    Args:
        goal: The savings goal.
        accelerated_multiplier: Multiplier for accelerated scenario.
        comfortable_multiplier: Multiplier for comfortable scenario.

    Returns:
        List of contribution scenarios.
    """
    scenarios = []
    remaining = goal.target_amount - goal.current_saved

    if remaining <= 0:
        return []

    # Current scenario
    if goal.contribution_amount > 0:
        current_date = project_achievement_date(
            goal.target_amount,
            goal.current_saved,
            goal.contribution_amount,
            goal.frequency,
        )
        if current_date:
            months = (
                (current_date.year - date.today().year) * 12
                + (current_date.month - date.today().month)
            )
            scenarios.append(
                ContributionScenario(
                    name="current",
                    contribution=goal.contribution_amount,
                    achievement_date=current_date,
                    months_to_goal=months,
                    is_current=True,
                )
            )

    # On-track scenario (if target date exists)
    if goal.target_date and goal.target_date > date.today():
        on_track_contribution = calculate_required_contribution(
            goal.target_amount,
            goal.current_saved,
            goal.target_date,
            goal.frequency,
        )
        if on_track_contribution > 0:
            scenarios.append(
                ContributionScenario(
                    name="on_track",
                    contribution=on_track_contribution,
                    achievement_date=goal.target_date,
                    months_to_goal=(
                        (goal.target_date.year - date.today().year) * 12
                        + (goal.target_date.month - date.today().month)
                    ),
                    is_current=False,
                )
            )

    # Accelerated scenario
    base_contribution = goal.contribution_amount or Decimal("100")
    accelerated = (base_contribution * accelerated_multiplier).quantize(Decimal("0.01"))
    accelerated_date = project_achievement_date(
        goal.target_amount,
        goal.current_saved,
        accelerated,
        goal.frequency,
    )
    if accelerated_date:
        months = (
            (accelerated_date.year - date.today().year) * 12
            + (accelerated_date.month - date.today().month)
        )
        scenarios.append(
            ContributionScenario(
                name="accelerated",
                contribution=accelerated,
                achievement_date=accelerated_date,
                months_to_goal=months,
                is_current=False,
            )
        )

    # Comfortable scenario
    comfortable = (base_contribution * comfortable_multiplier).quantize(Decimal("0.01"))
    comfortable_date = project_achievement_date(
        goal.target_amount,
        goal.current_saved,
        comfortable,
        goal.frequency,
    )
    if comfortable_date:
        months = (
            (comfortable_date.year - date.today().year) * 12
            + (comfortable_date.month - date.today().month)
        )
        scenarios.append(
            ContributionScenario(
                name="comfortable",
                contribution=comfortable,
                achievement_date=comfortable_date,
                months_to_goal=months,
                is_current=False,
            )
        )

    return scenarios


def calculate_milestones(
    goal: SavingsGoal,
    milestone_percentages: list[int] | None = None,
) -> list[Milestone]:
    """Calculate milestone status for a goal.

    Args:
        goal: The savings goal.
        milestone_percentages: List of milestone percentages.

    Returns:
        List of milestones with status.
    """
    if milestone_percentages is None:
        milestone_percentages = [10, 25, 50, 75, 90, 100]

    milestones = []
    current_percentage = float(goal.current_saved / goal.target_amount * 100)

    for pct in milestone_percentages:
        milestone_amount = goal.target_amount * Decimal(str(pct / 100))
        achieved = current_percentage >= pct

        # Calculate projected date for unachieved milestones
        projected_date = None
        if not achieved and goal.contribution_amount > 0:
            remaining_to_milestone = milestone_amount - goal.current_saved
            if remaining_to_milestone > 0:
                periods_needed = math.ceil(
                    float(remaining_to_milestone / goal.contribution_amount)
                )
                if goal.frequency == ContributionFrequency.MONTHLY:
                    projected_date = date.today() + relativedelta(months=periods_needed)
                elif goal.frequency == ContributionFrequency.WEEKLY:
                    projected_date = date.today() + timedelta(weeks=periods_needed)

        milestones.append(
            Milestone(
                percentage=pct,
                amount=milestone_amount.quantize(Decimal("0.01")),
                achieved=achieved,
                achieved_date=None,  # Would need contribution history
                projected_date=projected_date,
            )
        )

    return milestones


def calculate_streak(
    contributions: list[Contribution],
    frequency: ContributionFrequency = ContributionFrequency.MONTHLY,
) -> int:
    """Calculate current contribution streak.

    Args:
        contributions: List of contributions sorted by date.
        frequency: Expected contribution frequency.

    Returns:
        Current streak in periods.
    """
    if not contributions:
        return 0

    sorted_contributions = sorted(contributions, key=lambda c: c.date, reverse=True)
    streak = 0
    expected_date = date.today()

    for contrib in sorted_contributions:
        if frequency == ContributionFrequency.MONTHLY:
            period_start = expected_date.replace(day=1)
            period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)
        elif frequency == ContributionFrequency.WEEKLY:
            # Week starts on Monday
            period_start = expected_date - timedelta(days=expected_date.weekday())
            period_end = period_start + timedelta(days=6)
        else:
            # Default to monthly
            period_start = expected_date.replace(day=1)
            period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)

        if period_start <= contrib.date <= period_end:
            streak += 1
            # Move to previous period
            if frequency == ContributionFrequency.MONTHLY:
                expected_date = period_start - timedelta(days=1)
            elif frequency == ContributionFrequency.WEEKLY:
                expected_date = period_start - timedelta(days=1)
        else:
            break

    return streak


def check_on_track(goal: SavingsGoal) -> dict:
    """Check if goal is on track to meet target date.

    Args:
        goal: The savings goal.

    Returns:
        Dictionary with on-track status and recommendations.
    """
    if not goal.target_date:
        return {
            "has_target_date": False,
            "on_track": None,
            "message": "No target date set",
        }

    if goal.target_date <= date.today():
        return {
            "has_target_date": True,
            "on_track": goal.current_saved >= goal.target_amount,
            "message": (
                "Goal complete!"
                if goal.current_saved >= goal.target_amount
                else "Target date has passed"
            ),
        }

    required = calculate_required_contribution(
        goal.target_amount,
        goal.current_saved,
        goal.target_date,
        goal.frequency,
    )

    on_track = goal.contribution_amount >= required
    difference = goal.contribution_amount - required

    if on_track:
        message = "You're on track to meet your goal!"
        if difference > 10:
            projected = project_achievement_date(
                goal.target_amount,
                goal.current_saved,
                goal.contribution_amount,
                goal.frequency,
            )
            if projected and projected < goal.target_date:
                days_early = (goal.target_date - projected).days
                message = f"You're ahead of schedule by about {days_early} days!"
    else:
        message = f"Increase your contribution by £{abs(difference):.2f} to meet your target date"

    return {
        "has_target_date": True,
        "on_track": on_track,
        "current_contribution": goal.contribution_amount,
        "required_contribution": required,
        "difference": difference,
        "message": message,
    }
