"""Savings goal projections and calculations."""

from .savings_calculator import (
    Contribution,
    ContributionFrequency,
    ContributionScenario,
    Milestone,
    ProjectionResult,
    SavingsGoal,
    calculate_milestones,
    calculate_progress,
    calculate_required_contribution,
    calculate_streak,
    check_on_track,
    generate_scenarios,
    project_achievement_date,
)

__all__ = [
    "Contribution",
    "ContributionFrequency",
    "ContributionScenario",
    "Milestone",
    "ProjectionResult",
    "SavingsGoal",
    "calculate_milestones",
    "calculate_progress",
    "calculate_required_contribution",
    "calculate_streak",
    "check_on_track",
    "generate_scenarios",
    "project_achievement_date",
]
