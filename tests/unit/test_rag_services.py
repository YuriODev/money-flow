"""Comprehensive tests for RAG services.

Tests cover:
- EmbeddingService: singleton pattern, lazy loading, embedding generation
- VectorStore: CRUD operations, search, filtering
- RAGService: context retrieval, reference resolution, session management
"""

from unittest.mock import MagicMock, patch

import pytest

from src.services.embedding_service import EmbeddingService, get_embedding_service
from src.services.rag_service import (
    ConversationContext,
    ConversationTurn,
    RAGService,
    get_rag_service,
    reset_rag_service,
)
from src.services.vector_store import SearchResult, VectorStore, get_vector_store

# ============================================================================
# EmbeddingService Tests
# ============================================================================


class TestEmbeddingServiceSingleton:
    """Tests for EmbeddingService singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        EmbeddingService.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        EmbeddingService.reset()

    def test_singleton_returns_same_instance(self):
        """Test that multiple calls return the same instance."""
        service1 = EmbeddingService()
        service2 = EmbeddingService()

        assert service1 is service2

    def test_get_embedding_service_returns_singleton(self):
        """Test helper function returns singleton."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        assert service1 is service2

    def test_reset_creates_new_instance(self):
        """Test that reset allows creating a new instance."""
        service1 = EmbeddingService()
        EmbeddingService.reset()
        service2 = EmbeddingService()

        assert service1 is not service2

    def test_initialization_sets_properties(self):
        """Test that initialization sets model properties."""
        service = EmbeddingService()

        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.embedding_dim == 384


class TestEmbeddingServiceEmbed:
    """Tests for EmbeddingService embedding generation."""

    def setup_method(self):
        """Reset singleton before each test."""
        EmbeddingService.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        EmbeddingService.reset()

    @pytest.mark.asyncio
    async def test_embed_raises_on_empty_text(self):
        """Test that embedding empty text raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await service.embed("")

    @pytest.mark.asyncio
    async def test_embed_raises_on_whitespace_only(self):
        """Test that embedding whitespace-only text raises ValueError."""
        service = EmbeddingService()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await service.embed("   ")

    @pytest.mark.asyncio
    async def test_embed_generates_embedding(self):
        """Test that embedding generates correct dimension vector."""
        service = EmbeddingService()

        # Mock the model
        mock_embedding = [0.1] * 384
        with patch.object(service, "_ensure_model_loaded"):
            EmbeddingService._model = MagicMock()
            EmbeddingService._model.encode.return_value = MagicMock(tolist=lambda: mock_embedding)

            embedding = await service.embed("test text", use_cache=False)

            assert len(embedding) == 384
            assert embedding == mock_embedding

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self):
        """Test that batch embedding empty list returns empty list."""
        service = EmbeddingService()

        result = await service.embed_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_embed_batch_generates_embeddings(self):
        """Test that batch embedding works correctly."""
        service = EmbeddingService()

        mock_embeddings = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        with patch.object(service, "_ensure_model_loaded"):
            EmbeddingService._model = MagicMock()
            EmbeddingService._model.encode.return_value = MagicMock(tolist=lambda: mock_embeddings)

            texts = ["text1", "text2", "text3"]
            embeddings = await service.embed_batch(texts, use_cache=False)

            assert len(embeddings) == 3

    def test_get_cache_key_format(self):
        """Test cache key generation format."""
        service = EmbeddingService()

        key = service._get_cache_key("test text")

        assert key.startswith("emb:all-MiniLM-L6-v2:")
        assert len(key) > len("emb:all-MiniLM-L6-v2:")

    def test_get_cache_key_deterministic(self):
        """Test cache key is deterministic for same input."""
        service = EmbeddingService()

        key1 = service._get_cache_key("test text")
        key2 = service._get_cache_key("test text")

        assert key1 == key2

    def test_get_cache_key_different_for_different_text(self):
        """Test cache keys differ for different texts."""
        service = EmbeddingService()

        key1 = service._get_cache_key("text one")
        key2 = service._get_cache_key("text two")

        assert key1 != key2


# ============================================================================
# VectorStore Tests
# ============================================================================


class TestVectorStoreSingleton:
    """Tests for VectorStore singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        VectorStore.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        VectorStore.reset()

    def test_singleton_returns_same_instance(self):
        """Test that multiple calls return the same instance."""
        store1 = VectorStore()
        store2 = VectorStore()

        assert store1 is store2

    def test_get_vector_store_returns_singleton(self):
        """Test helper function returns singleton."""
        store1 = get_vector_store()
        store2 = get_vector_store()

        assert store1 is store2

    def test_reset_creates_new_instance(self):
        """Test that reset allows creating a new instance."""
        store1 = VectorStore()
        VectorStore.reset()
        store2 = VectorStore()

        assert store1 is not store2


