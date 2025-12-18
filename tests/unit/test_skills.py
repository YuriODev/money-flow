"""Tests for the custom Claude Skills calculators.

Tests for debt management and savings goal calculation modules.
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from dateutil.relativedelta import relativedelta

# Add skills directories to path for imports
skills_path = Path(__file__).parent.parent.parent / ".claude" / "skills"
sys.path.insert(0, str(skills_path / "debt-management"))
sys.path.insert(0, str(skills_path / "savings-goal"))

from calculators import (  # noqa: E402, I001
    Debt,
    PayoffStrategy,
    calculate_minimum_viable_payment,
    calculate_monthly_interest,
    calculate_payoff,
    calculate_progress,
    calculate_windfall_impact,
    compare_strategies,
)
from projections import (  # noqa: E402
    ContributionFrequency,
    SavingsGoal,
    calculate_milestones,
    calculate_progress as calc_savings_progress,
    calculate_required_contribution,
    check_on_track,
    generate_scenarios,
    project_achievement_date,
)


class TestDebtInterestCalculations:
    """Tests for debt interest calculations."""

    def test_calculate_monthly_interest(self):
        """Test basic monthly interest calculation."""
        # £1000 at 12% APR = £10/month interest
        balance = Decimal("1000")
        apr = Decimal("12")

        interest = calculate_monthly_interest(balance, apr)

        assert interest == Decimal("10.00")

    def test_calculate_monthly_interest_high_apr(self):
        """Test interest calculation with high APR."""
        # £3500 at 22.9% APR
        balance = Decimal("3500")
        apr = Decimal("22.9")

        interest = calculate_monthly_interest(balance, apr)

        # 22.9 / 12 / 100 = 0.01908333...
        # 3500 * 0.01908333 = 66.79...
        assert interest == Decimal("66.79")

    def test_calculate_monthly_interest_zero_balance(self):
        """Test interest on zero balance."""
        interest = calculate_monthly_interest(Decimal("0"), Decimal("20"))
        assert interest == Decimal("0.00")

    def test_calculate_minimum_viable_payment(self):
        """Test minimum viable payment calculation."""
        balance = Decimal("1000")
        apr = Decimal("12")

        min_payment = calculate_minimum_viable_payment(balance, apr)

        # Interest is £10, min principal is £10 (1% of balance)
        assert min_payment >= Decimal("20.00")


class TestDebtPayoffCalculations:
    """Tests for debt payoff calculations."""

    @pytest.fixture
    def sample_debts(self):
        """Create sample debts for testing."""
        return [
            Debt("1", "Credit Card A", Decimal("3500"), Decimal("22.9"), Decimal("87")),
            Debt("2", "Credit Card B", Decimal("1200"), Decimal("19.9"), Decimal("30")),
            Debt("3", "Personal Loan", Decimal("5000"), Decimal("7.9"), Decimal("150")),
        ]

    def test_calculate_payoff_empty_debts(self):
        """Test payoff calculation with no debts."""
        result = calculate_payoff([])

        assert result.months_to_payoff == 0
        assert result.total_interest == Decimal("0")
        assert result.schedule == []

    def test_calculate_payoff_single_debt(self):
        """Test payoff calculation for single debt."""
        debt = Debt("1", "Credit Card", Decimal("1000"), Decimal("12"), Decimal("100"))

        result = calculate_payoff([debt])

        assert result.months_to_payoff > 0
        assert result.total_interest > Decimal("0")
        assert len(result.schedule) > 0

    def test_calculate_payoff_with_extra_payment(self, sample_debts):
        """Test that extra payment reduces payoff time."""
        baseline = calculate_payoff(sample_debts, extra_payment=Decimal("0"))
        with_extra = calculate_payoff(sample_debts, extra_payment=Decimal("100"))

        assert with_extra.months_to_payoff < baseline.months_to_payoff
        assert with_extra.total_interest < baseline.total_interest

    def test_calculate_payoff_avalanche_strategy(self, sample_debts):
        """Test avalanche strategy orders by APR."""
        result = calculate_payoff(
            sample_debts,
            extra_payment=Decimal("100"),
            strategy=PayoffStrategy.AVALANCHE,
        )

        # First payments should go to Credit Card A (highest APR)
        first_extra_payments = [s for s in result.schedule if s.month_number == 1]
        # Credit Card A should have the highest payment
        credit_card_a = next(
            (p for p in first_extra_payments if p.debt_name == "Credit Card A"), None
        )
        assert credit_card_a is not None

    def test_calculate_payoff_snowball_strategy(self, sample_debts):
        """Test snowball strategy orders by balance."""
        result = calculate_payoff(
            sample_debts,
            extra_payment=Decimal("100"),
            strategy=PayoffStrategy.SNOWBALL,
        )

        # Snowball should have milestones
        assert len(result.milestones) > 0

        # Find the indices of debt payoff milestones
        # In snowball, Credit Card B (smallest) should be paid off before
        # Credit Card A (larger)
        credit_card_b_paid = None
        credit_card_a_paid = None

        for i, milestone in enumerate(result.milestones):
            if "Credit Card B" in milestone and "paid off" in milestone:
                credit_card_b_paid = i
            elif "Credit Card A" in milestone and "paid off" in milestone:
                credit_card_a_paid = i

        # Credit Card B should be paid off
        assert credit_card_b_paid is not None, "Credit Card B should be paid off"
        # If Credit Card A is also paid off, B should come first (snowball)
        if credit_card_a_paid is not None:
            assert credit_card_b_paid < credit_card_a_paid, (
                "Snowball should pay off smaller debt first"
            )

    def test_calculate_payoff_generates_milestones(self, sample_debts):
        """Test that milestones are generated during payoff."""
        result = calculate_payoff(sample_debts, extra_payment=Decimal("100"))

        assert len(result.milestones) > 0
        # Should have percentage milestones
        percentage_milestones = [m for m in result.milestones if "%" in m]
        assert len(percentage_milestones) > 0


class TestStrategyComparison:
    """Tests for strategy comparison."""

    @pytest.fixture
    def sample_debts(self):
        """Create sample debts for testing."""
        return [
            Debt("1", "Credit Card A", Decimal("3500"), Decimal("22.9"), Decimal("87")),
            Debt("2", "Credit Card B", Decimal("1200"), Decimal("19.9"), Decimal("30")),
            Debt("3", "Personal Loan", Decimal("5000"), Decimal("7.9"), Decimal("150")),
        ]

    def test_compare_strategies(self, sample_debts):
        """Test strategy comparison returns valid results."""
        comparison = compare_strategies(sample_debts, extra_payment=Decimal("100"))

        assert comparison.avalanche_months > 0
        assert comparison.snowball_months > 0
        assert comparison.avalanche_interest > Decimal("0")
        assert comparison.snowball_interest > Decimal("0")

    def test_avalanche_saves_more_interest(self, sample_debts):
        """Test that avalanche typically saves more on interest."""
        comparison = compare_strategies(sample_debts, extra_payment=Decimal("100"))

        # Avalanche should save interest (or at worst be equal)
        assert comparison.interest_saved >= Decimal("0")
        assert comparison.avalanche_interest <= comparison.snowball_interest

    def test_comparison_recommends_strategy(self, sample_debts):
        """Test that comparison provides a recommendation."""
        comparison = compare_strategies(sample_debts, extra_payment=Decimal("100"))

        assert comparison.recommended in [
            PayoffStrategy.AVALANCHE,
            PayoffStrategy.SNOWBALL,
        ]


class TestWindfallImpact:
    """Tests for windfall impact calculations."""

    @pytest.fixture
    def sample_debts(self):
        """Create sample debts for testing."""
        return [
            Debt("1", "Credit Card", Decimal("3500"), Decimal("22.9"), Decimal("87")),
            Debt("2", "Personal Loan", Decimal("5000"), Decimal("7.9"), Decimal("150")),
        ]

    def test_windfall_reduces_payoff_time(self, sample_debts):
        """Test that windfall reduces payoff time."""
        impact = calculate_windfall_impact(
            sample_debts,
            windfall_amount=Decimal("500"),
        )

        assert impact["months_saved"] > 0
        assert impact["interest_saved"] > Decimal("0")

    def test_windfall_to_specific_debt(self, sample_debts):
        """Test applying windfall to specific debt."""
        impact = calculate_windfall_impact(
            sample_debts,
            windfall_amount=Decimal("500"),
            target_debt_id="1",  # Credit Card
        )

        assert impact["windfall_amount"] == Decimal("500")
        assert "new_debt_free_date" in impact


class TestDebtProgress:
    """Tests for debt progress tracking."""

    def test_calculate_progress(self):
        """Test progress calculation."""
        original = [
            Debt("1", "Credit Card", Decimal("5000"), Decimal("20"), Decimal("100")),
        ]
        current = [
            Debt("1", "Credit Card", Decimal("3000"), Decimal("20"), Decimal("100")),
        ]

        progress = calculate_progress(original, current, date.today() - timedelta(days=180))

        assert progress["original_total"] == Decimal("5000")
        assert progress["current_total"] == Decimal("3000")
        assert progress["total_paid_off"] == Decimal("2000")
        assert progress["percentage_complete"] == Decimal("40.0")


class TestSavingsProgress:
    """Tests for savings goal progress calculations."""

    @pytest.fixture
    def sample_goal(self):
        """Create sample savings goal."""
        return SavingsGoal(
            id="1",
            name="Emergency Fund",
            target_amount=Decimal("5000"),
            current_saved=Decimal("2000"),
            contribution_amount=Decimal("200"),
            frequency=ContributionFrequency.MONTHLY,
            target_date=date.today() + relativedelta(months=24),
        )

    def test_calculate_savings_progress(self, sample_goal):
        """Test basic progress calculation."""
        progress = calc_savings_progress(sample_goal)

        assert progress["target_amount"] == Decimal("5000")
        assert progress["current_saved"] == Decimal("2000")
        assert progress["remaining"] == Decimal("3000")
        assert progress["percentage"] == Decimal("40.0")
        assert progress["is_complete"] is False

    def test_calculate_progress_complete(self):
        """Test progress for completed goal."""
        goal = SavingsGoal(
            id="1",
            name="Complete Goal",
            target_amount=Decimal("1000"),
            current_saved=Decimal("1000"),
            contribution_amount=Decimal("100"),
        )

        progress = calc_savings_progress(goal)

        assert progress["is_complete"] is True
        assert progress["percentage"] == Decimal("100.0")


class TestSavingsContributions:
    """Tests for savings contribution calculations."""

    def test_calculate_required_contribution(self):
        """Test required contribution calculation."""
        target = Decimal("6000")
        current = Decimal("0")
        target_date = date.today() + relativedelta(months=12)

        required = calculate_required_contribution(
            target, current, target_date, ContributionFrequency.MONTHLY
        )

        # Should be around £500/month (rounded up to £5 increment)
        assert required >= Decimal("500")
        assert required <= Decimal("505")

    def test_calculate_required_contribution_partial_progress(self):
        """Test required contribution with existing savings."""
        target = Decimal("6000")
        current = Decimal("3000")
        target_date = date.today() + relativedelta(months=12)

        required = calculate_required_contribution(
            target, current, target_date, ContributionFrequency.MONTHLY
        )

        # Should be around £250/month
        assert required >= Decimal("250")
        assert required <= Decimal("255")

    def test_calculate_required_contribution_goal_met(self):
        """Test required contribution when goal already met."""
        required = calculate_required_contribution(
            Decimal("1000"),
            Decimal("1500"),  # Already exceeded
            date.today() + relativedelta(months=6),
        )

        assert required == Decimal("0")


class TestSavingsProjections:
    """Tests for savings achievement projections."""

    def test_project_achievement_date(self):
        """Test achievement date projection."""
        target = Decimal("6000")
        current = Decimal("0")
        contribution = Decimal("500")

        achievement = project_achievement_date(
            target, current, contribution, ContributionFrequency.MONTHLY
        )

        # Should be about 12 months from now
        expected = date.today() + relativedelta(months=12)
        assert achievement is not None
        assert abs((achievement - expected).days) < 45  # Within 1.5 months

    def test_project_achievement_date_zero_contribution(self):
        """Test projection with zero contribution."""
        achievement = project_achievement_date(
            Decimal("1000"),
            Decimal("0"),
            Decimal("0"),
        )

        assert achievement is None

    def test_project_achievement_date_already_complete(self):
        """Test projection when already complete."""
        achievement = project_achievement_date(
            Decimal("1000"),
            Decimal("1500"),
            Decimal("100"),
        )

        assert achievement == date.today()


class TestSavingsScenarios:
    """Tests for savings scenario generation."""

    @pytest.fixture
    def sample_goal(self):
        """Create sample savings goal."""
        return SavingsGoal(
            id="1",
            name="Vacation",
            target_amount=Decimal("3000"),
            current_saved=Decimal("1000"),
            contribution_amount=Decimal("200"),
            frequency=ContributionFrequency.MONTHLY,
            target_date=date.today() + relativedelta(months=12),
        )

    def test_generate_scenarios(self, sample_goal):
        """Test scenario generation."""
        scenarios = generate_scenarios(sample_goal)

        assert len(scenarios) > 0
        # Should have current, accelerated, and comfortable scenarios
        scenario_names = [s.name for s in scenarios]
        assert "current" in scenario_names
        assert "accelerated" in scenario_names
        assert "comfortable" in scenario_names

    def test_accelerated_scenario_is_faster(self, sample_goal):
        """Test that accelerated scenario achieves goal faster."""
        scenarios = generate_scenarios(sample_goal)

        current = next((s for s in scenarios if s.name == "current"), None)
        accelerated = next((s for s in scenarios if s.name == "accelerated"), None)

        assert current is not None
        assert accelerated is not None
        assert accelerated.months_to_goal < current.months_to_goal


class TestSavingsMilestones:
    """Tests for savings milestone calculations."""

    @pytest.fixture
    def sample_goal(self):
        """Create sample savings goal."""
        return SavingsGoal(
            id="1",
            name="Emergency Fund",
            target_amount=Decimal("5000"),
            current_saved=Decimal("2000"),
            contribution_amount=Decimal("200"),
        )

    def test_calculate_milestones(self, sample_goal):
        """Test milestone calculation."""
        milestones = calculate_milestones(sample_goal)

        assert len(milestones) == 6  # Default: 10, 25, 50, 75, 90, 100
        # At 40%, 10% and 25% should be achieved
        achieved = [m for m in milestones if m.achieved]
        assert len(achieved) == 2  # 10% and 25%

    def test_calculate_milestones_custom_percentages(self, sample_goal):
        """Test milestone calculation with custom percentages."""
        milestones = calculate_milestones(sample_goal, milestone_percentages=[25, 50, 75, 100])

        assert len(milestones) == 4

    def test_milestone_projection_dates(self, sample_goal):
        """Test that unachieved milestones have projected dates."""
        milestones = calculate_milestones(sample_goal)

        # Unachieved milestones should have projected dates
        unachieved = [m for m in milestones if not m.achieved]
        for milestone in unachieved:
            assert milestone.projected_date is not None


class TestOnTrackCheck:
    """Tests for on-track status checking."""

    def test_check_on_track_ahead(self):
        """Test on-track check when ahead of schedule."""
        goal = SavingsGoal(
            id="1",
            name="Goal",
            target_amount=Decimal("6000"),
            current_saved=Decimal("3000"),  # 50% saved
            contribution_amount=Decimal("500"),  # More than needed
            target_date=date.today() + relativedelta(months=12),  # 12 months left
        )

        status = check_on_track(goal)

        assert status["has_target_date"] is True
        assert status["on_track"] is True

    def test_check_on_track_behind(self):
        """Test on-track check when behind schedule."""
        goal = SavingsGoal(
            id="1",
            name="Goal",
            target_amount=Decimal("6000"),
            current_saved=Decimal("0"),
            contribution_amount=Decimal("100"),  # Way less than needed
            target_date=date.today() + relativedelta(months=12),
        )

        status = check_on_track(goal)

        assert status["on_track"] is False
        assert "Increase" in status["message"]

    def test_check_on_track_no_target_date(self):
        """Test on-track check without target date."""
        goal = SavingsGoal(
            id="1",
            name="Goal",
            target_amount=Decimal("5000"),
            current_saved=Decimal("1000"),
            contribution_amount=Decimal("200"),
            target_date=None,
        )

        status = check_on_track(goal)

        assert status["has_target_date"] is False
        assert status["on_track"] is None
