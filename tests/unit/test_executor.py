"""Comprehensive tests for AgentExecutor.

Tests cover:
- Command execution for all intents
- Error handling
- Entity extraction
- Response formatting
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.agent.executor import AgentExecutor
from src.db.database import Base
from src.models.subscription import Frequency
from src.schemas.subscription import SubscriptionCreate


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
async def executor(db_session):
    """Create AgentExecutor with test database."""
    return AgentExecutor(db_session)


class TestAgentExecutorInit:
    """Tests for AgentExecutor initialization."""

    @pytest.mark.asyncio
    async def test_init(self, db_session):
        """Test executor initialization."""
        executor = AgentExecutor(db_session)

        assert executor.db is db_session
        assert executor.parser is not None
        assert executor.service is not None


class TestAgentExecutorCreate:
    """Tests for CREATE intent handling."""

    @pytest.mark.asyncio
    async def test_handle_create(self, executor):
        """Test handling create command."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "CREATE",
                "entities": {
                    "name": "Netflix",
                    "amount": Decimal("15.99"),
                    "frequency": Frequency.MONTHLY,
                },
            }

            result = await executor.execute("Add Netflix for £15.99 monthly")

            assert "message" in result
            assert "data" in result
            assert "Netflix" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_create_missing_name(self, executor):
        """Test create fails without name."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "CREATE",
                "entities": {
                    "amount": Decimal("15.99"),
                },
            }

            with pytest.raises(ValueError, match="name and amount"):
                await executor.execute("Add subscription")

    @pytest.mark.asyncio
    async def test_handle_create_missing_amount(self, executor):
        """Test create fails without amount."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "CREATE",
                "entities": {
                    "name": "Netflix",
                },
            }

            with pytest.raises(ValueError, match="name and amount"):
                await executor.execute("Add Netflix subscription")


class TestAgentExecutorRead:
    """Tests for READ intent handling."""

    @pytest.mark.asyncio
    async def test_handle_read_empty(self, executor):
        """Test reading when no payments exist."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "READ",
                "entities": {},
            }

            result = await executor.execute("Show my subscriptions")

            assert "No payment" in result["message"]
            assert result["data"] == []

    @pytest.mark.asyncio
    async def test_handle_read_with_subscriptions(self, executor):
        """Test reading existing subscriptions."""
        # First create a subscription
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "READ",
                "entities": {},
            }

            result = await executor.execute("Show all subscriptions")

            assert "Found 1" in result["message"]
            assert len(result["data"]) == 1


class TestAgentExecutorUpdate:
    """Tests for UPDATE intent handling."""

    @pytest.mark.asyncio
    async def test_handle_update(self, executor):
        """Test updating a subscription."""
        # Create subscription first
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UPDATE",
                "entities": {
                    "name": "Netflix",
                    "amount": Decimal("19.99"),
                },
            }

            result = await executor.execute("Update Netflix to £19.99")

            assert "Updated" in result["message"]
            assert result["data"]["amount"] == "19.99"

    @pytest.mark.asyncio
    async def test_handle_update_missing_name(self, executor):
        """Test update fails without name."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UPDATE",
                "entities": {
                    "amount": Decimal("19.99"),
                },
            }

            with pytest.raises(ValueError, match="specify which"):
                await executor.execute("Update to £19.99")

    @pytest.mark.asyncio
    async def test_handle_update_not_found(self, executor):
        """Test update fails when subscription not found."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UPDATE",
                "entities": {
                    "name": "NonExistent",
                    "amount": Decimal("19.99"),
                },
            }

            with pytest.raises(ValueError, match="No payment found"):
                await executor.execute("Update NonExistent to £19.99")


class TestAgentExecutorDelete:
    """Tests for DELETE intent handling."""

    @pytest.mark.asyncio
    async def test_handle_delete(self, executor):
        """Test deleting a subscription."""
        # Create subscription first
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
        )
        await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "DELETE",
                "entities": {
                    "name": "Netflix",
                },
            }

            result = await executor.execute("Cancel Netflix")

            assert "Removed" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_delete_missing_name(self, executor):
        """Test delete fails without name."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "DELETE",
                "entities": {},
            }

            with pytest.raises(ValueError, match="specify which"):
                await executor.execute("Cancel subscription")

    @pytest.mark.asyncio
    async def test_handle_delete_not_found(self, executor):
        """Test delete fails when subscription not found."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "DELETE",
                "entities": {
                    "name": "NonExistent",
                },
            }

            with pytest.raises(ValueError, match="No payment found"):
                await executor.execute("Cancel NonExistent")


class TestAgentExecutorSummary:
    """Tests for SUMMARY intent handling."""

    @pytest.mark.asyncio
    async def test_handle_summary_empty(self, executor):
        """Test summary with no subscriptions."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "SUMMARY",
                "entities": {},
            }

            result = await executor.execute("How much am I spending?")

            assert "Money Flow Summary" in result["message"]
            assert result["data"]["active_count"] == 0

    @pytest.mark.asyncio
    async def test_handle_summary_with_subscriptions(self, executor):
        """Test summary with subscriptions."""
        # Create subscription
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            currency="GBP",
            frequency=Frequency.MONTHLY,
            start_date=date.today(),
            category="entertainment",
        )
        await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "SUMMARY",
                "entities": {},
            }

            result = await executor.execute("Show my spending summary")

            assert "Monthly spending:" in result["message"]
            assert result["data"]["active_count"] == 1


class TestAgentExecutorUpcoming:
    """Tests for UPCOMING intent handling."""

    @pytest.mark.asyncio
    async def test_handle_upcoming_empty(self, executor):
        """Test upcoming with no payments due."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UPCOMING",
                "entities": {},
            }

            result = await executor.execute("What's due this week?")

            assert "No payments" in result["message"] or "Upcoming" in result["message"]


class TestAgentExecutorUnknown:
    """Tests for unknown intent handling."""

    @pytest.mark.asyncio
    async def test_handle_unknown(self, executor):
        """Test handling unknown command."""
        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UNKNOWN",
                "entities": {},
            }

            with pytest.raises(ValueError, match="didn't understand"):
                await executor.execute("Hello world")


class TestAgentExecutorMultipleMatches:
    """Tests for handling multiple subscription matches."""

    @pytest.mark.asyncio
    async def test_update_multiple_matches(self, executor):
        """Test update fails with multiple matches."""
        # Create similar subscriptions
        for name in ["Netflix Basic", "Netflix Premium"]:
            data = SubscriptionCreate(
                name=name,
                amount=Decimal("15.99"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                start_date=date.today(),
            )
            await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "UPDATE",
                "entities": {
                    "name": "Netflix",  # Matches both
                    "amount": Decimal("19.99"),
                },
            }

            with pytest.raises(ValueError, match="Multiple matches"):
                await executor.execute("Update Netflix to £19.99")

    @pytest.mark.asyncio
    async def test_delete_multiple_matches(self, executor):
        """Test delete fails with multiple matches."""
        # Create similar subscriptions
        for name in ["Spotify Personal", "Spotify Family"]:
            data = SubscriptionCreate(
                name=name,
                amount=Decimal("9.99"),
                currency="GBP",
                frequency=Frequency.MONTHLY,
                start_date=date.today(),
            )
            await executor.service.create(data)

        with patch.object(executor.parser, "parse") as mock_parse:
            mock_parse.return_value = {
                "intent": "DELETE",
                "entities": {
                    "name": "Spotify",  # Matches both
                },
            }

            with pytest.raises(ValueError, match="Multiple matches"):
                await executor.execute("Cancel Spotify")
