"""Database Integration Tests for Sprint 2.3.2.

Comprehensive integration tests for database operations:
- Subscription CRUD with real database
- Card-subscription relationships
- Cascade deletes
- Concurrent modifications
- Transaction rollbacks
- Data integrity constraints

Usage:
    pytest tests/integration/test_db_integration.py -v
"""

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.database import Base
from src.models.payment_card import CardType, PaymentCard
from src.models.subscription import (
    Frequency,
    PaymentHistory,
    PaymentStatus,
    PaymentType,
    Subscription,
)
from src.models.user import User, UserRole

# Test database URL - use a separate test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def enable_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine with foreign keys enabled."""
    from sqlalchemy import event

    # Enable foreign keys for SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Add event listener to enable foreign keys on every connection
    event.listen(engine.sync_engine, "connect", enable_foreign_keys)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    """Create test database session."""
    session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for relationship tests."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password="$2b$12$test_hash",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_card(db_session: AsyncSession) -> PaymentCard:
    """Create a test payment card."""
    card = PaymentCard(
        id=str(uuid.uuid4()),
        name="Test Card",
        card_type=CardType.DEBIT,
        bank_name="Test Bank",
        currency="GBP",
        is_active=True,
    )
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)
    return card


class TestSubscriptionCRUD:
    """Test subscription CRUD operations with real database (2.3.2.1)."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, db_session: AsyncSession, test_user: User):
        """Test creating a subscription."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            is_active=True,
            user_id=test_user.id,
        )

        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        # Verify created
        result = await db_session.execute(
            select(Subscription).where(Subscription.id == subscription.id)
        )
        fetched = result.scalar_one()

        assert fetched.name == "Netflix"
        assert fetched.amount == Decimal("15.99")
        assert fetched.currency == "GBP"
        assert fetched.frequency == Frequency.MONTHLY
        assert fetched.payment_type == PaymentType.SUBSCRIPTION
        assert fetched.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_subscription_all_payment_types(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating subscriptions for all payment types."""
        payment_types = list(PaymentType)

        for pt in payment_types:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                name=f"Test {pt.value}",
                amount=Decimal("50.00"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                payment_type=pt,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                is_active=True,
                user_id=test_user.id,
            )
            db_session.add(subscription)

        await db_session.commit()

        # Verify all created
        result = await db_session.execute(
            select(Subscription).where(Subscription.user_id == test_user.id)
        )
        subscriptions = result.scalars().all()

        assert len(subscriptions) == len(payment_types)

    @pytest.mark.asyncio
    async def test_read_subscription(self, db_session: AsyncSession, test_user: User):
        """Test reading a subscription by ID."""
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            name="Spotify",
            amount=Decimal("9.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()

        # Read back
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one_or_none()

        assert fetched is not None
        assert fetched.id == sub_id
        assert fetched.name == "Spotify"

    @pytest.mark.asyncio
    async def test_update_subscription(self, db_session: AsyncSession, test_user: User):
        """Test updating a subscription."""
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            name="Original Name",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()

        # Update
        subscription.name = "Updated Name"
        subscription.amount = Decimal("20.00")
        await db_session.commit()

        # Verify update
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one()

        assert fetched.name == "Updated Name"
        assert fetched.amount == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_delete_subscription(self, db_session: AsyncSession, test_user: User):
        """Test deleting a subscription."""
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            name="To Delete",
            amount=Decimal("5.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()

        # Delete
        await db_session.delete(subscription)
        await db_session.commit()

        # Verify deleted
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one_or_none()

        assert fetched is None

    @pytest.mark.asyncio
    async def test_subscription_with_debt_fields(self, db_session: AsyncSession, test_user: User):
        """Test subscription with debt-specific fields."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Credit Card Debt",
            amount=Decimal("100.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.DEBT,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            total_owed=Decimal("5000.00"),
            remaining_balance=Decimal("3500.00"),
            creditor="Barclays",
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.total_owed == Decimal("5000.00")
        assert subscription.remaining_balance == Decimal("3500.00")
        assert subscription.creditor == "Barclays"
        assert subscription.debt_paid_percentage == 30.0

    @pytest.mark.asyncio
    async def test_subscription_with_savings_fields(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test subscription with savings-specific fields."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Emergency Fund",
            amount=Decimal("200.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SAVINGS,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            target_amount=Decimal("10000.00"),
            current_saved=Decimal("2500.00"),
            recipient="HSBC Savings",
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.target_amount == Decimal("10000.00")
        assert subscription.current_saved == Decimal("2500.00")
        assert subscription.recipient == "HSBC Savings"
        assert subscription.savings_progress_percentage == 25.0


class TestCardSubscriptionRelationships:
    """Test card-subscription relationships (2.3.2.2)."""

    @pytest.mark.asyncio
    async def test_link_subscription_to_card(
        self, db_session: AsyncSession, test_user: User, test_card: PaymentCard
    ):
        """Test linking a subscription to a payment card."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            card_id=test_card.id,
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.card_id == test_card.id

        # Verify relationship through card
        await db_session.refresh(test_card)
        assert len(test_card.subscriptions) == 1
        assert test_card.subscriptions[0].name == "Netflix"

    @pytest.mark.asyncio
    async def test_multiple_subscriptions_per_card(
        self, db_session: AsyncSession, test_user: User, test_card: PaymentCard
    ):
        """Test multiple subscriptions linked to the same card."""
        for name in ["Netflix", "Spotify", "Disney+"]:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                name=name,
                amount=Decimal("10.00"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                payment_type=PaymentType.SUBSCRIPTION,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                card_id=test_card.id,
                user_id=test_user.id,
            )
            db_session.add(subscription)

        await db_session.commit()
        await db_session.refresh(test_card)

        assert len(test_card.subscriptions) == 3

    @pytest.mark.asyncio
    async def test_card_with_funding_card(self, db_session: AsyncSession):
        """Test card that is funded by another card (e.g., PayPal funded by Monzo)."""
        # Create main card
        main_card = PaymentCard(
            id=str(uuid.uuid4()),
            name="Monzo",
            card_type=CardType.DEBIT,
            bank_name="Monzo Bank",
            currency="GBP",
        )
        db_session.add(main_card)
        await db_session.commit()
        await db_session.refresh(main_card)

        # Create funded card
        funded_card = PaymentCard(
            id=str(uuid.uuid4()),
            name="PayPal",
            card_type=CardType.PREPAID,
            bank_name="PayPal",
            currency="GBP",
            funding_card_id=main_card.id,
        )
        db_session.add(funded_card)
        await db_session.commit()
        await db_session.refresh(funded_card)

        assert funded_card.funding_card_id == main_card.id
        assert funded_card.funding_card.name == "Monzo"


class TestCascadeDeletes:
    """Test cascade delete behavior (2.3.2.3)."""

    @pytest.mark.asyncio
    async def test_delete_subscription_cascades_payment_history(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting subscription cascades to payment history."""
        sub_id = str(uuid.uuid4())
        subscription = Subscription(
            id=sub_id,
            name="Test Sub",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()

        # Add payment history
        for i in range(3):
            payment = PaymentHistory(
                id=str(uuid.uuid4()),
                subscription_id=sub_id,
                payment_date=date.today() - timedelta(days=30 * i),
                amount=Decimal("10.00"),
                currency="GBP",
                status=PaymentStatus.COMPLETED,
            )
            db_session.add(payment)

        await db_session.commit()

        # Verify payments exist
        result = await db_session.execute(
            select(PaymentHistory).where(PaymentHistory.subscription_id == sub_id)
        )
        payments = result.scalars().all()
        assert len(payments) == 3

        # Delete subscription
        await db_session.delete(subscription)
        await db_session.commit()

        # Verify payments cascaded
        result = await db_session.execute(
            select(PaymentHistory).where(PaymentHistory.subscription_id == sub_id)
        )
        payments = result.scalars().all()
        assert len(payments) == 0

    @pytest.mark.asyncio
    async def test_delete_user_cascades_subscriptions(self, db_session: AsyncSession):
        """Test deleting user cascades to subscriptions."""
        user = User(
            id=str(uuid.uuid4()),
            email="cascade_test@example.com",
            hashed_password="$2b$12$test_hash",
            full_name="Cascade Test",
            role=UserRole.USER,
        )
        db_session.add(user)
        await db_session.commit()

        # Add subscriptions
        for name in ["Sub1", "Sub2", "Sub3"]:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                name=name,
                amount=Decimal("10.00"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                payment_type=PaymentType.SUBSCRIPTION,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                user_id=user.id,
            )
            db_session.add(subscription)

        await db_session.commit()

        # Verify subscriptions exist
        result = await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subs = result.scalars().all()
        assert len(subs) == 3

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Verify subscriptions cascaded
        result = await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subs = result.scalars().all()
        assert len(subs) == 0

    @pytest.mark.asyncio
    async def test_delete_card_sets_subscription_card_to_null(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting card sets subscription.card_id to NULL (SET NULL)."""
        card = PaymentCard(
            id=str(uuid.uuid4()),
            name="Card to Delete",
            card_type=CardType.DEBIT,
            bank_name="Test Bank",
            currency="GBP",
        )
        db_session.add(card)
        await db_session.commit()

        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Test Sub",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            card_id=card.id,
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()

        sub_id = subscription.id

        # Delete card
        await db_session.delete(card)
        await db_session.commit()

        # Verify subscription still exists but card_id is null
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one()
        assert fetched is not None
        assert fetched.card_id is None


class TestConcurrentModifications:
    """Test concurrent modification handling (2.3.2.4)."""

    @pytest.mark.asyncio
    async def test_concurrent_subscription_updates(self, db_engine, test_user: User):
        """Test concurrent updates to the same subscription."""
        session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        # Create user first in session 1
        async with session_maker() as session1:
            user = User(
                id=str(uuid.uuid4()),
                email="concurrent_test@example.com",
                hashed_password="$2b$12$test_hash",
            )
            session1.add(user)
            await session1.commit()
            user_id = user.id

        # Create subscription
        sub_id = str(uuid.uuid4())
        async with session_maker() as session:
            subscription = Subscription(
                id=sub_id,
                name="Concurrent Test",
                amount=Decimal("10.00"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                payment_type=PaymentType.SUBSCRIPTION,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                user_id=user_id,
            )
            session.add(subscription)
            await session.commit()

        # Simulate concurrent updates (both read, then update)
        async with session_maker() as session1, session_maker() as session2:
            # Both sessions read the same subscription
            result1 = await session1.execute(select(Subscription).where(Subscription.id == sub_id))
            sub1 = result1.scalar_one()

            result2 = await session2.execute(select(Subscription).where(Subscription.id == sub_id))
            sub2 = result2.scalar_one()

            # Update in session1
            sub1.amount = Decimal("20.00")
            await session1.commit()

            # Update in session2 (should succeed - no optimistic locking)
            sub2.amount = Decimal("30.00")
            await session2.commit()

        # Verify final state (last write wins)
        async with session_maker() as session:
            result = await session.execute(select(Subscription).where(Subscription.id == sub_id))
            final = result.scalar_one()
            assert final.amount == Decimal("30.00")


class TestTransactionRollbacks:
    """Test transaction rollback behavior (2.3.2.5)."""

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, db_session: AsyncSession, test_user: User):
        """Test transaction rollback when an error occurs."""
        sub_id = str(uuid.uuid4())

        try:
            # Create subscription
            subscription = Subscription(
                id=sub_id,
                name="Rollback Test",
                amount=Decimal("10.00"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                payment_type=PaymentType.SUBSCRIPTION,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                user_id=test_user.id,
            )
            db_session.add(subscription)

            # Force an error by trying to create duplicate
            duplicate_user = User(
                id=str(uuid.uuid4()),
                email=test_user.email,  # Duplicate email
                hashed_password="$2b$12$test_hash",
            )
            db_session.add(duplicate_user)

            await db_session.commit()  # Should fail
        except IntegrityError:
            await db_session.rollback()

        # Verify subscription was not created
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one_or_none()
        assert fetched is None

    @pytest.mark.asyncio
    async def test_explicit_rollback(self, db_session: AsyncSession, test_user: User):
        """Test explicit transaction rollback."""
        sub_id = str(uuid.uuid4())

        subscription = Subscription(
            id=sub_id,
            name="Explicit Rollback Test",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)

        # Explicitly rollback before commit
        await db_session.rollback()

        # Verify subscription was not created
        result = await db_session.execute(select(Subscription).where(Subscription.id == sub_id))
        fetched = result.scalar_one_or_none()
        assert fetched is None


class TestDataIntegrityConstraints:
    """Test data integrity constraints (2.3.2.7)."""

    @pytest.mark.asyncio
    async def test_unique_user_email(self, db_session: AsyncSession):
        """Test unique constraint on user email."""
        user1 = User(
            id=str(uuid.uuid4()),
            email="unique@example.com",
            hashed_password="$2b$12$test_hash",
        )
        db_session.add(user1)
        await db_session.commit()

        user2 = User(
            id=str(uuid.uuid4()),
            email="unique@example.com",  # Duplicate
            hashed_password="$2b$12$test_hash",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_subscription_requires_name(self, db_session: AsyncSession, test_user: User):
        """Test NOT NULL constraint on subscription name."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name=None,  # Should fail
            amount=Decimal("10.00"),
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_subscription_requires_amount(self, db_session: AsyncSession, test_user: User):
        """Test NOT NULL constraint on subscription amount."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Test",
            amount=None,  # Should fail
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id=test_user.id,
        )
        db_session.add(subscription)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_user(self, db_session: AsyncSession):
        """Test foreign key constraint for user_id."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Test",
            amount=Decimal("10.00"),
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            user_id="non-existent-user-id",  # Invalid FK
        )
        db_session.add(subscription)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_card(self, db_session: AsyncSession, test_user: User):
        """Test foreign key constraint for card_id."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Test",
            amount=Decimal("10.00"),
            frequency=Frequency.MONTHLY,
            payment_type=PaymentType.SUBSCRIPTION,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            card_id="non-existent-card-id",  # Invalid FK
            user_id=test_user.id,
        )
        db_session.add(subscription)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_payment_history_foreign_key(self, db_session: AsyncSession):
        """Test foreign key constraint for payment_history.subscription_id."""
        payment = PaymentHistory(
            id=str(uuid.uuid4()),
            subscription_id="non-existent-subscription-id",  # Invalid FK
            payment_date=date.today(),
            amount=Decimal("10.00"),
            status=PaymentStatus.COMPLETED,
        )
        db_session.add(payment)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_enum_constraints(self, db_session: AsyncSession, test_user: User):
        """Test enum constraints are properly enforced."""
        # Valid enum values should work
        subscription = Subscription(
            id=str(uuid.uuid4()),
            name="Enum Test",
            amount=Decimal("10.00"),
            currency="GBP",
            frequency=Frequency.WEEKLY,
            payment_type=PaymentType.UTILITY,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=7),
            user_id=test_user.id,
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        assert subscription.frequency == Frequency.WEEKLY
        assert subscription.payment_type == PaymentType.UTILITY


class TestQueryPerformance:
    """Test query patterns and performance (bonus tests)."""

    @pytest.mark.asyncio
    async def test_filter_by_user_id(self, db_session: AsyncSession):
        """Test filtering subscriptions by user_id."""
        # Create two users
        user1 = User(
            id=str(uuid.uuid4()),
            email="user1@example.com",
            hashed_password="$2b$12$test_hash",
        )
        user2 = User(
            id=str(uuid.uuid4()),
            email="user2@example.com",
            hashed_password="$2b$12$test_hash",
        )
        db_session.add_all([user1, user2])
        await db_session.commit()

        # Create subscriptions for each user
        for user in [user1, user2]:
            for i in range(3):
                subscription = Subscription(
                    id=str(uuid.uuid4()),
                    name=f"{user.email} Sub {i}",
                    amount=Decimal("10.00"),
                    frequency=Frequency.MONTHLY,
                    payment_type=PaymentType.SUBSCRIPTION,
                    start_date=date.today(),
                    next_payment_date=date.today() + timedelta(days=30),
                    user_id=user.id,
                )
                db_session.add(subscription)

        await db_session.commit()

        # Filter by user1
        result = await db_session.execute(
            select(Subscription).where(Subscription.user_id == user1.id)
        )
        user1_subs = result.scalars().all()

        assert len(user1_subs) == 3
        assert all(s.user_id == user1.id for s in user1_subs)

    @pytest.mark.asyncio
    async def test_filter_by_payment_type(self, db_session: AsyncSession, test_user: User):
        """Test filtering subscriptions by payment_type."""
        # Create subscriptions of different types
        types_to_create = [
            PaymentType.SUBSCRIPTION,
            PaymentType.SUBSCRIPTION,
            PaymentType.DEBT,
            PaymentType.SAVINGS,
        ]

        for i, pt in enumerate(types_to_create):
            subscription = Subscription(
                id=str(uuid.uuid4()),
                name=f"Type Test {i}",
                amount=Decimal("10.00"),
                frequency=Frequency.MONTHLY,
                payment_type=pt,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                user_id=test_user.id,
            )
            db_session.add(subscription)

        await db_session.commit()

        # Filter by SUBSCRIPTION type
        result = await db_session.execute(
            select(Subscription).where(
                Subscription.payment_type == PaymentType.SUBSCRIPTION,
                Subscription.user_id == test_user.id,
            )
        )
        subs = result.scalars().all()

        assert len(subs) == 2
        assert all(s.payment_type == PaymentType.SUBSCRIPTION for s in subs)

    @pytest.mark.asyncio
    async def test_filter_by_active_status(self, db_session: AsyncSession, test_user: User):
        """Test filtering subscriptions by is_active."""
        # Create active and inactive subscriptions
        for is_active in [True, True, False]:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                name=f"Active={is_active}",
                amount=Decimal("10.00"),
                frequency=Frequency.MONTHLY,
                payment_type=PaymentType.SUBSCRIPTION,
                start_date=date.today(),
                next_payment_date=date.today() + timedelta(days=30),
                is_active=is_active,
                user_id=test_user.id,
            )
            db_session.add(subscription)

        await db_session.commit()

        # Filter by active
        result = await db_session.execute(
            select(Subscription).where(
                Subscription.is_active == True,  # noqa: E712
                Subscription.user_id == test_user.id,
            )
        )
        active_subs = result.scalars().all()

        assert len(active_subs) == 2
