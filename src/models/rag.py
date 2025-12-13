"""RAG (Retrieval-Augmented Generation) ORM models.

This module defines SQLAlchemy ORM models for RAG-related data storage,
including conversation history and analytics.

The models support the RAG system's needs for:
- Storing conversation turns for context retrieval
- Tracking RAG query performance and analytics
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class Conversation(Base):
    """Conversation turn model for RAG context retrieval.

    Stores individual conversation turns (user messages and assistant responses)
    for use in building context for the AI agent. Vectors are stored separately
    in Qdrant, with this table providing the source of truth for content.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: User identifier for data isolation.
        session_id: Session identifier for grouping conversation turns.
        role: Either "user" or "assistant".
        content: The message content.
        entities: JSON array of extracted entities (e.g., subscription names).
        timestamp: When the message was sent.
        created_at: Record creation timestamp.

    Example:
        >>> conversation = Conversation(
        ...     user_id="user-123",
        ...     session_id="session-456",
        ...     role="user",
        ...     content="Add Netflix for £15.99",
        ...     entities=["Netflix"],
        ... )
    """

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    entities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return string representation of conversation turn.

        Returns:
            Debug-friendly string with role and content preview.
        """
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Conversation(role='{self.role}', content='{content_preview}')>"


class RAGAnalytics(Base):
    """RAG analytics model for tracking query performance.

    Records metrics for each RAG query to enable performance monitoring,
    debugging, and optimization. Tracks latencies, cache hits, and quality
    metrics.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: User identifier.
        query: The original user query.
        resolved_query: Query after reference resolution (e.g., "it" -> "Netflix").
        context_turns: Number of recent conversation turns included.
        relevant_history_count: Number of semantically similar turns found.
        embedding_latency_ms: Time to generate embedding in milliseconds.
        search_latency_ms: Time to search vector database in milliseconds.
        total_latency_ms: Total RAG processing time in milliseconds.
        cache_hit: Whether the embedding was retrieved from cache.
        avg_relevance_score: Average relevance score of retrieved results.
        entities_resolved: JSON object of resolved entity references.
        error: Error message if RAG processing failed.
        created_at: Record creation timestamp.

    Example:
        >>> analytics = RAGAnalytics(
        ...     user_id="user-123",
        ...     query="Cancel it",
        ...     resolved_query="Cancel Netflix",
        ...     total_latency_ms=150,
        ...     cache_hit=True,
        ... )
    """

    __tablename__ = "rag_analytics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_turns: Mapped[int] = mapped_column(Integer, default=0)
    relevant_history_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    entities_resolved: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return string representation of RAG analytics.

        Returns:
            Debug-friendly string with query and latency.
        """
        query_preview = self.query[:30] + "..." if len(self.query) > 30 else self.query
        return f"<RAGAnalytics(query='{query_preview}', latency={self.total_latency_ms}ms)>"
