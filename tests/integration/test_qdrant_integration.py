"""Qdrant Vector Store Integration Tests for Sprint 2.3.4.

Tests for Qdrant vector database operations including:
- Vector insertion and retrieval
- Similarity search
- User-based filtering
- Collection management
- Connection failure handling
- Embedding update operations

Usage:
    pytest tests/integration/test_qdrant_integration.py -v

    # Run with real Qdrant (requires running Qdrant):
    docker-compose up qdrant -d
    pytest tests/integration/test_qdrant_integration.py -v
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.services.vector_store import SearchResult, VectorStore, get_vector_store

# Skip entire module if qdrant-client not installed
pytest.importorskip("qdrant_client")


class TestVectorInsertion:
    """Tests for vector insertion operations (2.3.4.1)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client."""
        client = MagicMock()
        client.get_collections.return_value = MagicMock(collections=[])
        client.create_collection.return_value = None
        client.get_collection.return_value = MagicMock(payload_schema={})
        client.create_payload_index.return_value = None
        client.upsert.return_value = None
        return client

    @pytest.fixture
    def sample_vector(self):
        """Create a sample embedding vector."""
        return [0.1] * 384  # Default embedding dimension

    @pytest.fixture
    def sample_payload(self):
        """Create a sample payload with required user_id."""
        return {
            "user_id": "test-user-1",
            "text": "Add Netflix subscription for $15.99 monthly",
            "timestamp": 1702500000,
            "session_id": "session-123",
        }

    @pytest.mark.asyncio
    async def test_upsert_single_vector(self, mock_client, sample_vector, sample_payload):
        """Test inserting a single vector into collection."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.upsert(
                collection_name="conversations",
                id="vec-001",
                vector=sample_vector,
                payload=sample_payload,
            )

            mock_client.upsert.assert_called_once()
            call_args = mock_client.upsert.call_args
            assert call_args.kwargs["collection_name"] == "conversations"
            assert len(call_args.kwargs["points"]) == 1
            point = call_args.kwargs["points"][0]
            assert point.id == "vec-001"
            assert point.payload == sample_payload

    @pytest.mark.asyncio
    async def test_upsert_requires_user_id(self, mock_client, sample_vector):
        """Test that upsert fails without user_id in payload."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            with pytest.raises(ValueError, match="user_id"):
                await store.upsert(
                    collection_name="conversations",
                    id="vec-001",
                    vector=sample_vector,
                    payload={"text": "Hello"},  # Missing user_id
                )

    @pytest.mark.asyncio
    async def test_upsert_batch_vectors(self, mock_client):
        """Test batch inserting multiple vectors."""
        store = get_vector_store()

        ids = ["vec-001", "vec-002", "vec-003"]
        vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        payloads = [
            {"user_id": "user-1", "text": "First message"},
            {"user_id": "user-1", "text": "Second message"},
            {"user_id": "user-1", "text": "Third message"},
        ]

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.upsert_batch(
                collection_name="conversations",
                ids=ids,
                vectors=vectors,
                payloads=payloads,
            )

            mock_client.upsert.assert_called_once()
            call_args = mock_client.upsert.call_args
            assert len(call_args.kwargs["points"]) == 3

    @pytest.mark.asyncio
    async def test_upsert_batch_validates_lengths(self, mock_client):
        """Test that batch upsert fails with mismatched lengths."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            with pytest.raises(ValueError, match="same length"):
                await store.upsert_batch(
                    collection_name="conversations",
                    ids=["vec-001", "vec-002"],
                    vectors=[[0.1] * 384],  # Only 1 vector
                    payloads=[{"user_id": "user-1"}],
                )

    @pytest.mark.asyncio
    async def test_upsert_creates_collection_if_not_exists(
        self, mock_client, sample_vector, sample_payload
    ):
        """Test that collection is created if it doesn't exist."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.upsert(
                collection_name="new_collection",
                id="vec-001",
                vector=sample_vector,
                payload=sample_payload,
            )

            mock_client.create_collection.assert_called_once()
            call_args = mock_client.create_collection.call_args
            assert call_args.kwargs["collection_name"] == "new_collection"

    @pytest.mark.asyncio
    async def test_generate_id_creates_valid_uuid(self):
        """Test that generate_id creates valid UUIDs."""
        id1 = VectorStore.generate_id()
        id2 = VectorStore.generate_id()

        # Should be valid UUIDs
        uuid.UUID(id1)
        uuid.UUID(id2)

        # Should be unique
        assert id1 != id2


class TestSimilaritySearch:
    """Tests for similarity search operations (2.3.4.2)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client with search results."""

        client = MagicMock()

        # Mock search results
        client.search.return_value = [
            MagicMock(
                id="vec-001",
                score=0.95,
                payload={
                    "text": "Netflix subscription",
                    "user_id": "user-1",
                    "timestamp": 1702500000,
                },
            ),
            MagicMock(
                id="vec-002",
                score=0.85,
                payload={
                    "text": "Spotify subscription",
                    "user_id": "user-1",
                    "timestamp": 1702400000,
                },
            ),
            MagicMock(
                id="vec-003",
                score=0.75,
                payload={
                    "text": "Disney+ subscription",
                    "user_id": "user-1",
                    "timestamp": 1702300000,
                },
            ),
        ]

        return client

    @pytest.mark.asyncio
    async def test_search_returns_similar_vectors(self, mock_client):
        """Test basic similarity search returns results."""
        store = get_vector_store()
        query_vector = [0.1] * 384

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="conversations",
                vector=query_vector,
                user_id="user-1",
                limit=5,
            )

            assert len(results) == 3
            assert all(isinstance(r, SearchResult) for r in results)
            assert results[0].score == 0.95
            assert results[0].payload["text"] == "Netflix subscription"

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, mock_client):
        """Test search respects result limit."""
        store = get_vector_store()
        query_vector = [0.1] * 384

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="conversations",
                vector=query_vector,
                user_id="user-1",
                limit=2,
            )

            # Should return at most 2 results
            assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_filters_by_min_score(self, mock_client):
        """Test search filters results by minimum score."""
        store = get_vector_store()
        query_vector = [0.1] * 384

        with patch.object(store, "_ensure_client", return_value=mock_client):
            mock_client.search.return_value = [
                MagicMock(
                    id="vec-001", score=0.95, payload={"text": "High score", "user_id": "user-1"}
                ),
            ]

            await store.search(
                collection_name="conversations",
                vector=query_vector,
                user_id="user-1",
                min_score=0.9,
            )

            # Verify score_threshold was passed
            call_args = mock_client.search.call_args
            assert call_args.kwargs["score_threshold"] == 0.9

    @pytest.mark.asyncio
    async def test_search_with_recency_boost(self, mock_client):
        """Test search with recency weighting."""
        store = get_vector_store()
        query_vector = [0.1] * 384

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="conversations",
                vector=query_vector,
                user_id="user-1",
                recency_weight=0.2,
                limit=5,
            )

            # Most recent should get a boost
            # Results should be re-ordered based on combined score
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_returns_empty_for_no_matches(self, mock_client):
        """Test search returns empty list when no matches found."""
        store = get_vector_store()
        mock_client.search.return_value = []

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-1",
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_hybrid_search_boosts_keywords(self, mock_client):
        """Test hybrid search boosts keyword matches."""
        store = get_vector_store()

        # Mock semantic search results
        semantic_results = [
            SearchResult(
                id="1", score=0.9, payload={"text": "Something unrelated", "user_id": "user-1"}
            ),
            SearchResult(
                id="2", score=0.7, payload={"text": "Cancel Netflix now", "user_id": "user-1"}
            ),
        ]

        with patch.object(store, "search", return_value=semantic_results):
            results = await store.hybrid_search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["netflix", "cancel"],
                boost_keyword_matches=0.15,
            )

            # Netflix result should now be first due to keyword boost
            assert "Netflix" in results[0].payload["text"]


class TestUserFiltering:
    """Tests for user_id filtering operations (2.3.4.3)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client."""

        client = MagicMock()

        # Return results filtered by user
        def mock_search(**kwargs):
            query_filter = kwargs.get("query_filter")
            # Check if user filter is applied correctly
            if query_filter:
                for cond in query_filter.must:
                    if hasattr(cond, "key") and cond.key == "user_id":
                        user_id = cond.match.value
                        # Return user-specific results
                        return [
                            MagicMock(
                                id=f"vec-{user_id}",
                                score=0.9,
                                payload={"text": f"Data for {user_id}", "user_id": user_id},
                            )
                        ]
            return []

        client.search.side_effect = mock_search
        return client

    @pytest.mark.asyncio
    async def test_search_filters_by_user_id(self, mock_client):
        """Test that search always filters by user_id."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-123",
            )

            # Verify user filter was applied
            assert len(results) == 1
            assert results[0].payload["user_id"] == "user-123"

    @pytest.mark.asyncio
    async def test_different_users_get_different_results(self, mock_client):
        """Test that different users see different data."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            # User 1 search
            results1 = await store.search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-1",
            )

            # User 2 search
            results2 = await store.search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-2",
            )

            # Results should be different
            assert results1[0].payload["user_id"] != results2[0].payload["user_id"]

    @pytest.mark.asyncio
    async def test_delete_by_user_removes_only_user_data(self):
        """Test that delete_by_user only removes specific user's data."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.delete.return_value = None

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.delete_by_user(
                collection_name="conversations",
                user_id="user-to-delete",
            )

            # Verify delete was called with user filter
            mock_client.delete.assert_called_once()
            call_args = mock_client.delete.call_args
            filter_selector = call_args.kwargs["points_selector"]
            # Check that filter contains user_id condition
            assert filter_selector.filter.must[0].key == "user_id"
            assert filter_selector.filter.must[0].match.value == "user-to-delete"

    @pytest.mark.asyncio
    async def test_count_by_user_returns_user_specific_count(self):
        """Test that count with user_id returns user-specific count."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.count.return_value = MagicMock(count=5)

        with patch.object(store, "_ensure_client", return_value=mock_client):
            count = await store.count(
                collection_name="conversations",
                user_id="user-1",
            )

            assert count == 5
            # Verify user filter was passed
            mock_client.count.assert_called_once()
            call_args = mock_client.count.call_args
            assert call_args.kwargs.get("count_filter") is not None

    @pytest.mark.asyncio
    async def test_search_with_additional_filters(self, mock_client):
        """Test search with additional filters beyond user_id."""

        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.search(
                collection_name="conversations",
                vector=[0.1] * 384,
                user_id="user-1",
                filters={"session_id": "session-abc"},
            )

            # Verify both user_id and additional filter were applied
            call_args = mock_client.search.call_args
            query_filter = call_args.kwargs["query_filter"]

            # Should have 2 conditions (user_id and session_id)
            assert len(query_filter.must) == 2


class TestCollectionManagement:
    """Tests for collection management operations (2.3.4.4)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client."""
        client = MagicMock()
        client.get_collections.return_value = MagicMock(collections=[])
        client.create_collection.return_value = None
        client.get_collection.return_value = MagicMock(payload_schema={})
        client.create_payload_index.return_value = None
        return client

    @pytest.mark.asyncio
    async def test_ensure_collection_creates_new(self, mock_client):
        """Test ensure_collection creates collection if not exists."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.ensure_collection("new_collection")

            mock_client.create_collection.assert_called_once()
            call_args = mock_client.create_collection.call_args
            assert call_args.kwargs["collection_name"] == "new_collection"

    @pytest.mark.asyncio
    async def test_ensure_collection_skips_existing(self):
        """Test ensure_collection does not recreate existing collection."""
        store = get_vector_store()

        # Create fresh mock with existing collection
        mock_client = MagicMock()
        existing_coll = MagicMock()
        existing_coll.name = "existing_collection"
        mock_client.get_collections.return_value = MagicMock(collections=[existing_coll])
        mock_client.get_collection.return_value = MagicMock(
            payload_schema={"user_id": {}, "timestamp": {}}
        )

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.ensure_collection("existing_collection")

            # Should not try to create since collection exists
            mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_collection_creates_payload_indexes(self, mock_client):
        """Test that ensure_collection creates payload indexes."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            await store.ensure_collection("new_collection")

            # Should create indexes for user_id, timestamp, session_id, subscription_id
            assert mock_client.create_payload_index.call_count >= 4

    @pytest.mark.asyncio
    async def test_collection_names_constants(self):
        """Test that collection name constants are defined."""
        assert VectorStore.CONVERSATIONS_COLLECTION == "conversations"
        assert VectorStore.NOTES_COLLECTION == "notes"

    @pytest.mark.asyncio
    async def test_get_by_id_retrieves_point(self):
        """Test retrieving a specific vector by ID."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.retrieve.return_value = [
            MagicMock(
                id="vec-123",
                payload={"text": "Test data", "user_id": "user-1"},
            )
        ]

        with patch.object(store, "_ensure_client", return_value=mock_client):
            result = await store.get_by_id("conversations", "vec-123")

            assert result is not None
            assert result.id == "vec-123"
            assert result.payload["text"] == "Test data"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self):
        """Test get_by_id returns None for non-existent ID."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.retrieve.return_value = []

        with patch.object(store, "_ensure_client", return_value=mock_client):
            result = await store.get_by_id("conversations", "non-existent")

            assert result is None


class TestConnectionFailureHandling:
    """Tests for connection failure handling (2.3.4.5)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.mark.asyncio
    async def test_connection_error_raises_exception(self):
        """Test that connection failure raises ConnectionError."""
        store = get_vector_store()

        with patch("src.services.vector_store.QdrantClient") as mock_qdrant_client:
            mock_qdrant_client.side_effect = Exception("Connection refused")
            VectorStore._client = None  # Force reconnection

            with pytest.raises(ConnectionError, match="Failed to connect"):
                store._ensure_client()

    @pytest.mark.asyncio
    async def test_search_handles_collection_not_found(self):
        """Test search returns empty on collection not found."""
        from qdrant_client.http.exceptions import UnexpectedResponse

        store = get_vector_store()
        mock_client = MagicMock()
        mock_headers = MagicMock()
        mock_client.search.side_effect = UnexpectedResponse(
            status_code=404,
            reason_phrase="Collection not found",
            content=b"",
            headers=mock_headers,
        )

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.search(
                collection_name="non_existent",
                vector=[0.1] * 384,
                user_id="user-1",
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_upsert_error_raises_runtime_error(self):
        """Test that upsert failure raises RuntimeError."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.get_collections.return_value = MagicMock(
            collections=[MagicMock(name="conversations")]
        )
        mock_client.get_collection.return_value = MagicMock(payload_schema={})
        mock_client.upsert.side_effect = Exception("Upsert failed")

        with patch.object(store, "_ensure_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to upsert"):
                await store.upsert(
                    collection_name="conversations",
                    id="vec-001",
                    vector=[0.1] * 384,
                    payload={"user_id": "user-1"},
                )

    @pytest.mark.asyncio
    async def test_delete_error_raises_runtime_error(self):
        """Test that delete failure raises RuntimeError."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Delete failed")

        with patch.object(store, "_ensure_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to delete"):
                await store.delete(
                    collection_name="conversations",
                    ids=["vec-001"],
                )

    @pytest.mark.asyncio
    async def test_count_handles_error_gracefully(self):
        """Test that count returns 0 on error."""
        store = get_vector_store()
        mock_client = MagicMock()
        mock_client.count.side_effect = Exception("Count failed")

        with patch.object(store, "_ensure_client", return_value=mock_client):
            count = await store.count("conversations", "user-1")

            assert count == 0

    @pytest.mark.asyncio
    async def test_keyword_filter_search_handles_collection_not_found(self):
        """Test keyword filter search handles missing collection."""
        from qdrant_client.http.exceptions import UnexpectedResponse

        store = get_vector_store()
        mock_client = MagicMock()
        mock_headers = MagicMock()
        mock_client.scroll.side_effect = UnexpectedResponse(
            status_code=404,
            reason_phrase="not found",
            content=b"",
            headers=mock_headers,
        )

        with patch.object(store, "_ensure_client", return_value=mock_client):
            results = await store.keyword_filter_search(
                collection_name="non_existent",
                user_id="user-1",
                text_contains="test",
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_import_error_for_missing_qdrant_client(self):
        """Test that ImportError is raised when qdrant-client not installed."""
        store = VectorStore()

        with patch("src.services.vector_store.QDRANT_AVAILABLE", False):
            VectorStore._client = None  # Force check

            with pytest.raises(ImportError, match="qdrant-client is required"):
                store._ensure_client()


class TestEmbeddingUpdateOperations:
    """Tests for embedding update operations (2.3.4.6)."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client."""
        client = MagicMock()
        client.get_collections.return_value = MagicMock(
            collections=[MagicMock(name="conversations")]
        )
        client.get_collection.return_value = MagicMock(
            payload_schema={"user_id": {}, "timestamp": {}}
        )
        client.upsert.return_value = None
        client.delete.return_value = None
        return client

    @pytest.mark.asyncio
    async def test_update_vector_with_same_id(self, mock_client):
        """Test updating a vector by upserting with same ID."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            # Initial insert
            await store.upsert(
                collection_name="conversations",
                id="vec-update-001",
                vector=[0.1] * 384,
                payload={"user_id": "user-1", "text": "Original text"},
            )

            # Update with same ID
            await store.upsert(
                collection_name="conversations",
                id="vec-update-001",
                vector=[0.2] * 384,  # Different vector
                payload={"user_id": "user-1", "text": "Updated text"},
            )

            # Should have called upsert twice
            assert mock_client.upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_update_vectors(self, mock_client):
        """Test batch updating multiple vectors."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            ids = ["vec-001", "vec-002"]
            new_vectors = [[0.5] * 384, [0.6] * 384]
            new_payloads = [
                {"user_id": "user-1", "text": "Updated 1"},
                {"user_id": "user-1", "text": "Updated 2"},
            ]

            await store.upsert_batch(
                collection_name="conversations",
                ids=ids,
                vectors=new_vectors,
                payloads=new_payloads,
            )

            mock_client.upsert.assert_called_once()
            call_args = mock_client.upsert.call_args
            assert len(call_args.kwargs["points"]) == 2

    @pytest.mark.asyncio
    async def test_delete_then_insert_new_version(self, mock_client):
        """Test deleting and inserting as update pattern."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            # Delete old version
            await store.delete("conversations", ["vec-001"])

            # Insert new version
            await store.upsert(
                collection_name="conversations",
                id="vec-001",
                vector=[0.3] * 384,
                payload={"user_id": "user-1", "text": "New version"},
            )

            mock_client.delete.assert_called_once()
            mock_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preserves_user_id(self, mock_client):
        """Test that updates must still include user_id."""
        store = get_vector_store()

        with patch.object(store, "_ensure_client", return_value=mock_client):
            with pytest.raises(ValueError, match="user_id"):
                await store.upsert(
                    collection_name="conversations",
                    id="vec-001",
                    vector=[0.1] * 384,
                    payload={"text": "Missing user_id"},  # No user_id
                )


class TestRecencyBoost:
    """Tests for recency boost functionality."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    def test_apply_recency_boost_empty_results(self):
        """Test recency boost with empty results."""
        store = get_vector_store()
        results = store._apply_recency_boost([], 0.2)
        assert results == []

    def test_apply_recency_boost_favors_recent(self):
        """Test that recency boost favors recent items."""
        store = get_vector_store()
        results = [
            SearchResult(id="1", score=0.9, payload={"timestamp": 1000}),
            SearchResult(id="2", score=0.8, payload={"timestamp": 2000}),  # More recent
        ]

        boosted = store._apply_recency_boost(results, 0.3)

        # Most recent should get higher combined score
        # ID "2" should now be first due to recency
        assert boosted[0].id == "2"

    def test_apply_recency_boost_clamps_weight(self):
        """Test that recency weight is clamped to 0.0-0.5."""
        store = get_vector_store()
        results = [
            SearchResult(id="1", score=0.9, payload={"timestamp": 1000}),
        ]

        # Should clamp 0.8 to 0.5
        boosted = store._apply_recency_boost(results, 0.8)
        # Score should be affected but result should work
        assert len(boosted) == 1

    def test_apply_recency_boost_handles_missing_timestamp(self):
        """Test recency boost handles items without timestamp."""
        store = get_vector_store()
        results = [
            SearchResult(id="1", score=0.9, payload={}),  # No timestamp
            SearchResult(id="2", score=0.8, payload={"timestamp": 2000}),
        ]

        boosted = store._apply_recency_boost(results, 0.2)
        assert len(boosted) == 2


class TestSingletonBehavior:
    """Tests for VectorStore singleton behavior."""

    @pytest.fixture(autouse=True)
    def reset_vector_store(self):
        """Reset vector store before each test."""
        VectorStore.reset()
        yield
        VectorStore.reset()

    def test_singleton_returns_same_instance(self):
        """Test that VectorStore returns same instance."""
        store1 = VectorStore()
        store2 = VectorStore()

        assert store1 is store2

    def test_get_vector_store_returns_singleton(self):
        """Test that get_vector_store returns singleton."""
        store1 = get_vector_store()
        store2 = get_vector_store()

        assert store1 is store2

    def test_reset_clears_instance(self):
        """Test that reset creates fresh instance."""
        store1 = VectorStore()
        VectorStore.reset()
        store2 = VectorStore()

        # After reset, should be different object
        assert store1 is not store2

    def test_client_is_shared_across_instances(self):
        """Test that client is shared via class variable."""
        # Client is stored as class variable
        assert hasattr(VectorStore, "_client")
        assert hasattr(VectorStore, "_instance")
