"""RAG (Retrieval-Augmented Generation) service for context retrieval.

This module provides the main RAG orchestration service that combines
embedding generation and vector search to provide relevant context
for the AI agent.

The service supports:
- Storing conversation turns for context retrieval (Redis-backed)
- Semantic search over past conversations
- Reference resolution (e.g., "it" -> "Netflix")
- Context building for agent prompts
- Cache invalidation on subscription changes
"""

import logging
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from src.core.config import settings
from src.services.embedding_service import get_embedding_service
from src.services.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)

# Session TTL in seconds (1 hour default)
SESSION_TTL = 3600


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

    It maintains a session-based conversation history using Redis for
    persistence across restarts. Falls back to in-memory storage if
    Redis is unavailable.

    Attributes:
        embedding_service: Service for generating text embeddings.
        vector_store: Service for storing and searching vectors.
        cache: Optional Redis cache service for session persistence.

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
        self.cache: Any = None  # Will be set via set_cache()

        # In-memory session fallback (used when Redis is unavailable)
        self._sessions: dict[str, list[ConversationTurn]] = {}

        logger.info("RAGService initialized")

    def set_cache(self, cache: Any) -> None:
        """Set the cache service for session persistence.

        This enables Redis-backed session storage for conversation turns.
        Should be called after cache service initialization.

        Args:
            cache: The cache service instance (CacheService).
        """
        self.cache = cache
        # Also inject cache into embedding service
        self.embedding_service.set_cache(cache)
        logger.info("RAGService: Cache service configured for sessions and embeddings")

    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """Generate a session key from user and session IDs.

        Args:
            user_id: The user's ID.
            session_id: The session ID.

        Returns:
            Combined session key for in-memory storage.
        """
        return f"{user_id}:{session_id}"

    def _get_redis_session_key(self, user_id: str, session_id: str) -> str:
        """Generate a Redis key for session storage.

        Args:
            user_id: The user's ID.
            session_id: The session ID.

        Returns:
            Redis key with rag:session prefix.
        """
        return f"rag:session:{user_id}:{session_id}"

    async def _get_session_from_cache(
        self, user_id: str, session_id: str
    ) -> list[ConversationTurn]:
        """Get session turns from Redis cache.

        Args:
            user_id: The user's ID.
            session_id: The session ID.

        Returns:
            List of conversation turns from cache, or empty list.
        """
        if not self.cache:
            return []

        try:
            redis_key = self._get_redis_session_key(user_id, session_id)
            cached = await self.cache.get(redis_key)
            if cached:
                # Convert dict list back to ConversationTurn objects
                return [
                    ConversationTurn(
                        role=t["role"],
                        content=t["content"],
                        timestamp=t.get("timestamp", 0),
                        entities=t.get("entities", []),
                    )
                    for t in cached
                ]
        except Exception as e:
            logger.warning(f"Failed to get session from cache: {e}")

        return []

    async def _save_session_to_cache(
        self, user_id: str, session_id: str, turns: list[ConversationTurn]
    ) -> None:
        """Save session turns to Redis cache.

        Args:
            user_id: The user's ID.
            session_id: The session ID.
            turns: List of conversation turns to save.
        """
        if not self.cache:
            return

        try:
            redis_key = self._get_redis_session_key(user_id, session_id)
            # Convert to dict list for JSON serialization
            turns_data = [asdict(t) for t in turns]
            await self.cache.set(redis_key, turns_data, ttl=SESSION_TTL)
        except Exception as e:
            logger.warning(f"Failed to save session to cache: {e}")

    async def add_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        entities: list[str] | None = None,
    ) -> None:
        """Add a conversation turn to the session and vector store.

        Stores turns in Redis for persistence across restarts, with
        in-memory fallback. Also indexes in vector DB for semantic search.

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

        # Get existing session (prefer Redis, fallback to memory)
        session_key = self._get_session_key(user_id, session_id)
        if self.cache:
            turns = await self._get_session_from_cache(user_id, session_id)
            if not turns:
                # Check in-memory fallback
                turns = self._sessions.get(session_key, [])
        else:
            turns = self._sessions.get(session_key, [])

        # Add new turn
        turns.append(turn)

        # Keep only recent turns (consistent window size)
        max_turns = settings.rag_context_window
        if len(turns) > max_turns:
            turns = turns[-max_turns:]

        # Save to Redis (preferred) and in-memory (fallback)
        if self.cache:
            await self._save_session_to_cache(user_id, session_id, turns)
        self._sessions[session_key] = turns

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
        1. Gets recent turns from the current session (Redis or memory)
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
        # Get recent turns from session (prefer Redis, fallback to memory)
        session_key = self._get_session_key(user_id, session_id)
        if self.cache:
            recent_turns = await self._get_session_from_cache(user_id, session_id)
            if not recent_turns:
                recent_turns = self._sessions.get(session_key, [])
        else:
            recent_turns = self._sessions.get(session_key, [])

        # Apply context window (consistent size)
        recent_turns = recent_turns[-settings.rag_context_window :]

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
        Uses word boundaries to avoid matching substrings within words.

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

        # Common pronouns to resolve (ordered by specificity)
        pronouns = ["the subscription", "them", "those", "that", "this", "it"]

        resolved = query

        for pronoun in pronouns:
            # Use word boundaries to avoid matching substrings (e.g., "them" in "anthem")
            pattern = re.compile(r"\b" + re.escape(pronoun) + r"\b", re.IGNORECASE)

            if pattern.search(resolved):
                # Replace with most recent entity (or all if "them"/"those")
                if pronoun in ["them", "those"] and len(entities) > 1:
                    replacement = ", ".join(entities)
                else:
                    replacement = entities[-1] if entities else pronoun

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

    async def clear_session(self, user_id: str, session_id: str) -> None:
        """Clear session data from Redis and memory.

        Args:
            user_id: The user's ID.
            session_id: The session ID to clear.
        """
        session_key = self._get_session_key(user_id, session_id)

        # Clear from Redis
        if self.cache:
            try:
                redis_key = self._get_redis_session_key(user_id, session_id)
                await self.cache.delete(redis_key)
            except Exception as e:
                logger.warning(f"Failed to clear session from cache: {e}")

        # Clear from memory
        if session_key in self._sessions:
            del self._sessions[session_key]
            logger.debug(f"Cleared session {session_key}")

    async def invalidate_subscription_cache(self, subscription_id: str) -> None:
        """Invalidate cached data related to a subscription.

        Should be called when a subscription is updated or deleted
        to ensure RAG doesn't return stale context.

        Args:
            subscription_id: The subscription's ID.
        """
        if not self.cache:
            return

        try:
            # Invalidate note embedding cache
            note_key = f"note:{subscription_id}"
            await self.cache.delete(note_key)

            # Delete the note from vector store
            if settings.rag_enabled:
                await self.vector_store.delete(
                    collection_name=VectorStore.NOTES_COLLECTION,
                    id=note_key,
                )

            logger.debug(f"Invalidated RAG cache for subscription {subscription_id}")

        except Exception as e:
            logger.warning(f"Failed to invalidate subscription cache: {e}")

    async def invalidate_embedding_cache(self, text: str) -> None:
        """Invalidate a specific embedding from cache.

        Args:
            text: The text whose embedding should be invalidated.
        """
        if not self.cache:
            return

        try:
            cache_key = self.embedding_service._get_cache_key(text)
            await self.cache.delete(cache_key)
            logger.debug(f"Invalidated embedding cache for: {text[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to invalidate embedding cache: {e}")

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
