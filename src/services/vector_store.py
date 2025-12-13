"""Vector store service for Qdrant operations.

This module provides a wrapper around the Qdrant client for vector database operations.
It handles storing and retrieving embeddings for RAG (Retrieval-Augmented Generation).

The service supports:
- Collection management (create, delete, check existence)
- Vector CRUD operations (upsert, delete, search)
- Filtering by user_id for data isolation
- Similarity search with score thresholds
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any, ClassVar

from src.core.config import settings

# RAG dependencies are optional - only import if RAG is enabled
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.exceptions import UnexpectedResponse

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None  # type: ignore
    models = None  # type: ignore
    UnexpectedResponse = Exception  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from a vector similarity search.

    Attributes:
        id: Unique identifier of the vector.
        score: Similarity score (0-1, higher is more similar).
        payload: Associated metadata stored with the vector.
    """

    id: str
    score: float
    payload: dict[str, Any]


class VectorStore:
    """Qdrant vector store wrapper for RAG operations.

    This service provides a high-level interface for interacting with Qdrant.
    It handles collection management, vector storage, and similarity search.

    All operations filter by user_id to ensure data isolation between users.

    Attributes:
        collection_name: Name of the Qdrant collection to use.
        dimension: Dimension of vectors (must match embedding model).

    Example:
        >>> store = get_vector_store()
        >>> await store.upsert(
        ...     id="conv-123",
        ...     vector=[0.1, 0.2, ...],
        ...     payload={"text": "Hello", "user_id": "user-1"}
        ... )
        >>> results = await store.search(
        ...     vector=[0.1, 0.2, ...],
        ...     user_id="user-1",
        ...     limit=5
        ... )
    """

    _instance: ClassVar["VectorStore | None"] = None
    _client: ClassVar[Any] = None  # QdrantClient when available

    # Collection names
    CONVERSATIONS_COLLECTION = "conversations"
    NOTES_COLLECTION = "notes"

    def __new__(cls) -> "VectorStore":
        """Create or return the singleton instance.

        Returns:
            The singleton VectorStore instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the vector store.

        The Qdrant client is created lazily on first operation.
        """
        if getattr(self, "_initialized", False):
            return

        self.dimension = settings.embedding_dimension
        self._initialized = True
        logger.info(f"VectorStore initialized for {settings.qdrant_host}:{settings.qdrant_port}")

    def _ensure_client(self) -> Any:  # Returns QdrantClient
        """Get or create the Qdrant client.

        Returns:
            The Qdrant client instance.

        Raises:
            ConnectionError: If cannot connect to Qdrant.
            ImportError: If qdrant-client is not installed.
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client is required for RAG features. "
                "Install with: pip install 'subscription-tracker[rag]'"
            )

        if VectorStore._client is None:
            try:
                VectorStore._client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    prefer_grpc=True,
                    grpc_port=settings.qdrant_grpc_port,
                )
                logger.info("Connected to Qdrant")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise ConnectionError(f"Failed to connect to Qdrant: {e}") from e

        return VectorStore._client

    async def ensure_collection(self, collection_name: str) -> None:
        """Ensure a collection exists, creating it if necessary.

        Args:
            collection_name: Name of the collection to ensure exists.

        Raises:
            RuntimeError: If collection creation fails.
        """
        client = self._ensure_client()

        try:
            collections = client.get_collections()
            existing = [c.name for c in collections.collections]

            if collection_name not in existing:
                logger.info(f"Creating collection: {collection_name}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info(f"Collection created: {collection_name}")
            else:
                logger.debug(f"Collection already exists: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise RuntimeError(f"Failed to ensure collection: {e}") from e

    async def upsert(
        self,
        collection_name: str,
        id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Insert or update a vector in the collection.

        Args:
            collection_name: Name of the collection.
            id: Unique identifier for the vector.
            vector: The embedding vector.
            payload: Metadata to store with the vector (must include user_id).

        Raises:
            ValueError: If payload doesn't contain user_id.
            RuntimeError: If upsert operation fails.

        Example:
            >>> await store.upsert(
            ...     collection_name="conversations",
            ...     id="conv-123",
            ...     vector=[0.1, 0.2, ...],
            ...     payload={"text": "Hello", "user_id": "user-1", "timestamp": 123}
            ... )
        """
        if "user_id" not in payload:
            raise ValueError("Payload must contain 'user_id' for data isolation")

        await self.ensure_collection(collection_name)
        client = self._ensure_client()

        try:
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.debug(f"Upserted vector {id} to {collection_name}")

        except Exception as e:
            logger.error(f"Failed to upsert vector {id}: {e}")
            raise RuntimeError(f"Failed to upsert vector: {e}") from e

    async def upsert_batch(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Insert or update multiple vectors in batch.

        Args:
            collection_name: Name of the collection.
            ids: List of unique identifiers.
            vectors: List of embedding vectors.
            payloads: List of metadata dictionaries.

        Raises:
            ValueError: If lists have different lengths or payloads missing user_id.
            RuntimeError: If batch upsert fails.
        """
        if not (len(ids) == len(vectors) == len(payloads)):
            raise ValueError("ids, vectors, and payloads must have the same length")

        for i, payload in enumerate(payloads):
            if "user_id" not in payload:
                raise ValueError(f"Payload at index {i} must contain 'user_id'")

        await self.ensure_collection(collection_name)
        client = self._ensure_client()

        try:
            points = [
                models.PointStruct(id=id, vector=vector, payload=payload)
                for id, vector, payload in zip(ids, vectors, payloads)
            ]
            client.upsert(collection_name=collection_name, points=points)
            logger.debug(f"Batch upserted {len(ids)} vectors to {collection_name}")

        except Exception as e:
            logger.error(f"Failed to batch upsert: {e}")
            raise RuntimeError(f"Failed to batch upsert: {e}") from e

    async def search(
        self,
        collection_name: str,
        vector: list[float],
        user_id: str,
        limit: int | None = None,
        min_score: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar vectors with user filtering.

        Args:
            collection_name: Name of the collection to search.
            vector: Query embedding vector.
            user_id: User ID for data isolation (required).
            limit: Maximum number of results (default from settings).
            min_score: Minimum similarity score threshold (default from settings).
            filters: Additional filters to apply.

        Returns:
            List of SearchResult objects sorted by similarity (highest first).

        Example:
            >>> results = await store.search(
            ...     collection_name="conversations",
            ...     vector=[0.1, 0.2, ...],
            ...     user_id="user-1",
            ...     limit=5
            ... )
            >>> for r in results:
            ...     print(f"{r.payload['text']}: {r.score:.2f}")
        """
        limit = limit or settings.rag_top_k
        min_score = min_score or settings.rag_min_score

        client = self._ensure_client()

        # Build filter conditions
        must_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id),
            )
        ]

        # Add any additional filters
        if filters:
            for key, value in filters.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )

        try:
            results = client.search(
                collection_name=collection_name,
                query_vector=vector,
                query_filter=models.Filter(must=must_conditions),
                limit=limit,
                score_threshold=min_score,
            )

            return [
                SearchResult(
                    id=str(r.id),
                    score=r.score,
                    payload=r.payload or {},
                )
                for r in results
            ]

        except UnexpectedResponse as e:
            # Collection might not exist yet
            if "not found" in str(e).lower():
                logger.warning(f"Collection {collection_name} not found")
                return []
            raise

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search failed: {e}") from e

    async def delete(self, collection_name: str, ids: list[str]) -> None:
        """Delete vectors by their IDs.

        Args:
            collection_name: Name of the collection.
            ids: List of vector IDs to delete.

        Raises:
            RuntimeError: If deletion fails.
        """
        client = self._ensure_client()

        try:
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=ids),
            )
            logger.debug(f"Deleted {len(ids)} vectors from {collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise RuntimeError(f"Failed to delete vectors: {e}") from e

    async def delete_by_user(self, collection_name: str, user_id: str) -> None:
        """Delete all vectors for a user.

        Args:
            collection_name: Name of the collection.
            user_id: User ID whose vectors should be deleted.

        Raises:
            RuntimeError: If deletion fails.
        """
        client = self._ensure_client()

        try:
            client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user_id",
                                match=models.MatchValue(value=user_id),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted all vectors for user {user_id} from {collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete user vectors: {e}")
            raise RuntimeError(f"Failed to delete user vectors: {e}") from e

    async def get_by_id(self, collection_name: str, id: str) -> SearchResult | None:
        """Get a vector by its ID.

        Args:
            collection_name: Name of the collection.
            id: Vector ID to retrieve.

        Returns:
            SearchResult if found, None otherwise.
        """
        client = self._ensure_client()

        try:
            results = client.retrieve(
                collection_name=collection_name,
                ids=[id],
                with_payload=True,
                with_vectors=False,
            )

            if results:
                point = results[0]
                return SearchResult(
                    id=str(point.id),
                    score=1.0,  # No score for direct retrieval
                    payload=point.payload or {},
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get vector {id}: {e}")
            return None

    async def count(self, collection_name: str, user_id: str | None = None) -> int:
        """Count vectors in a collection, optionally filtered by user.

        Args:
            collection_name: Name of the collection.
            user_id: Optional user ID to filter by.

        Returns:
            Number of vectors matching the criteria.
        """
        client = self._ensure_client()

        try:
            if user_id:
                result = client.count(
                    collection_name=collection_name,
                    count_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user_id",
                                match=models.MatchValue(value=user_id),
                            )
                        ]
                    ),
                )
            else:
                result = client.count(collection_name=collection_name)

            return result.count

        except UnexpectedResponse:
            # Collection might not exist
            return 0
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            return 0

    async def hybrid_search(
        self,
        collection_name: str,
        vector: list[float],
        user_id: str,
        keywords: list[str] | None = None,
        text_field: str = "text",
        limit: int | None = None,
        min_score: float | None = None,
        boost_keyword_matches: float = 0.1,
    ) -> list[SearchResult]:
        """Hybrid search combining semantic similarity with keyword matching.

        Performs a semantic vector search and optionally boosts results
        that contain any of the specified keywords.

        Args:
            collection_name: Name of the collection to search.
            vector: Query embedding vector.
            user_id: User ID for data isolation.
            keywords: Optional list of keywords to boost matches for.
            text_field: Field name containing text to search for keywords.
            limit: Maximum number of results.
            min_score: Minimum similarity score threshold.
            boost_keyword_matches: Score boost for keyword matches (0-1).

        Returns:
            List of SearchResult objects sorted by combined score.

        Example:
            >>> results = await store.hybrid_search(
            ...     collection_name="conversations",
            ...     vector=[0.1, 0.2, ...],
            ...     user_id="user-1",
            ...     keywords=["netflix", "cancel"],
            ...     limit=10
            ... )
        """
        limit = limit or settings.rag_top_k
        min_score = min_score or settings.rag_min_score

        # First, perform semantic search with a larger limit for reranking
        fetch_limit = limit * 3 if keywords else limit
        semantic_results = await self.search(
            collection_name=collection_name,
            vector=vector,
            user_id=user_id,
            limit=fetch_limit,
            min_score=min_score * 0.8,  # Lower threshold for initial fetch
        )

        if not keywords or not semantic_results:
            return semantic_results[:limit]

        # Apply keyword boosting
        keywords_lower = [k.lower() for k in keywords]
        boosted_results = []

        for result in semantic_results:
            text = result.payload.get(text_field, "").lower()
            keyword_match_count = sum(1 for kw in keywords_lower if kw in text)

            # Calculate boost based on keyword matches
            if keyword_match_count > 0:
                boost = min(boost_keyword_matches * keyword_match_count, 0.3)
                boosted_score = min(result.score + boost, 1.0)
            else:
                boosted_score = result.score

            boosted_results.append(
                SearchResult(
                    id=result.id,
                    score=boosted_score,
                    payload={
                        **result.payload,
                        "_keyword_matches": keyword_match_count,
                        "_original_score": result.score,
                    },
                )
            )

        # Sort by boosted score and apply minimum threshold
        boosted_results.sort(key=lambda x: x.score, reverse=True)
        filtered_results = [r for r in boosted_results if r.score >= min_score]

        logger.debug(
            f"Hybrid search: {len(semantic_results)} semantic results, "
            f"{len(filtered_results)} after keyword boost and filter"
        )

        return filtered_results[:limit]

    async def keyword_filter_search(
        self,
        collection_name: str,
        user_id: str,
        text_contains: str,
        text_field: str = "text",
        limit: int = 100,
    ) -> list[SearchResult]:
        """Search by keyword/text containment without vector similarity.

        Uses Qdrant's payload filtering to find records containing specific text.
        Useful for exact keyword matching when semantic similarity isn't needed.

        Args:
            collection_name: Name of the collection to search.
            user_id: User ID for data isolation.
            text_contains: Text that must be contained in the field.
            text_field: Field name to search in.
            limit: Maximum number of results.

        Returns:
            List of SearchResult objects matching the keyword filter.

        Note:
            This is slower than vector search for large collections.
            For best performance, combine with vector search using hybrid_search.
        """
        client = self._ensure_client()

        try:
            # Use scroll to find all matching records
            records, _ = client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        ),
                        models.FieldCondition(
                            key=text_field,
                            match=models.MatchText(text=text_contains),
                        ),
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            return [
                SearchResult(
                    id=str(r.id),
                    score=1.0,  # No similarity score for keyword search
                    payload=r.payload or {},
                )
                for r in records
            ]

        except UnexpectedResponse as e:
            if "not found" in str(e).lower():
                logger.warning(f"Collection {collection_name} not found")
                return []
            raise

        except Exception as e:
            logger.error(f"Keyword filter search failed: {e}")
            return []

    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID for a vector.

        Returns:
            UUID string suitable for use as a vector ID.
        """
        return str(uuid.uuid4())

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance.

        Primarily useful for testing.
        """
        if cls._client:
            cls._client.close()
        cls._instance = None
        cls._client = None
        logger.info("VectorStore reset")


def get_vector_store() -> VectorStore:
    """Get the singleton VectorStore instance.

    This is the recommended way to access the vector store.

    Returns:
        The singleton VectorStore instance.

    Example:
        >>> store = get_vector_store()
        >>> await store.upsert(...)
    """
    return VectorStore()
