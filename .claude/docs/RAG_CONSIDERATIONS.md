# RAG (Retrieval-Augmented Generation) Considerations

## Overview

This document analyzes whether RAG is needed for the Subscription Tracker and provides implementation guidance if you decide to add it.

## Current Status: RAG Not Implemented

**Decision**: RAG is **not currently needed** for core functionality.

### Why RAG is Not Currently Needed

1. **Simple Domain**: Subscription management is well-defined
   - CRUD operations on structured data
   - Clear entity extraction (name, amount, frequency)
   - No complex knowledge retrieval needed

2. **Structured Data**: PostgreSQL handles all queries efficiently
   - Direct SQL queries for subscriptions
   - Aggregations for summaries
   - No unstructured text to search

3. **Stateless Commands**: Each command is independent
   - "Add Netflix £15.99 monthly" → Direct action
   - "Show my subscriptions" → Simple query
   - No need for conversation context

4. **Performance**: Current approach is faster
   - Direct database queries: <50ms
   - RAG would add: 200-500ms overhead
   - Not worth the latency for simple operations

## When to Consider Adding RAG

Add RAG if you implement these features:

### 1. Conversational Context
```python
# User: "Add Netflix for £15.99"
# User: "Actually, make that £12.99"  # ← Needs context of "that"
# User: "Cancel it"  # ← Needs to know what "it" refers to
```

**Implementation**: Store conversation history in vector database, retrieve context for ambiguous commands.

### 2. Natural Language Queries Over History
```python
# "What subscriptions did I add in January?"
# "Show me all the times I mentioned Spotify"
# "Find conversations where I talked about canceling subscriptions"
```

**Implementation**: Embed chat history and user notes, retrieve relevant conversations.

### 3. Intelligent Insights and Recommendations
```python
# "Why is my spending higher this month?"
# → Retrieve: previous spending patterns, notes, subscription changes
# → Generate: contextual analysis

# "Suggest subscriptions I should cancel"
# → Retrieve: usage notes, payment history, similar user patterns
# → Generate: personalized recommendations
```

**Implementation**: RAG over subscription notes, user behavior, and aggregated patterns.

### 4. Document/Note Search
```python
# If users can add notes to subscriptions:
# "Find the subscription where I noted 'annual renewal'"
# "What did I say about my gym membership?"
```

**Implementation**: Embed subscription notes, retrieve relevant documents.

## Recommended RAG Architecture (If Implementing)

### Technology Stack

```python
# Vector Database Options
VECTOR_DB_OPTIONS = {
    "pgvector": {
        "pros": ["PostgreSQL extension", "No additional infra", "SQL queries"],
        "cons": ["Less optimized than specialized DBs"],
        "recommended_for": "Small to medium scale"
    },
    "qdrant": {
        "pros": ["Fast", "Docker-friendly", "Good Python SDK"],
        "cons": ["Additional service to manage"],
        "recommended_for": "Production use"
    },
    "chromadb": {
        "pros": ["Lightweight", "Easy to use", "Great for dev"],
        "cons": ["Less production-ready"],
        "recommended_for": "Development and testing"
    }
}

# Embedding Models
EMBEDDING_OPTIONS = {
    "openai_ada_002": "Best quality, costs money",
    "sentence_transformers": "Free, good quality, runs locally",
    "claude_embeddings": "When Anthropic releases embedding API"
}
```

### Implementation Example

```python
"""RAG service for subscription tracker."""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class RAGService:
    """
    Retrieval-Augmented Generation service.

    Provides semantic search over conversation history, subscription notes,
    and user interactions to enhance agent responses with relevant context.

    Attributes:
        embedder: Sentence transformer model for creating embeddings
        vector_db: Qdrant client for vector storage and retrieval
        collection_name: Name of the vector collection
    """

    def __init__(
        self,
        vector_db_url: str = "http://localhost:6333",
        collection_name: str = "subscription_context"
    ):
        """
        Initialize RAG service.

        Args:
            vector_db_url: Qdrant server URL
            collection_name: Vector collection name
        """
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_db = QdrantClient(url=vector_db_url)
        self.collection_name = collection_name

        # Create collection if doesn't exist
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create vector collection if it doesn't exist."""
        collections = self.vector_db.get_collections().collections
        if self.collection_name not in [c.name for c in collections]:
            self.vector_db.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 embedding size
                    distance=Distance.COSINE
                )
            )

    async def index_conversation(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Index a conversation exchange for later retrieval.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Additional metadata (e.g., timestamp, intent)
        """
        # Combine user message and agent response for context
        text = f"User: {user_message}\nAgent: {agent_response}"

        # Create embedding
        embedding = self.embedder.encode(text).tolist()

        # Store in vector DB
        point = PointStruct(
            id=conversation_id,
            vector=embedding,
            payload={
                "user_id": user_id,
                "user_message": user_message,
                "agent_response": agent_response,
                "text": text,
                **(metadata or {})
            }
        )

        self.vector_db.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    async def retrieve_context(
        self,
        query: str,
        user_id: str,
        top_k: int = 5
    ) -> List[dict]:
        """
        Retrieve relevant context for a query.

        Args:
            query: User's current query
            user_id: User identifier for filtering
            top_k: Number of results to return

        Returns:
            List of relevant context items with scores

        Example:
            >>> rag = RAGService()
            >>> context = await rag.retrieve_context(
            ...     query="What did I say about Netflix?",
            ...     user_id="user123"
            ... )
            >>> for item in context:
            ...     print(f"Score: {item['score']}, Text: {item['text']}")
        """
        # Create query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Search vector DB
        results = self.vector_db.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter={"user_id": user_id},
            limit=top_k
        )

        # Format results
        context = []
        for result in results:
            context.append({
                "score": result.score,
                "text": result.payload["text"],
                "user_message": result.payload["user_message"],
                "agent_response": result.payload["agent_response"],
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k not in ["text", "user_message", "agent_response"]
                }
            })

        return context

    async def index_subscription_notes(
        self,
        subscription_id: str,
        user_id: str,
        notes: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Index subscription notes for semantic search.

        Args:
            subscription_id: Subscription identifier
            user_id: User identifier
            notes: Subscription notes text
            metadata: Additional metadata
        """
        if not notes or not notes.strip():
            return

        embedding = self.embedder.encode(notes).tolist()

        point = PointStruct(
            id=f"sub_{subscription_id}",
            vector=embedding,
            payload={
                "type": "subscription_notes",
                "subscription_id": subscription_id,
                "user_id": user_id,
                "notes": notes,
                **(metadata or {})
            }
        )

        self.vector_db.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
```