class TestVectorStoreOperations:
    """Tests for VectorStore CRUD operations."""

    def setup_method(self):
        """Reset singleton before each test."""
        VectorStore.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        VectorStore.reset()

    @pytest.mark.asyncio
    async def test_upsert_requires_user_id(self):
        """Test that upsert requires user_id in payload."""
        store = VectorStore()

        with pytest.raises(ValueError, match="Payload must contain 'user_id'"):
            await store.upsert(
                collection_name="test",
                id="test-id",
                vector=[0.1] * 384,
                payload={"text": "test"},  # Missing user_id
            )

    @pytest.mark.asyncio
    async def test_upsert_batch_requires_matching_lengths(self):
        """Test that batch upsert requires matching list lengths."""
        store = VectorStore()

        with pytest.raises(ValueError, match="must have the same length"):
            await store.upsert_batch(
                collection_name="test",
                ids=["id1", "id2"],
                vectors=[[0.1] * 384],  # Only one vector
                payloads=[{"user_id": "user1"}],
            )

    @pytest.mark.asyncio
    async def test_upsert_batch_requires_user_id_in_all_payloads(self):
        """Test that batch upsert requires user_id in all payloads."""
        store = VectorStore()

        with pytest.raises(ValueError, match="Payload at index 1 must contain 'user_id'"):
            await store.upsert_batch(
                collection_name="test",
                ids=["id1", "id2"],
                vectors=[[0.1] * 384, [0.2] * 384],
                payloads=[{"user_id": "user1"}, {"text": "missing user_id"}],
            )

    def test_generate_id_returns_uuid(self):
        """Test that generate_id returns a valid UUID string."""
        id1 = VectorStore.generate_id()
        id2 = VectorStore.generate_id()

        assert len(id1) == 36  # UUID format
        assert id1 != id2  # Each call should be unique


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test SearchResult can be created with all fields."""
        result = SearchResult(
            id="test-id",
            score=0.95,
            payload={"text": "test", "user_id": "user1"},
        )

        assert result.id == "test-id"
        assert result.score == 0.95
        assert result.payload["text"] == "test"


# ============================================================================
# RAGService Tests
# ============================================================================


class TestRAGServiceInit:
    """Tests for RAGService initialization."""

    def setup_method(self):
        """Reset services before each test."""
        reset_rag_service()
        EmbeddingService.reset()
        VectorStore.reset()

    def teardown_method(self):
        """Reset services after each test."""
        reset_rag_service()
        EmbeddingService.reset()
        VectorStore.reset()

    def test_get_rag_service_returns_singleton(self):
        """Test helper function returns singleton."""
        rag1 = get_rag_service()
        rag2 = get_rag_service()

        assert rag1 is rag2

    def test_reset_creates_new_instance(self):
        """Test that reset allows creating a new instance."""
        rag1 = get_rag_service()
        reset_rag_service()
        rag2 = get_rag_service()

        assert rag1 is not rag2


class TestRAGServiceSessionManagement:
    """Tests for RAGService session management."""

    def setup_method(self):
        """Reset services and create fresh RAG service."""
        reset_rag_service()
        EmbeddingService.reset()
        VectorStore.reset()
        self.rag = RAGService()

    def teardown_method(self):
        """Reset services after each test."""
        reset_rag_service()
        EmbeddingService.reset()
        VectorStore.reset()

    def test_get_session_key(self):
        """Test session key generation."""
        key = self.rag._get_session_key("user-1", "session-1")

        assert key == "user-1:session-1"

    @pytest.mark.asyncio
    async def test_add_turn_stores_in_session(self):
        """Test that add_turn stores turn in memory."""
        # Disable RAG to avoid vector store operations
        with patch("src.services.rag_service.settings") as mock_settings:
            mock_settings.rag_enabled = False
            mock_settings.rag_context_window = 5

            await self.rag.add_turn("user-1", "session-1", "user", "Hello")

            session_key = self.rag._get_session_key("user-1", "session-1")
            assert session_key in self.rag._sessions
            assert len(self.rag._sessions[session_key]) == 1
            assert self.rag._sessions[session_key][0].content == "Hello"

    @pytest.mark.asyncio
    async def test_add_turn_with_entities(self):
        """Test that add_turn stores entities."""
        with patch("src.services.rag_service.settings") as mock_settings:
            mock_settings.rag_enabled = False
            mock_settings.rag_context_window = 5

            await self.rag.add_turn(
                "user-1", "session-1", "user", "Add Netflix", entities=["Netflix"]
            )

            session_key = self.rag._get_session_key("user-1", "session-1")
            assert self.rag._sessions[session_key][0].entities == ["Netflix"]

    @pytest.mark.asyncio
    async def test_add_turn_maintains_sliding_window(self):
        """Test that session maintains sliding window."""
        with patch("src.services.rag_service.settings") as mock_settings:
            mock_settings.rag_enabled = False
            mock_settings.rag_context_window = 2

            # Add more turns than the window size (2*2=4 max)
            for i in range(6):
                await self.rag.add_turn("user-1", "session-1", "user", f"Message {i}")

            session_key = self.rag._get_session_key("user-1", "session-1")
            # Should only keep last 4 turns (rag_context_window * 2)
            assert len(self.rag._sessions[session_key]) == 4
            assert self.rag._sessions[session_key][0].content == "Message 2"

    def test_clear_session(self):
        """Test session clearing."""
        session_key = self.rag._get_session_key("user-1", "session-1")
        self.rag._sessions[session_key] = [ConversationTurn(role="user", content="test")]

        self.rag.clear_session("user-1", "session-1")

        assert session_key not in self.rag._sessions

    def test_clear_session_nonexistent(self):
        """Test clearing nonexistent session doesn't raise."""
        # Should not raise
        self.rag.clear_session("user-1", "nonexistent-session")


