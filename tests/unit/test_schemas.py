"""Comprehensive tests for Pydantic schemas.

Tests cover:
- Validation rules
- Default values
- Type coercion
- Error messages
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.subscription import Frequency
from src.schemas.subscription import (
    SubscriptionBase,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionSummary,
    SubscriptionUpdate,
)


class TestSubscriptionBase:
    """Tests for SubscriptionBase schema."""

    def test_valid_subscription_base(self):
        """Test creating valid subscription base."""
        data = SubscriptionBase(
            name="Netflix",
            amount=Decimal("15.99"),
            start_date=date.today(),
        )

        assert data.name == "Netflix"
        assert data.amount == Decimal("15.99")
        assert data.currency == "GBP"  # Default (changed from USD)
        assert data.frequency == Frequency.MONTHLY  # Default
        assert data.frequency_interval == 1  # Default

    def test_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="",
                amount=Decimal("10.00"),
                start_date=date.today(),
            )

        error_str = str(exc_info.value)
        assert "string_too_short" in error_str or "at least 1 character" in error_str

    def test_name_max_length(self):
        """Test name maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="a" * 300,
                amount=Decimal("10.00"),
                start_date=date.today(),
            )

        error_str = str(exc_info.value)
        assert "string_too_long" in error_str or "at most 255 characters" in error_str

    def test_amount_must_be_positive(self):
        """Test amount must be greater than 0."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="Test",
                amount=Decimal("0"),
                start_date=date.today(),
            )

        assert "greater_than" in str(exc_info.value)

    def test_amount_negative_invalid(self):
        """Test negative amount is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="Test",
                amount=Decimal("-10.00"),
                start_date=date.today(),
            )

        assert "greater_than" in str(exc_info.value)

    def test_currency_code_length(self):
        """Test currency code must be 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="Test",
                amount=Decimal("10.00"),
                currency="US",  # Too short
                start_date=date.today(),
            )

        assert "min_length" in str(exc_info.value) or "String should have at least" in str(
            exc_info.value
        )

    def test_frequency_interval_minimum(self):
        """Test frequency interval must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="Test",
                amount=Decimal("10.00"),
                frequency_interval=0,
                start_date=date.today(),
            )

        assert "greater_than_equal" in str(exc_info.value)

    def test_category_max_length(self):
        """Test category maximum length."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionBase(
                name="Test",
                amount=Decimal("10.00"),
                category="a" * 200,
                start_date=date.today(),
            )

        error_str = str(exc_info.value)
        assert "string_too_long" in error_str or "at most 100 characters" in error_str

    def test_all_frequencies_valid(self):
        """Test all frequency values are valid."""
        for freq in Frequency:
            data = SubscriptionBase(
                name="Test",
                amount=Decimal("10.00"),
                frequency=freq,
                start_date=date.today(),
            )
            assert data.frequency == freq


class TestSubscriptionCreate:
    """Tests for SubscriptionCreate schema."""

    def test_inherits_base(self):
        """Test SubscriptionCreate inherits from SubscriptionBase."""
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date(2025, 1, 1),
        )

        assert data.name == "Netflix"
        assert data.currency == "GBP"

    def test_with_all_fields(self):
        """Test creating with all optional fields."""
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            frequency_interval=1,
            start_date=date.today(),
            category="entertainment",
            notes="My streaming subscription",
        )

        assert data.category == "entertainment"
        assert data.notes == "My streaming subscription"


class TestSubscriptionUpdate:
    """Tests for SubscriptionUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional in update."""
        data = SubscriptionUpdate()

        # All should be None
        assert data.name is None
        assert data.amount is None
        assert data.currency is None
        assert data.frequency is None
        assert data.is_active is None

    def test_partial_update(self):
        """Test updating only some fields."""
        data = SubscriptionUpdate(amount=Decimal("19.99"))

        assert data.amount == Decimal("19.99")
        assert data.name is None
        assert data.frequency is None

    def test_exclude_unset(self):
        """Test model_dump excludes unset fields."""
        data = SubscriptionUpdate(amount=Decimal("19.99"))
        dumped = data.model_dump(exclude_unset=True)

        assert "amount" in dumped
        assert "name" not in dumped
        assert "frequency" not in dumped

    def test_is_active_toggle(self):
        """Test is_active can be toggled."""
        activate = SubscriptionUpdate(is_active=True)
        deactivate = SubscriptionUpdate(is_active=False)

        assert activate.is_active is True
        assert deactivate.is_active is False

    def test_validation_still_applies(self):
        """Test validation rules still apply to update."""
        with pytest.raises(ValidationError):
            SubscriptionUpdate(amount=Decimal("-10.00"))


class TestSubscriptionResponse:
    """Tests for SubscriptionResponse schema."""

    def test_from_attributes_config(self):
        """Test model_config allows from_attributes."""

        # Create a mock ORM object
        class MockSubscription:
            id = "uuid-123"
            name = "Netflix"
            amount = Decimal("15.99")
            currency = "GBP"
            frequency = Frequency.MONTHLY
            frequency_interval = 1
            start_date = date.today()
            next_payment_date = date.today()
            category = "entertainment"
            notes = None
            is_active = True
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()

        response = SubscriptionResponse.model_validate(MockSubscription())

        assert response.id == "uuid-123"
        assert response.name == "Netflix"
        assert response.is_active is True

    def test_all_required_fields(self):
        """Test all response fields are present."""
        response = SubscriptionResponse(
            id="uuid-123",
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            frequency_interval=1,
            start_date=date.today(),
            next_payment_date=date.today(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert response.id is not None
        assert response.next_payment_date is not None
        assert response.created_at is not None
        assert response.updated_at is not None


class TestSubscriptionSummary:
    """Tests for SubscriptionSummary schema."""

    def test_valid_summary(self):
        """Test creating valid summary."""
        summary = SubscriptionSummary(
            total_monthly=Decimal("125.99"),
            total_yearly=Decimal("1511.88"),
            active_count=5,
            by_category={"entertainment": Decimal("45.99"), "health": Decimal("80.00")},
            upcoming_week=[],
        )

        assert summary.total_monthly == Decimal("125.99")
        assert summary.total_yearly == Decimal("1511.88")
        assert summary.active_count == 5
        assert len(summary.by_category) == 2
        assert len(summary.upcoming_week) == 0

    def test_empty_summary(self):
        """Test empty summary."""
        summary = SubscriptionSummary(
            total_monthly=Decimal("0"),
            total_yearly=Decimal("0"),
            active_count=0,
            by_category={},
            upcoming_week=[],
        )

        assert summary.active_count == 0
        assert len(summary.by_category) == 0

    def test_with_upcoming_subscriptions(self):
        """Test summary with upcoming subscriptions."""
        upcoming = SubscriptionResponse(
            id="uuid-123",
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            frequency_interval=1,
            start_date=date.today(),
            next_payment_date=date.today(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        summary = SubscriptionSummary(
            total_monthly=Decimal("15.99"),
            total_yearly=Decimal("191.88"),
            active_count=1,
            by_category={"entertainment": Decimal("15.99")},
            upcoming_week=[upcoming],
        )

        assert len(summary.upcoming_week) == 1
        assert summary.upcoming_week[0].name == "Netflix"
