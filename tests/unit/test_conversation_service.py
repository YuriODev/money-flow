"""Tests for ConversationService.

Tests cover:
- Conversation turn persistence
- Session history retrieval
- RAG context integration
- Entity extraction from responses
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.conversation_service import (
    ConversationService,
    generate_session_id,
)


class TestGenerateSessionId:
    """Tests for session ID generation."""

    def test_generate_session_id_returns_uuid(self):
        """Test that generate_session_id returns a valid UUID."""
        session_id = generate_session_id()

        assert len(session_id) == 36
        assert session_id.count("-") == 4

    def test_generate_session_id_unique(self):
        """Test that each call generates a unique ID."""
        id1 = generate_session_id()
        id2 = generate_session_id()

        assert id1 != id2


class TestConversationServiceExtractEntities:
    """Tests for entity extraction from responses."""

    def test_extract_single_subscription(self):
        """Test extracting entity from single subscription response."""
        response = {"data": {"name": "Netflix", "amount": 15.99}}

        entities = ConversationService.extract_entities_from_response(response)

        assert entities == ["Netflix"]

    def test_extract_multiple_subscriptions(self):
        """Test extracting entities from list of subscriptions."""
        response = {
            "data": [
                {"name": "Netflix", "amount": 15.99},
                {"name": "Spotify", "amount": 9.99},
            ]
        }

        entities = ConversationService.extract_entities_from_response(response)

        assert "Netflix" in entities
        assert "Spotify" in entities
        assert len(entities) == 2

    def test_extract_no_data(self):
        """Test extracting from response without data."""
        response = {"message": "No subscriptions found"}

        entities = ConversationService.extract_entities_from_response(response)

        assert entities == []

    def test_extract_empty_list(self):
        """Test extracting from empty list response."""
        response = {"data": []}

        entities = ConversationService.extract_entities_from_response(response)

        assert entities == []

    def test_extract_data_without_name(self):
        """Test extracting from data without name field."""
        response = {"data": {"amount": 15.99}}

        entities = ConversationService.extract_entities_from_response(response)

        assert entities == []


class TestConversationServiceInit:
    """Tests for ConversationService initialization."""

    def test_init_creates_service(self):
        """Test that service initializes correctly."""
        mock_db = MagicMock()

        service = ConversationService(mock_db)

        assert service.db == mock_db
        assert service.rag is not None


class TestConversationServiceAddTurn:
    """Tests for adding conversation turns."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_add_turn_creates_conversation(self, mock_db):
        """Test that add_turn creates a conversation record."""
        with patch("src.services.conversation_service.get_rag_service") as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.add_turn = AsyncMock()
            mock_rag.return_value = mock_rag_instance

            service = ConversationService(mock_db)
            await service.add_turn(
                user_id="user-1",
                session_id="session-1",
                role="user",
                content="Hello",
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_turn_with_entities(self, mock_db):
        """Test that add_turn stores entities."""
        with patch("src.services.conversation_service.get_rag_service") as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.add_turn = AsyncMock()
            mock_rag.return_value = mock_rag_instance

            service = ConversationService(mock_db)
            await service.add_turn(
                user_id="user-1",
                session_id="session-1",
                role="user",
                content="Add Netflix",
                entities=["Netflix"],
            )

            # Verify RAG service was called with entities
            mock_rag_instance.add_turn.assert_called_once_with(
                user_id="user-1",
                session_id="session-1",
                role="user",
                content="Add Netflix",
                entities=["Netflix"],
            )


class TestConversationServiceGetContext:
    """Tests for context retrieval."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_context_returns_context(self, mock_db):
        """Test that get_context returns a ConversationContext."""
        from src.services.rag_service import ConversationContext

        mock_context = ConversationContext(
            recent_turns=[],
            relevant_history=[],
            mentioned_entities=["Netflix"],
            resolved_query="Cancel Netflix",
        )

        with (
            patch("src.services.conversation_service.get_rag_service") as mock_rag,
            patch("src.services.conversation_service.settings") as mock_settings,
        ):
            mock_settings.rag_enabled = False  # Disable analytics logging
            mock_rag_instance = MagicMock()
            mock_rag_instance.get_context = AsyncMock(return_value=mock_context)
            mock_rag.return_value = mock_rag_instance

            service = ConversationService(mock_db)
            context = await service.get_context(
                user_id="user-1",
                session_id="session-1",
                query="Cancel it",
            )

            assert context.resolved_query == "Cancel Netflix"
            assert "Netflix" in context.mentioned_entities


class TestConversationServiceFormatContext:
    """Tests for context formatting."""

    def test_format_context_delegates_to_rag(self):
        """Test that format_context delegates to RAG service."""
        from src.services.rag_service import ConversationContext

        mock_db = MagicMock()
        context = ConversationContext(
            recent_turns=[],
            relevant_history=[],
            mentioned_entities=[],
            resolved_query="test",
        )

        with patch("src.services.conversation_service.get_rag_service") as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.format_context_for_prompt = MagicMock(return_value="formatted")
            mock_rag.return_value = mock_rag_instance

            service = ConversationService(mock_db)
            result = service.format_context_for_prompt(context)

            assert result == "formatted"
            mock_rag_instance.format_context_for_prompt.assert_called_once_with(context)