class TestRAGServiceReferenceResolution:
    """Tests for RAGService reference resolution."""

    def setup_method(self):
        """Create fresh RAG service."""
        reset_rag_service()
        self.rag = RAGService()

    def teardown_method(self):
        """Reset services."""
        reset_rag_service()

    def test_resolve_references_no_entities(self):
        """Test that query is unchanged when no entities available."""
        result = self.rag._resolve_references("Cancel it", [])

        assert result == "Cancel it"

    def test_resolve_it_pronoun(self):
        """Test resolving 'it' pronoun."""
        result = self.rag._resolve_references("Cancel it", ["Netflix"])

        assert result == "Cancel Netflix"

    def test_resolve_that_pronoun(self):
        """Test resolving 'that' pronoun."""
        result = self.rag._resolve_references("Update that to £20", ["Spotify"])

        assert result == "Update Spotify to £20"

    def test_resolve_this_pronoun(self):
        """Test resolving 'this' pronoun."""
        result = self.rag._resolve_references("How much is this?", ["Netflix"])

        assert result == "How much is Netflix?"

    def test_resolve_them_with_multiple_entities(self):
        """Test resolving 'them' with multiple entities."""
        result = self.rag._resolve_references("Cancel them", ["Netflix", "Spotify"])

        assert result == "Cancel Netflix, Spotify"

    def test_resolve_those_with_multiple_entities(self):
        """Test resolving 'those' with multiple entities."""
        result = self.rag._resolve_references("Update those", ["Netflix", "Spotify"])

        assert result == "Update Netflix, Spotify"

    def test_resolve_the_subscription(self):
        """Test resolving 'the subscription' phrase."""
        result = self.rag._resolve_references("Cancel the subscription", ["Netflix"])

        assert result == "Cancel Netflix"

    def test_resolve_uses_most_recent_entity(self):
        """Test that single pronouns use most recent entity."""
        result = self.rag._resolve_references("Cancel it", ["Netflix", "Spotify"])

        # Should use last entity
        assert result == "Cancel Spotify"

    def test_resolve_case_insensitive(self):
        """Test that resolution is case-insensitive."""
        result = self.rag._resolve_references("Cancel IT", ["Netflix"])

        assert result == "Cancel Netflix"


