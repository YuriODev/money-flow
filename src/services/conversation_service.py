"""Conversation service for RAG-enhanced dialogue management.

This module provides the ConversationService class for managing conversation
sessions, persisting turns to the database, and integrating with the RAG
system for context retrieval and reference resolution.

The service supports:
- Session-based conversation tracking
- Database persistence for conversation history
- RAG context building for agent prompts
- Reference resolution ("it" → "Netflix")
- Entity extraction from agent responses
"""

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.rag import Conversation, RAGAnalytics
from src.services.rag_service import ConversationContext, get_rag_service

logger = logging.getLogger(__name__)


class ConversationService:
    """Manage conversations with RAG context support.

    This service handles conversation persistence and integrates with RAG
    for context retrieval. It maintains conversation history in both the
    database and vector store for semantic search.

    Attributes:
        db: Async database session.
        rag: RAG service for context operations.

    Example:
        >>> service = ConversationService(db_session)
        >>> await service.add_turn("user-1", "session-1", "user", "Add Netflix")
        >>> context = await service.get_context("user-1", "session-1", "Cancel it")
        >>> context.resolved_query
        'Cancel Netflix'
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the conversation service.

        Args:
            db: Async database session for persistence.
        """
        self.db = db
        self.rag = get_rag_service()
        logger.debug("ConversationService initialized")

    async def add_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        entities: list[str] | None = None,
    ) -> Conversation:
        """Add a conversation turn to the session.

        Persists the turn to both the database and vector store for
        future retrieval.

        Args:
            user_id: The user's identifier.
            session_id: The session identifier.
            role: Either "user" or "assistant".
            content: The message content.
            entities: Optional list of extracted entities (subscription names).

        Returns:
            The created Conversation database record.

        Example:
            >>> turn = await service.add_turn(
            ...     "user-1", "session-1", "user", "Add Netflix for £15.99"
            ... )
            >>> turn.content
            'Add Netflix for £15.99'
        """
        # Create database record
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            entities=entities or [],
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        # Also add to RAG service for in-memory session + vector store
        await self.rag.add_turn(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            entities=entities,
        )

        logger.debug(f"Added turn to session {session_id}: {content[:50]}...")
        return conversation

    async def get_context(
        self,
        user_id: str,
        session_id: str,
        query: str,
    ) -> ConversationContext:
        """Build RAG context for the current query.

        Retrieves recent conversation history and semantically similar
        past conversations, resolves references, and returns structured
        context for agent prompts.

        Args:
            user_id: The user's identifier.
            session_id: The current session identifier.
            query: The user's current query.

        Returns:
            ConversationContext with recent turns, relevant history,
            mentioned entities, and resolved query.

        Example:
            >>> context = await service.get_context("user-1", "session-1", "Cancel it")
            >>> context.resolved_query
            'Cancel Netflix'
        """
        start_time = time.time()

        context = await self.rag.get_context(
            user_id=user_id,
            session_id=session_id,
            query=query,
        )

        # Log analytics if enabled
        if settings.rag_enabled:
            total_latency = int((time.time() - start_time) * 1000)
            await self._log_analytics(
                user_id=user_id,
                query=query,
                resolved_query=context.resolved_query,
                context=context,
                total_latency_ms=total_latency,
            )

        return context

    async def get_session_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20,
    ) -> list[Conversation]:
        """Get conversation history for a session.

        Retrieves persisted conversation turns from the database,
        ordered by timestamp.

        Args:
            user_id: The user's identifier.
            session_id: The session identifier.
            limit: Maximum number of turns to retrieve (default 20).

        Returns:
            List of Conversation records, oldest first.

        Example:
            >>> history = await service.get_session_history("user-1", "session-1")
            >>> len(history)
            5
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[Conversation]:
        """Get all conversations for a user.

        Retrieves all conversation turns across all sessions,
        ordered by timestamp descending.

        Args:
            user_id: The user's identifier.
            limit: Maximum number of turns to retrieve (default 50).

        Returns:
            List of Conversation records, newest first.
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear_session(
        self,
        user_id: str,
        session_id: str,
    ) -> int:
        """Clear all turns from a session.

        Removes conversation turns from the database and in-memory
        session storage.

        Args:
            user_id: The user's identifier.
            session_id: The session identifier.

        Returns:
            Number of turns deleted.
        """
        # Get turns to delete
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.session_id == session_id)
        )
        turns = list(result.scalars().all())

        # Delete from database
        for turn in turns:
            await self.db.delete(turn)
        await self.db.commit()

        # Clear from RAG service in-memory session
        self.rag.clear_session(user_id, session_id)

        logger.info(f"Cleared {len(turns)} turns from session {session_id}")
        return len(turns)

    def format_context_for_prompt(self, context: ConversationContext) -> str:
        """Format context as a string for inclusion in agent prompts.

        Args:
            context: The conversation context to format.

        Returns:
            Formatted string suitable for inclusion in system prompts.
        """
        return self.rag.format_context_for_prompt(context)

    async def _log_analytics(
        self,
        user_id: str,
        query: str,
        resolved_query: str,
        context: ConversationContext,
        total_latency_ms: int,
        error: str | None = None,
    ) -> None:
        """Log RAG analytics to the database.

        Records performance metrics and quality indicators for
        monitoring and optimization.

        Args:
            user_id: The user's identifier.
            query: Original user query.
            resolved_query: Query after reference resolution.
            context: The built conversation context.
            total_latency_ms: Total RAG processing time.
            error: Optional error message if RAG failed.
        """
        try:
            analytics = RAGAnalytics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                query=query,
                resolved_query=resolved_query if resolved_query != query else None,
                context_turns=len(context.recent_turns),
                relevant_history_count=len(context.relevant_history),
                total_latency_ms=total_latency_ms,
                entities_resolved=(
                    {entity: entity for entity in context.mentioned_entities}
                    if context.mentioned_entities
                    else None
                ),
                error=error,
            )
            self.db.add(analytics)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to log RAG analytics: {e}")

    @staticmethod
    def extract_entities_from_response(
        response: dict[str, Any],
    ) -> list[str]:
        """Extract entity names from an agent response.

        Parses the response data to find subscription names that
        should be tracked for reference resolution.

        Args:
            response: Agent executor response dictionary.

        Returns:
            List of entity names found in the response.

        Example:
            >>> response = {"data": {"name": "Netflix"}}
            >>> entities = ConversationService.extract_entities_from_response(response)
            >>> entities
            ['Netflix']
        """
        entities = []
        data = response.get("data")

        if isinstance(data, dict):
            # Single subscription
            if "name" in data:
                entities.append(data["name"])
        elif isinstance(data, list):
            # List of subscriptions
            for item in data:
                if isinstance(item, dict) and "name" in item:
                    entities.append(item["name"])

        return entities


def generate_session_id() -> str:
    """Generate a new session ID.

    Returns:
        UUID string suitable for use as a session identifier.

    Example:
        >>> session_id = generate_session_id()
        >>> len(session_id)
        36
    """
    return str(uuid.uuid4())
