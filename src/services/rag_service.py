"""RAG (Retrieval-Augmented Generation) service for context retrieval.

This module provides the main RAG orchestration service that combines
embedding generation and vector search to provide relevant context
for the AI agent.

The service supports:
- Storing conversation turns for context retrieval
- Semantic search over past conversations
- Reference resolution (e.g., "it" -> "Netflix")
- Context building for agent prompts
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.core.config import settings
from src.services.embedding_service import get_embedding_service
from src.services.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """A single turn in a conversation.

    Attributes:
        role: Either "user" or "assistant".
        content: The message content.
        timestamp: Unix timestamp of the message.
        entities: Extracted entities (e.g., subscription names).
    """

    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    entities: list[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Context built from RAG for agent prompts.

    Attributes:
        recent_turns: Recent conversation turns from current session.
        relevant_history: Semantically similar past conversations.
        mentioned_entities: Entities mentioned in recent context.
        resolved_query: Query with pronouns resolved to entity names.
    """

    recent_turns: list[ConversationTurn]
    relevant_history: list[ConversationTurn]
    mentioned_entities: list[str]
    resolved_query: str


class RAGService:
    """Main RAG orchestration service.

    This service coordinates embedding generation, vector storage,
    and context retrieval to provide relevant context for the AI agent.

    It maintains a session-based conversation history and can retrieve
    semantically similar past conversations to augment agent responses.

    Attributes:
        embedding_service: Service for generating text embeddings.
        vector_store: Service for storing and searching vectors.

    Example:
        >>> rag = get_rag_service()
        >>> await rag.add_turn("user-1", "session-1", "user", "Add Netflix for £15.99")
        >>> context = await rag.get_context("user-1", "session-1", "Cancel it")
        >>> context.resolved_query
        'Cancel Netflix'
    """

    def __init__(self) -> None:
        """Initialize the RAG service with required dependencies."""
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

        # In-memory session storage (could be Redis in production)
        self._sessions: dict[str, list[ConversationTurn]] = {}

        logger.info("RAGService initialized")

    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """Generate a session key from user and session IDs.

        Args:
            user_id: The user's ID.
            session_id: The session ID.

        Returns:
            Combined session key.
        """
        return f"{user_id}:{session_id}"

    async def add_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        entities: list[str] | None = None,
    ) -> None:
        """Add a conversation turn to the session and vector store.

        Args:
            user_id: The user's ID.
            session_id: The current session ID.
            role: Either "user" or "assistant".
            content: The message content.
            entities: Optional list of extracted entities.

        Example:
            >>> await rag.add_turn("user-1", "session-1", "user", "Add Netflix")
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=time.time(),
            entities=entities or [],
        )

        # Add to in-memory session
        session_key = self._get_session_key(user_id, session_id)
        if session_key not in self._sessions:
            self._sessions[session_key] = []
        self._sessions[session_key].append(turn)

        # Keep only recent turns in memory (sliding window)
        max_turns = settings.rag_context_window * 2  # Store double for safety
        if len(self._sessions[session_key]) > max_turns:
            self._sessions[session_key] = self._sessions[session_key][-max_turns:]

        # Store in vector database for long-term retrieval
        if settings.rag_enabled:
            try:
                embedding = await self.embedding_service.embed(content, use_cache=True)
                vector_id = self.vector_store.generate_id()

                await self.vector_store.upsert(
                    collection_name=VectorStore.CONVERSATIONS_COLLECTION,
                    id=vector_id,
                    vector=embedding,
                    payload={
                        "user_id": user_id,
                        "session_id": session_id,
                        "role": role,
                        "content": content,
                        "timestamp": turn.timestamp,
                        "entities": turn.entities,
                    },
                )
                logger.debug(f"Stored turn in vector DB: {content[:50]}...")

            except Exception as e:
                logger.warning(f"Failed to store turn in vector DB: {e}")

    async def get_context(
        self,
        user_id: str,
        session_id: str,
        query: str,
    ) -> ConversationContext:
        """Build context for the agent from RAG.

        This method:
        1. Gets recent turns from the current session
        2. Searches for semantically similar past conversations
        3. Extracts mentioned entities
        4. Resolves pronouns in the query

        Args:
            user_id: The user's ID.
            session_id: The current session ID.
            query: The user's current query.

        Returns:
            ConversationContext with all relevant context for the agent.

        Example:
            >>> context = await rag.get_context("user-1", "session-1", "Cancel it")
            >>> print(context.resolved_query)
            'Cancel Netflix'
            >>> print(context.mentioned_entities)
            ['Netflix']
        """
        # Get recent turns from session
        session_key = self._get_session_key(user_id, session_id)
        recent_turns = self._sessions.get(session_key, [])[-settings.rag_context_window :]

        # Search for relevant history
        relevant_history: list[ConversationTurn] = []
        if settings.rag_enabled:
            try:
                query_embedding = await self.embedding_service.embed(query, use_cache=True)
                results = await self.vector_store.search(
                    collection_name=VectorStore.CONVERSATIONS_COLLECTION,
                    vector=query_embedding,
                    user_id=user_id,
                    limit=settings.rag_top_k,
                )

                # Convert to ConversationTurn objects
                for result in results:
                    # Skip if it's from current session (already in recent_turns)
                    if result.payload.get("session_id") == session_id:
                        continue

                    relevant_history.append(
                        ConversationTurn(
                            role=result.payload.get("role", "user"),
                            content=result.payload.get("content", ""),
                            timestamp=result.payload.get("timestamp", 0),
                            entities=result.payload.get("entities", []),
                        )
                    )

            except Exception as e:
                logger.warning(f"Failed to search relevant history: {e}")

        # Extract mentioned entities from recent context
        mentioned_entities = self._extract_entities(recent_turns)

        # Resolve pronouns in the query
        resolved_query = self._resolve_references(query, mentioned_entities)

        return ConversationContext(
            recent_turns=recent_turns,
            relevant_history=relevant_history,
            mentioned_entities=mentioned_entities,
            resolved_query=resolved_query,
        )

    def _extract_entities(self, turns: list[ConversationTurn]) -> list[str]:
        """Extract mentioned entities from conversation turns.

        This looks at explicitly tagged entities and attempts to find
        subscription names mentioned in the conversation.

        Args:
            turns: List of conversation turns to analyze.

        Returns:
            List of unique entity names found.
        """
        entities: set[str] = set()

        for turn in turns:
            # Add explicitly tagged entities
            entities.update(turn.entities)

        return list(entities)

    def _resolve_references(self, query: str, entities: list[str]) -> str:
        """Resolve pronoun references to entity names.

        This handles common pronouns like "it", "that", "them", "this"
        and replaces them with the most recently mentioned entity.

        Args:
            query: The user's query with potential pronouns.
            entities: List of recently mentioned entities.

        Returns:
            Query with pronouns resolved to entity names.

        Example:
            >>> rag._resolve_references("Cancel it", ["Netflix"])
            'Cancel Netflix'
            >>> rag._resolve_references("Update them", ["Spotify", "Netflix"])
            'Update Spotify, Netflix'
        """
        if not entities:
            return query

        # Common pronouns to resolve
        pronouns = ["it", "that", "this", "them", "those", "the subscription"]

        query_lower = query.lower()
        resolved = query

        for pronoun in pronouns:
            if pronoun in query_lower:
                # Replace with most recent entity (or all if "them"/"those")
                if pronoun in ["them", "those"] and len(entities) > 1:
                    replacement = ", ".join(entities)
                else:
                    replacement = entities[-1] if entities else pronoun

                # Case-insensitive replacement
                import re

                pattern = re.compile(re.escape(pronoun), re.IGNORECASE)
                resolved = pattern.sub(replacement, resolved, count=1)

        return resolved

    async def search_notes(
        self,
        user_id: str,
        query: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search subscription notes semantically.

        Args:
            user_id: The user's ID.
            query: Search query.
            limit: Maximum results (default from settings).

        Returns:
            List of matching notes with scores.
        """
        if not settings.rag_enabled:
            return []

        try:
            query_embedding = await self.embedding_service.embed(query, use_cache=True)
            results = await self.vector_store.search(
                collection_name=VectorStore.NOTES_COLLECTION,
                vector=query_embedding,
                user_id=user_id,
                limit=limit or settings.rag_top_k,
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "subscription_id": r.payload.get("subscription_id"),
                    "note": r.payload.get("note"),
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Note search failed: {e}")
            return []

    async def index_note(
        self,
        user_id: str,
        subscription_id: str,
        note: str,
    ) -> None:
        """Index a subscription note for semantic search.

        Args:
            user_id: The user's ID.
            subscription_id: The subscription's ID.
            note: The note content to index.
        """
        if not settings.rag_enabled or not note:
            return

        try:
            embedding = await self.embedding_service.embed(note, use_cache=True)
            vector_id = f"note:{subscription_id}"

            await self.vector_store.upsert(
                collection_name=VectorStore.NOTES_COLLECTION,
                id=vector_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "note": note,
                    "timestamp": time.time(),
                },
            )
            logger.debug(f"Indexed note for subscription {subscription_id}")

        except Exception as e:
            logger.warning(f"Failed to index note: {e}")

    def clear_session(self, user_id: str, session_id: str) -> None:
        """Clear in-memory session data.

        Args:
            user_id: The user's ID.
            session_id: The session ID to clear.
        """
        session_key = self._get_session_key(user_id, session_id)
        if session_key in self._sessions:
            del self._sessions[session_key]
            logger.debug(f"Cleared session {session_key}")

    def format_context_for_prompt(self, context: ConversationContext) -> str:
        """Format context as a string for inclusion in agent prompts.

        Args:
            context: The conversation context to format.

        Returns:
            Formatted string representation of the context.
        """
        parts = []

        if context.recent_turns:
            parts.append("Recent conversation:")
            for turn in context.recent_turns[-3:]:  # Last 3 turns
                parts.append(f"  {turn.role}: {turn.content}")

        if context.relevant_history:
            parts.append("\nRelevant past context:")
            for turn in context.relevant_history[:2]:  # Top 2 relevant
                parts.append(f"  {turn.role}: {turn.content}")

        if context.mentioned_entities:
            parts.append(f"\nMentioned subscriptions: {', '.join(context.mentioned_entities)}")

        return "\n".join(parts)


# Singleton instance
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Get the RAG service instance.

    This creates a singleton instance on first call.

    Returns:
        The RAGService instance.

    Example:
        >>> rag = get_rag_service()
        >>> context = await rag.get_context(...)
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def reset_rag_service() -> None:
    """Reset the RAG service singleton.

    Primarily useful for testing.
    """
    global _rag_service
    _rag_service = None
    logger.info("RAGService reset")