class TestRAGServiceEntityExtraction:
    """Tests for RAGService entity extraction."""

    def setup_method(self):
        """Create fresh RAG service."""
        reset_rag_service()
        self.rag = RAGService()

    def teardown_method(self):
        """Reset services."""
        reset_rag_service()

    def test_extract_entities_from_turns(self):
        """Test extracting entities from conversation turns."""
        turns = [
            ConversationTurn(role="user", content="Add Netflix", entities=["Netflix"]),
            ConversationTurn(role="assistant", content="Added Netflix"),
            ConversationTurn(role="user", content="Add Spotify", entities=["Spotify"]),
        ]

        entities = self.rag._extract_entities(turns)

        assert "Netflix" in entities
        assert "Spotify" in entities

    def test_extract_entities_empty_turns(self):
        """Test extracting entities from empty list."""
        entities = self.rag._extract_entities([])

        assert entities == []

    def test_extract_entities_deduplicates(self):
        """Test that entities are deduplicated."""
        turns = [
            ConversationTurn(role="user", content="Netflix", entities=["Netflix"]),
            ConversationTurn(role="user", content="Netflix again", entities=["Netflix"]),
        ]

        entities = self.rag._extract_entities(turns)

        assert len(entities) == 1
        assert entities[0] == "Netflix"


class TestRAGServiceContextFormatting:
    """Tests for RAGService context formatting."""

    def setup_method(self):
        """Create fresh RAG service."""
        reset_rag_service()
        self.rag = RAGService()

    def teardown_method(self):
        """Reset services."""
        reset_rag_service()

    def test_format_context_empty(self):
        """Test formatting empty context."""
        context = ConversationContext(
            recent_turns=[],
            relevant_history=[],
            mentioned_entities=[],
            resolved_query="test",
        )

        result = self.rag.format_context_for_prompt(context)

        assert result == ""

    def test_format_context_with_recent_turns(self):
        """Test formatting context with recent turns."""
        context = ConversationContext(
            recent_turns=[
                ConversationTurn(role="user", content="Hello"),
                ConversationTurn(role="assistant", content="Hi there"),
            ],
            relevant_history=[],
            mentioned_entities=[],
            resolved_query="test",
        )

        result = self.rag.format_context_for_prompt(context)

        assert "Recent conversation:" in result
        assert "user: Hello" in result
        assert "assistant: Hi there" in result

    def test_format_context_with_entities(self):
        """Test formatting context with mentioned entities."""
        context = ConversationContext(
            recent_turns=[],
            relevant_history=[],
            mentioned_entities=["Netflix", "Spotify"],
            resolved_query="test",
        )

        result = self.rag.format_context_for_prompt(context)

        assert "Mentioned subscriptions: Netflix, Spotify" in result

    def test_format_context_limits_recent_turns(self):
        """Test that formatting limits recent turns to 3."""
        context = ConversationContext(
            recent_turns=[
                ConversationTurn(role="user", content="Message 1"),
                ConversationTurn(role="user", content="Message 2"),
                ConversationTurn(role="user", content="Message 3"),
                ConversationTurn(role="user", content="Message 4"),
                ConversationTurn(role="user", content="Message 5"),
            ],
            relevant_history=[],
            mentioned_entities=[],
            resolved_query="test",
        )

        result = self.rag.format_context_for_prompt(context)

        # Should only include last 3
        assert "Message 1" not in result
        assert "Message 2" not in result
        assert "Message 3" in result
        assert "Message 4" in result
        assert "Message 5" in result


class TestConversationTurn:
    """Tests for ConversationTurn dataclass."""

    def test_conversation_turn_defaults(self):
        """Test ConversationTurn default values."""
        turn = ConversationTurn(role="user", content="Hello")

        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.timestamp > 0
        assert turn.entities == []

    def test_conversation_turn_with_entities(self):
        """Test ConversationTurn with entities."""
        turn = ConversationTurn(
            role="user",
            content="Add Netflix",
            entities=["Netflix"],
        )

        assert turn.entities == ["Netflix"]


class TestConversationContext:
    """Tests for ConversationContext dataclass."""

    def test_conversation_context_creation(self):
        """Test ConversationContext creation."""
        context = ConversationContext(
            recent_turns=[ConversationTurn(role="user", content="Hello")],
            relevant_history=[],
            mentioned_entities=["Netflix"],
            resolved_query="Cancel Netflix",
        )

        assert len(context.recent_turns) == 1
        assert context.resolved_query == "Cancel Netflix"
        assert context.mentioned_entities == ["Netflix"]
