"""Integration tests for Search API endpoints.

Tests cover:
- Note search endpoint
- Conversation search endpoint
- Session history endpoint
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestNoteSearchEndpoint:
    """Tests for POST /api/search/notes endpoint."""

    def test_note_search_rag_disabled(self, client):
        """Test that note search returns 503 when RAG is disabled."""
        with patch("src.api.search.settings") as mock_settings:
            mock_settings.rag_enabled = False

            response = client.post(
                "/api/search/notes",
                json={"query": "work subscriptions", "user_id": "user-1"},
            )

            assert response.status_code == 503
            data = response.json()
            # Support both old format (detail) and new format (error.message)
            message = data.get("detail") or data.get("error", {}).get("message", "")
            assert "RAG search is not enabled" in message

    def test_note_search_success(self, client):
        """Test successful note search."""
        mock_results = [
            {
                "id": "note-1",
                "subscription_id": "sub-1",
                "note": "Work expense",
                "score": 0.85,
            }
        ]

        with (
            patch("src.api.search.settings") as mock_settings,
            patch("src.api.search.get_rag_service") as mock_rag,
        ):
            mock_settings.rag_enabled = True
            mock_rag_instance = MagicMock()
            mock_rag_instance.search_notes = AsyncMock(return_value=mock_results)
            mock_rag.return_value = mock_rag_instance

            response = client.post(
                "/api/search/notes",
                json={"query": "work", "user_id": "user-1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["query"] == "work"
            assert len(data["results"]) == 1
            assert data["results"][0]["note"] == "Work expense"


class TestConversationSearchEndpoint:
    """Tests for POST /api/search/conversations endpoint."""

    def test_conversation_search_rag_disabled(self, client):
        """Test that conversation search returns 503 when RAG is disabled."""
        with patch("src.api.search.settings") as mock_settings:
            mock_settings.rag_enabled = False

            response = client.post(
                "/api/search/conversations",
                json={"query": "cancellation", "user_id": "user-1"},
            )

            assert response.status_code == 503


class TestSessionHistoryEndpoint:
    """Tests for GET /api/search/history/{session_id} endpoint."""

    def test_get_session_history(self, client):
        """Test retrieving session history."""
        from datetime import datetime

        mock_conversations = [
            MagicMock(
                id="conv-1",
                role="user",
                content="Hello",
                entities=["Netflix"],
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
            ),
            MagicMock(
                id="conv-2",
                role="assistant",
                content="Hi there!",
                entities=[],
                timestamp=datetime(2025, 1, 1, 12, 0, 1),
            ),
        ]

        with patch("src.api.search.ConversationService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_session_history = AsyncMock(return_value=mock_conversations)
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/search/history/session-123",
                params={"user_id": "user-1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session-123"
            assert data["user_id"] == "user-1"
            assert len(data["turns"]) == 2
            assert data["turns"][0]["role"] == "user"
            assert data["turns"][0]["content"] == "Hello"


class TestSearchRequestValidation:
    """Tests for request validation."""

    def test_empty_query_rejected(self, client):
        """Test that empty query is rejected."""
        response = client.post(
            "/api/search/notes",
            json={"query": "", "user_id": "user-1"},
        )

        assert response.status_code == 422  # Validation error

    def test_limit_bounds(self, client):
        """Test that limit respects bounds."""
        with patch("src.api.search.settings") as mock_settings:
            mock_settings.rag_enabled = False

            # Limit too high
            response = client.post(
                "/api/search/notes",
                json={"query": "test", "limit": 100},
            )

            assert response.status_code == 422

            # Limit too low
            response = client.post(
                "/api/search/notes",
                json={"query": "test", "limit": 0},
            )

            assert response.status_code == 422
