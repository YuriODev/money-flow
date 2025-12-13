"""Tests for VectorStore hybrid search functionality.

Tests cover:
- Hybrid search (semantic + keyword)
- Keyword boosting
- Keyword filter search
"""

from unittest.mock import MagicMock, patch

import pytest

from src.services.vector_store import SearchResult, VectorStore


class TestHybridSearch:
    """Tests for hybrid search functionality."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance with mocked client."""
        VectorStore.reset()
        store = VectorStore()
        return store

    @pytest.fixture
    def mock_search_results(self):
        """Create mock search results."""
        return [
            SearchResult(
                id="1",
                score=0.9,
                payload={"text": "Cancel my Netflix subscription", "user_id": "user-1"},
            ),
            SearchResult(
                id="2",
                score=0.8,
                payload={"text": "Show all subscriptions", "user_id": "user-1"},
            ),
            SearchResult(
                id="3",
                score=0.7,
                payload={"text": "Add Spotify for music", "user_id": "user-1"},
            ),
        ]

    @pytest.mark.asyncio
    async def test_hybrid_search_without_keywords(self, vector_store, mock_search_results):
        """Test hybrid search without keywords returns semantic results."""
        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = mock_search_results

            results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=None,
                limit=5,
            )

            assert len(results) == 3
            assert results[0].score == 0.9

    @pytest.mark.asyncio
    async def test_hybrid_search_boosts_keyword_matches(self, vector_store, mock_search_results):
        """Test that keyword matches boost scores."""
        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = mock_search_results

            results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["netflix"],
                limit=5,
            )

            # Netflix result should be boosted
            netflix_result = next(r for r in results if "Netflix" in r.payload["text"])
            assert netflix_result.payload.get("_keyword_matches", 0) > 0
            assert netflix_result.score > 0.9  # Boosted

    @pytest.mark.asyncio
    async def test_hybrid_search_multiple_keywords(self, vector_store, mock_search_results):
        """Test hybrid search with multiple keywords."""
        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = mock_search_results

            results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["cancel", "netflix"],
                limit=5,
            )

            # Result with both keywords should have higher boost
            netflix_cancel = next(r for r in results if "Cancel" in r.payload["text"])
            assert netflix_cancel.payload.get("_keyword_matches", 0) == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_preserves_original_score(self, vector_store, mock_search_results):
        """Test that original score is preserved in payload."""
        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = mock_search_results

            results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["netflix"],
                limit=5,
            )

            netflix_result = next(r for r in results if "Netflix" in r.payload["text"])
            assert netflix_result.payload.get("_original_score") == 0.9

    @pytest.mark.asyncio
    async def test_hybrid_search_reorders_by_boosted_score(self, vector_store):
        """Test that results are reordered by boosted score."""
        # Create results where keyword match is lower ranked semantically
        results = [
            SearchResult(
                id="1",
                score=0.9,
                payload={"text": "Something unrelated", "user_id": "user-1"},
            ),
            SearchResult(
                id="2",
                score=0.7,
                payload={"text": "Cancel Netflix now", "user_id": "user-1"},
            ),
        ]

        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = results

            hybrid_results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["netflix", "cancel"],
                boost_keyword_matches=0.15,
                limit=5,
            )

            # Netflix result should now be first due to keyword boost
            assert "Netflix" in hybrid_results[0].payload["text"]

    @pytest.mark.asyncio
    async def test_hybrid_search_empty_results(self, vector_store):
        """Test hybrid search with empty semantic results."""
        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = []

            results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["netflix"],
                limit=5,
            )

            assert results == []


class TestKeywordFilterSearch:
    """Tests for keyword filter search."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance."""
        VectorStore.reset()
        return VectorStore()

    @pytest.mark.asyncio
    async def test_keyword_filter_search_returns_matches(self, vector_store):
        """Test that keyword filter search returns matching records."""
        mock_client = MagicMock()
        mock_records = [
            MagicMock(id="1", payload={"text": "Netflix subscription", "user_id": "user-1"}),
            MagicMock(id="2", payload={"text": "Netflix account", "user_id": "user-1"}),
        ]
        mock_client.scroll.return_value = (mock_records, None)

        with patch.object(vector_store, "_ensure_client", return_value=mock_client):
            results = await vector_store.keyword_filter_search(
                collection_name="test",
                user_id="user-1",
                text_contains="Netflix",
            )

            assert len(results) == 2
            assert all(r.score == 1.0 for r in results)  # No similarity score

    @pytest.mark.asyncio
    async def test_keyword_filter_search_collection_not_found(self, vector_store):
        """Test keyword filter search handles missing collection."""
        from unittest.mock import MagicMock as MockHeaders

        from qdrant_client.http.exceptions import UnexpectedResponse

        mock_client = MagicMock()
        mock_headers = MockHeaders()
        mock_client.scroll.side_effect = UnexpectedResponse(
            status_code=404,
            reason_phrase="not found",
            content=b"",
            headers=mock_headers,
        )

        with patch.object(vector_store, "_ensure_client", return_value=mock_client):
            results = await vector_store.keyword_filter_search(
                collection_name="nonexistent",
                user_id="user-1",
                text_contains="test",
            )

            assert results == []


class TestHybridSearchScoreCapping:
    """Tests for score capping in hybrid search."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance."""
        VectorStore.reset()
        return VectorStore()

    @pytest.mark.asyncio
    async def test_boosted_score_capped_at_one(self, vector_store):
        """Test that boosted scores are capped at 1.0."""
        results = [
            SearchResult(
                id="1",
                score=0.95,
                payload={"text": "Cancel Netflix Spotify Disney", "user_id": "user-1"},
            ),
        ]

        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = results

            hybrid_results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["cancel", "netflix", "spotify", "disney"],
                boost_keyword_matches=0.1,
                limit=5,
            )

            # Score should be capped at 1.0
            assert hybrid_results[0].score <= 1.0

    @pytest.mark.asyncio
    async def test_keyword_boost_limit(self, vector_store):
        """Test that total keyword boost is limited."""
        results = [
            SearchResult(
                id="1",
                score=0.8,
                payload={
                    "text": "a b c d e f g h i j",  # Many matching words
                    "user_id": "user-1",
                },
            ),
        ]

        with patch.object(vector_store, "search") as mock_search:
            mock_search.return_value = results

            hybrid_results = await vector_store.hybrid_search(
                collection_name="test",
                vector=[0.1] * 384,
                user_id="user-1",
                keywords=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
                boost_keyword_matches=0.1,
                limit=5,
            )

            # Boost should be capped at 0.3 maximum
            max_expected_score = 0.8 + 0.3
            assert hybrid_results[0].score <= max_expected_score