### Integration with Agent Executor

```python
class AgentExecutor:
    """Execute commands with RAG-enhanced context."""

    def __init__(
        self,
        db: AsyncSession,
        rag_service: Optional[RAGService] = None
    ):
        self.db = db
        self.rag_service = rag_service

    async def execute(
        self,
        command: ParsedCommand,
        user_id: str
    ) -> ExecutionResult:
        """
        Execute command with optional RAG context.

        If RAG is enabled and query is ambiguous, retrieve relevant context
        before executing the command.
        """
        context = None

        # Use RAG for ambiguous queries
        if self.rag_service and self._is_ambiguous(command):
            context = await self.rag_service.retrieve_context(
                query=command.raw_input,
                user_id=user_id,
                top_k=3
            )

        # Execute with context
        result = await self._execute_with_context(command, context)

        # Index this interaction
        if self.rag_service:
            await self.rag_service.index_conversation(
                user_id=user_id,
                conversation_id=str(uuid.uuid4()),
                user_message=command.raw_input,
                agent_response=result.message,
                metadata={
                    "intent": command.intent,
                    "timestamp": datetime.now().isoformat()
                }
            )

        return result

    def _is_ambiguous(self, command: ParsedCommand) -> bool:
        """Check if command has ambiguous references."""
        ambiguous_words = ["it", "that", "them", "this", "those"]
        return any(
            word in command.raw_input.lower().split()
            for word in ambiguous_words
        )
```

## Cost-Benefit Analysis

### Without RAG (Current)
**Pros:**
- ✅ Fast response times (<50ms)
- ✅ Simple architecture
- ✅ No additional infrastructure
- ✅ Lower operational costs
- ✅ Easier to debug

**Cons:**
- ❌ No conversation context
- ❌ Can't search notes semantically
- ❌ Limited to direct commands

### With RAG
**Pros:**
- ✅ Conversational context
- ✅ Semantic search over notes
- ✅ Better handling of ambiguous queries
- ✅ Richer insights and recommendations

**Cons:**
- ❌ Added complexity
- ❌ Additional infrastructure (vector DB)
- ❌ Higher latency (200-500ms)
- ❌ Increased costs (embedding + storage)
- ❌ More debugging complexity

## Recommendation

### Phase 1 (Current): No RAG
Keep the current simple architecture for MVP and initial users.

### Phase 2 (Future): Add RAG When Needed
Implement RAG if you add:
1. Multi-turn conversations
2. Extensive user notes on subscriptions
3. Historical pattern analysis
4. Personalized recommendations
5. Document/note search features

### Phase 3 (Scale): Hybrid Approach
Use both:
- Direct database queries for simple operations (fast)
- RAG for complex, context-dependent queries (smart)

## Implementation Checklist (If Adding RAG)

- [ ] Choose vector database (pgvector, Qdrant, or ChromaDB)
- [ ] Select embedding model (sentence-transformers recommended)
- [ ] Add RAG service to backend
- [ ] Integrate with agent executor
- [ ] Index conversation history
- [ ] Index subscription notes
- [ ] Add semantic search endpoints
- [ ] Update prompts to use retrieved context
- [ ] Add monitoring for retrieval quality
- [ ] Benchmark latency vs accuracy trade-offs

## Docker Compose Addition (If Implementing)

```yaml
# Add to docker-compose.yml if using Qdrant
qdrant:
  image: qdrant/qdrant:latest
  container_name: subscription-qdrant
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
  networks:
    - subscription-network

volumes:
  qdrant_data:
```

---

**Last Updated**: 2025-11-28
**Status**: RAG Not Currently Implemented
**Recommendation**: Add when conversational features are needed
