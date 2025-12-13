"""Search API endpoints for RAG-powered semantic search.

This module provides REST API endpoints for semantic search over
conversations and subscription notes using RAG.

The search endpoints support:
- Note search: Find subscriptions by semantic similarity of notes
- Conversation search: Find past conversations by similarity
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.dependencies import get_db
from src.services.conversation_service import ConversationService
from src.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request schema for search endpoints.

    Attributes:
        query: The search query string.
        user_id: User ID for data isolation.
        limit: Maximum number of results to return.

    Example:
        >>> request = SearchRequest(query="renewal", user_id="user-123")
    """

    query: str = Field(
        ...,
        description="Search query",
        min_length=1,
        examples=["subscriptions for work", "streaming services", "renewal notes"],
    )
    user_id: str = Field(
        default="default",
        description="User ID for data isolation",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results (1-20)",
    )


class NoteSearchResult(BaseModel):
    """A single note search result.

    Attributes:
        subscription_id: ID of the matching subscription.
        note: The note content.
        score: Relevance score (0-1, higher is more relevant).
    """

    subscription_id: str
    note: str
    score: float


class ConversationSearchResult(BaseModel):
    """A single conversation search result.

    Attributes:
        role: Message role (user or assistant).
        content: Message content.
        timestamp: When the message was sent.
        score: Relevance score (0-1, higher is more relevant).
    """

    role: str
    content: str
    timestamp: float
    score: float


class SearchResponse(BaseModel):
    """Response schema for search endpoints.

    Attributes:
        success: Whether the search was successful.
        query: The original search query.
        results: List of search results.
        total: Total number of results.
    """

    success: bool
    query: str
    results: list[NoteSearchResult] | list[ConversationSearchResult]
    total: int


@router.post("/notes", response_model=SearchResponse)
async def search_notes(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search subscription notes by semantic similarity.

    Performs a semantic search over all subscription notes for the user,
    returning the most relevant matches.

    Args:
        request: Search request with query and user ID.
        db: Async database session.

    Returns:
        SearchResponse with matching notes and scores.

    Raises:
        HTTPException: 503 if RAG is disabled, 500 on unexpected errors.

    Example:
        POST /api/search/notes
        {"query": "work subscriptions", "user_id": "user-123"}

        Response:
        {
            "success": true,
            "query": "work subscriptions",
            "results": [
                {"subscription_id": "...", "note": "Work expense", "score": 0.85}
            ],
            "total": 1
        }
    """
    if not settings.rag_enabled:
        raise HTTPException(
            status_code=503,
            detail="RAG search is not enabled. Set RAG_ENABLED=true to enable.",
        )

    try:
        rag = get_rag_service()
        results = await rag.search_notes(
            user_id=request.user_id,
            query=request.query,
            limit=request.limit,
        )

        return SearchResponse(
            success=True,
            query=request.query,
            results=[
                NoteSearchResult(
                    subscription_id=r["subscription_id"],
                    note=r["note"],
                    score=r["score"],
                )
                for r in results
            ],
            total=len(results),
        )

    except Exception as e:
        logger.exception(f"Note search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/conversations", response_model=SearchResponse)
async def search_conversations(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search conversation history by semantic similarity.

    Performs a semantic search over past conversations for the user,
    returning the most relevant matches.

    Args:
        request: Search request with query and user ID.
        db: Async database session.

    Returns:
        SearchResponse with matching conversation turns and scores.

    Raises:
        HTTPException: 503 if RAG is disabled, 500 on unexpected errors.

    Example:
        POST /api/search/conversations
        {"query": "cancellation requests", "user_id": "user-123"}

        Response:
        {
            "success": true,
            "query": "cancellation requests",
            "results": [
                {"role": "user", "content": "Cancel Netflix", "score": 0.92}
            ],
            "total": 1
        }
    """
    if not settings.rag_enabled:
        raise HTTPException(
            status_code=503,
            detail="RAG search is not enabled. Set RAG_ENABLED=true to enable.",
        )

    try:
        rag = get_rag_service()
        embedding = await rag.embedding_service.embed(request.query, use_cache=True)

        # Search the conversations collection
        from src.services.vector_store import VectorStore

        results = await rag.vector_store.search(
            collection_name=VectorStore.CONVERSATIONS_COLLECTION,
            vector=embedding,
            user_id=request.user_id,
            limit=request.limit,
        )

        return SearchResponse(
            success=True,
            query=request.query,
            results=[
                ConversationSearchResult(
                    role=r.payload.get("role", "unknown"),
                    content=r.payload.get("content", ""),
                    timestamp=r.payload.get("timestamp", 0),
                    score=r.score,
                )
                for r in results
            ],
            total=len(results),
        )

    except Exception as e:
        logger.exception(f"Conversation search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    user_id: str = "default",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get conversation history for a session.

    Retrieves persisted conversation turns for a specific session.

    Args:
        session_id: The session ID to retrieve history for.
        user_id: The user ID for data isolation.
        limit: Maximum number of turns to retrieve.
        db: Async database session.

    Returns:
        Dictionary with session info and conversation history.

    Example:
        GET /api/search/history/session-123?user_id=user-123

        Response:
        {
            "session_id": "session-123",
            "user_id": "user-123",
            "turns": [
                {"role": "user", "content": "Hello", "timestamp": "..."}
            ],
            "total": 1
        }
    """
    try:
        conversation_service = ConversationService(db)
        history = await conversation_service.get_session_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
        )

        return {
            "session_id": session_id,
            "user_id": user_id,
            "turns": [
                {
                    "id": turn.id,
                    "role": turn.role,
                    "content": turn.content,
                    "entities": turn.entities,
                    "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
                }
                for turn in history
            ],
            "total": len(history),
        }

    except Exception as e:
        logger.exception(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
