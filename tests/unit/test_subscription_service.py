"""Comprehensive tests for SubscriptionService.

Tests cover:
- CRUD operations for subscriptions
- Payment date calculations
- Spending summary calculations
- Filtering and querying
- Edge cases and error handling
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.database import Base
from src.models.subscription import Frequency
from src.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from src.services.subscription_service import (
    SubscriptionService,
)


@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create in-memory test database and session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def service(db_session):
    """Create SubscriptionService with test database."""
    return SubscriptionService(db_session)


@pytest_asyncio.fixture
async def sample_subscription(service):
    """Create a sample subscription for testing."""
    data = SubscriptionCreate(
        name="Netflix",
        amount=Decimal("15.99"),
        currency="GBP",
        frequency=Frequency.MONTHLY,
        start_date=date.today() - timedelta(days=30),
        category="entertainment",
    )
    return await service.create(data)


class TestSubscriptionServiceCreate:
    """Tests for subscription creation."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, service):
        """Test creating a new subscription."""
        data = SubscriptionCreate(
            name="Spotify",
            amount=Decimal("9.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )

        subscription = await service.create(data)

        assert subscription.id is not None
        assert subscription.name == "Spotify"
        assert subscription.amount == Decimal("9.99")
        assert subscription.currency == "GBP"
        assert subscription.frequency == Frequency.MONTHLY
        assert subscription.is_active is True

    @pytest.mark.asyncio
    async def test_create_subscription_calculates_next_payment(self, service):
        """Test that next payment date is calculated correctly."""
        start = date.today() - timedelta(days=15)
        data = SubscriptionCreate(
            name="Test",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=start,
        )

        subscription = await service.create(data)

        # Next payment should be in the future or today
        assert subscription.next_payment_date >= date.today()

    @pytest.mark.asyncio
    async def test_create_with_category(self, service):
        """Test creating subscription with category."""
        data = SubscriptionCreate(
            name="Gym",
            amount=Decimal("50.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
            category="health",
        )

        subscription = await service.create(data)

        assert subscription.category == "health"

    @pytest.mark.asyncio
    async def test_create_with_notes(self, service):
        """Test creating subscription with notes."""
        data = SubscriptionCreate(
            name="Insurance",
            amount=Decimal("100.00"),
            currency="GBP",
            frequency=Frequency.YEARLY,
            start_date=date.today(),
            notes="Annual home insurance",
        )

        subscription = await service.create(data)

        assert subscription.notes == "Annual home insurance"


class TestSubscriptionServiceRead:
    """Tests for reading subscriptions."""

    @pytest.mark.asyncio
    async def test_get_by_id(self, service, sample_subscription):
        """Test getting subscription by ID."""
        found = await service.get_by_id(sample_subscription.id)

        assert found is not None
        assert found.id == sample_subscription.id
        assert found.name == "Netflix"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test getting non-existent subscription returns None."""
        found = await service.get_by_id("non-existent-id")

        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_name(self, service, sample_subscription):
        """Test getting subscription by name."""
        found = await service.get_by_name("Netflix")

        assert found is not None
        assert found.name == "Netflix"

    @pytest.mark.asyncio
    async def test_get_by_name_partial(self, service, sample_subscription):
        """Test getting subscription by partial name."""
        found = await service.get_by_name("net")

        assert found is not None
        assert found.name == "Netflix"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, service):
        """Test getting non-existent name returns None."""
        found = await service.get_by_name("NonExistent")

        assert found is None

    @pytest.mark.asyncio
    async def test_get_all(self, service, sample_subscription):
        """Test getting all subscriptions."""
        # Add another subscription
        data = SubscriptionCreate(
            name="Spotify",
            amount=Decimal("9.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await service.create(data)

        all_subs = await service.get_all()

        assert len(all_subs) == 2

    @pytest.mark.asyncio
    async def test_get_all_filter_active(self, service, db_session):
        """Test filtering by active status."""
        # Create active subscription
        active = SubscriptionCreate(
            name="Active",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await service.create(active)

        # Create and deactivate another
        inactive = SubscriptionCreate(
            name="Inactive",
            amount=Decimal("5.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        inactive_sub = await service.create(inactive)
        await service.update(inactive_sub.id, SubscriptionUpdate(is_active=False))

        # Filter active only
        active_subs = await service.get_all(is_active=True)

        assert len(active_subs) == 1
        assert active_subs[0].name == "Active"

    @pytest.mark.asyncio
    async def test_get_all_filter_category(self, service):
        """Test filtering by category."""
        # Create subscriptions with different categories
        ent = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
            category="entertainment",
        )
        await service.create(ent)

        health = SubscriptionCreate(
            name="Gym",
            amount=Decimal("50.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
            category="health",
        )
        await service.create(health)

        # Filter by category
        entertainment_subs = await service.get_all(category="entertainment")

        assert len(entertainment_subs) == 1
        assert entertainment_subs[0].name == "Netflix"


class TestSubscriptionServiceUpdate:
    """Tests for updating subscriptions."""

    @pytest.mark.asyncio
    async def test_update_subscription(self, service, sample_subscription):
        """Test updating subscription fields."""
        update_data = SubscriptionUpdate(
            amount=Decimal("19.99"),
            category="streaming",
        )

        updated = await service.update(sample_subscription.id, update_data)

        assert updated is not None
        assert updated.amount == Decimal("19.99")
        assert updated.category == "streaming"
        assert updated.name == "Netflix"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_not_found(self, service):
        """Test updating non-existent subscription."""
        update_data = SubscriptionUpdate(amount=Decimal("10.00"))

        result = await service.update("non-existent-id", update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_frequency_recalculates_next_payment(self, service, sample_subscription):
        """Test that changing frequency recalculates next payment."""
        update_data = SubscriptionUpdate(frequency=Frequency.WEEKLY)

        updated = await service.update(sample_subscription.id, update_data)

        assert updated.frequency == Frequency.WEEKLY
        # Next payment may have changed
        assert updated.next_payment_date is not None

    @pytest.mark.asyncio
    async def test_update_deactivate(self, service, sample_subscription):
        """Test deactivating a subscription."""
        update_data = SubscriptionUpdate(is_active=False)

        updated = await service.update(sample_subscription.id, update_data)

        assert updated.is_active is False


class TestSubscriptionServiceDelete:
    """Tests for deleting subscriptions."""

    @pytest.mark.asyncio
    async def test_delete_subscription(self, service, sample_subscription):
        """Test deleting a subscription."""
        result = await service.delete(sample_subscription.id)

        assert result is True

        # Verify it's gone
        found = await service.get_by_id(sample_subscription.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service):
        """Test deleting non-existent subscription."""
        result = await service.delete("non-existent-id")

        assert result is False


class TestSubscriptionServiceSummary:
    """Tests for spending summary calculations."""

    @pytest.mark.asyncio
    async def test_get_summary_empty(self, service):
        """Test summary with no subscriptions."""
        summary = await service.get_summary()

        assert summary.total_monthly == Decimal("0")
        assert summary.total_yearly == Decimal("0")
        assert summary.active_count == 0
        assert len(summary.by_category) == 0
        assert len(summary.upcoming_week) == 0

    @pytest.mark.asyncio
    async def test_get_summary_with_subscriptions(self, service):
        """Test summary calculation with subscriptions."""
        # Create monthly subscription
        monthly = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
            category="entertainment",
        )
        await service.create(monthly)

        summary = await service.get_summary()

        assert summary.total_monthly == Decimal("15.99")
        assert summary.total_yearly == Decimal("191.88")
        assert summary.active_count == 1
        assert "entertainment" in summary.by_category

    @pytest.mark.asyncio
    async def test_get_summary_yearly_to_monthly(self, service):
        """Test yearly subscription converted to monthly."""
        yearly = SubscriptionCreate(
            name="Insurance",
            amount=Decimal("120.00"),
            currency="GBP",
            frequency=Frequency.YEARLY,
            start_date=date.today(),
        )
        await service.create(yearly)

        summary = await service.get_summary()

        # £120/year = £10/month
        assert summary.total_monthly == Decimal("10.00")


class TestSubscriptionServiceUpcoming:
    """Tests for upcoming payment queries."""

    @pytest.mark.asyncio
    async def test_get_upcoming_empty(self, service):
        """Test upcoming with no subscriptions."""
        upcoming = await service.get_upcoming()

        assert len(upcoming) == 0

    @pytest.mark.asyncio
    async def test_get_upcoming_within_days(self, service):
        """Test getting subscriptions due within N days."""
        # Create subscription due today
        data = SubscriptionCreate(
            name="Due Today",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await service.create(data)

        upcoming = await service.get_upcoming(days=7)

        assert len(upcoming) >= 1
        assert any(s.name == "Due Today" for s in upcoming)


class TestPaymentDateCalculation:
    """Tests for payment date calculations."""

    @pytest.fixture
    def service_instance(self, db_session):
        """Create service instance for testing internal methods."""
        return SubscriptionService(db_session)

    @pytest.mark.asyncio
    async def test_calculate_next_payment_daily(self, service_instance):
        """Test daily frequency calculation."""
        start = date.today() - timedelta(days=5)
        next_date = service_instance._calculate_next_payment(start, Frequency.DAILY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_weekly(self, service_instance):
        """Test weekly frequency calculation."""
        start = date.today() - timedelta(days=10)
        next_date = service_instance._calculate_next_payment(start, Frequency.WEEKLY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_biweekly(self, service_instance):
        """Test biweekly frequency calculation."""
        start = date.today() - timedelta(days=20)
        next_date = service_instance._calculate_next_payment(start, Frequency.BIWEEKLY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_monthly(self, service_instance):
        """Test monthly frequency calculation."""
        start = date.today() - timedelta(days=45)
        next_date = service_instance._calculate_next_payment(start, Frequency.MONTHLY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_quarterly(self, service_instance):
        """Test quarterly frequency calculation."""
        start = date.today() - timedelta(days=100)
        next_date = service_instance._calculate_next_payment(start, Frequency.QUARTERLY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_yearly(self, service_instance):
        """Test yearly frequency calculation."""
        start = date.today() - timedelta(days=400)
        next_date = service_instance._calculate_next_payment(start, Frequency.YEARLY, 1)

        assert next_date >= date.today()

    @pytest.mark.asyncio
    async def test_calculate_next_payment_with_interval(self, service_instance):
        """Test calculation with custom interval."""
        start = date.today() - timedelta(days=20)
        # Every 2 weeks
        next_date = service_instance._calculate_next_payment(start, Frequency.WEEKLY, 2)

        assert next_date >= date.today()


class TestMonthlyAmountConversion:
    """Tests for monthly amount conversion."""

    @pytest.fixture
    def service_instance(self, db_session):
        """Create service instance for testing internal methods."""
        return SubscriptionService(db_session)

    @pytest.mark.asyncio
    async def test_to_monthly_daily(self, service_instance):
        """Test daily to monthly conversion."""
        # $1/day ≈ $30/month
        monthly = service_instance._to_monthly_amount(Decimal("1.00"), Frequency.DAILY, 1)

        assert monthly == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_to_monthly_weekly(self, service_instance):
        """Test weekly to monthly conversion."""
        # $10/week ≈ $43.30/month
        monthly = service_instance._to_monthly_amount(Decimal("10.00"), Frequency.WEEKLY, 1)

        assert monthly == Decimal("43.30")

    @pytest.mark.asyncio
    async def test_to_monthly_monthly(self, service_instance):
        """Test monthly stays same."""
        monthly = service_instance._to_monthly_amount(Decimal("15.99"), Frequency.MONTHLY, 1)

        assert monthly == Decimal("15.99")

    @pytest.mark.asyncio
    async def test_to_monthly_yearly(self, service_instance):
        """Test yearly to monthly conversion."""
        # $120/year = $10/month
        monthly = service_instance._to_monthly_amount(Decimal("120.00"), Frequency.YEARLY, 1)

        assert monthly == Decimal("10.00")

    @pytest.mark.asyncio
    async def test_to_monthly_with_interval(self, service_instance):
        """Test conversion with custom interval."""
        # $20 every 2 months = $10/month
        monthly = service_instance._to_monthly_amount(Decimal("20.00"), Frequency.MONTHLY, 2)

        assert monthly == Decimal("10.00")
