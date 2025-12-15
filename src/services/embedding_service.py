"""Embedding generation service for RAG.

This module provides text embedding capabilities using Sentence Transformers.
Embeddings are used for semantic search and context retrieval in the RAG system.

The service follows a singleton pattern with lazy model loading for efficiency.
Supports Redis caching via CacheService for improved performance.
"""

import hashlib
import logging
import time
from typing import TYPE_CHECKING, Any, ClassVar

from src.core.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate text embeddings for semantic search.

    Uses Sentence Transformers with the all-MiniLM-L6-v2 model for fast,
    high-quality embeddings. Supports optional Redis caching for performance.

    This is a singleton service with lazy model loading - the model is only
    loaded on first embedding request, not during initialization.

    Attributes:
        model_name: Name of the model being used.
        embedding_dim: Dimensionality of embeddings (384 for MiniLM).
        cache: Optional Redis client for caching embeddings.

    Example:
        >>> service = get_embedding_service()
        >>> embedding = await service.embed("Add Netflix for £15.99 monthly")
        >>> len(embedding)
        384
    """

    _instance: ClassVar["EmbeddingService | None"] = None
    _model: ClassVar[Any] = None

    def __new__(cls, cache: Any | None = None) -> "EmbeddingService":
        """Create or return the singleton instance.

        Args:
            cache: Optional Redis client for caching embeddings.

        Returns:
            The singleton EmbeddingService instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cache: Any | None = None) -> None:
        """Initialize embedding service.

        The model is loaded lazily on first use, not during initialization.

        Args:
            cache: Optional Redis client for caching embeddings.

        Model Info:
            - all-MiniLM-L6-v2: Fast (50ms), small (80MB), 384 dimensions
            - Alternative: all-mpnet-base-v2 (better quality, slower, 768 dims)
        """
        if getattr(self, "_initialized", False):
            # Allow updating cache even if already initialized
            if cache is not None and self.cache is None:
                self.cache = cache
                logger.info("EmbeddingService: Cache service injected")
            return

        self.model_name = settings.embedding_model
        self.embedding_dim = settings.embedding_dimension
        self.cache = cache
        self._initialized = True
        logger.info(f"EmbeddingService initialized with model: {self.model_name}")

    def set_cache(self, cache: Any) -> None:
        """Set the cache service for embedding caching.

        This allows injecting the cache service after initialization,
        which is needed since the cache service requires async initialization.

        Args:
            cache: The cache service instance (CacheService).

        Example:
            >>> service = get_embedding_service()
            >>> cache = await get_cache_service()
            >>> service.set_cache(cache)
        """
        self.cache = cache
        logger.info("EmbeddingService: Cache service configured")

    def _ensure_model_loaded(self) -> None:
        """Lazily load the model if not already loaded.

        This method is called internally before any embedding operation.
        The model is loaded only once and cached for subsequent calls.

        Raises:
            ImportError: If sentence-transformers is not installed.
            RuntimeError: If model loading fails.
        """
        if EmbeddingService._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self.model_name}")
                EmbeddingService._model = SentenceTransformer(self.model_name)
                actual_dim = EmbeddingService._model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded successfully. Dimension: {actual_dim}")
            except ImportError as e:
                logger.error("sentence-transformers not installed")
                raise ImportError(
                    "sentence-transformers is required. Install: pip install sentence-transformers"
                ) from e
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Failed to load embedding model: {e}") from e

    async def embed(self, text: str, use_cache: bool = True) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed.
            use_cache: Whether to use cache (default: True).

        Returns:
            Embedding vector as list of floats.

        Raises:
            ValueError: If text is empty.
            RuntimeError: If embedding generation fails.

        Example:
            >>> service = get_embedding_service()
            >>> embedding = await service.embed("Add Netflix subscription")
            >>> len(embedding)
            384

        Performance:
            - Typical latency: 30-50ms without cache
            - With cache: < 5ms
            - Cache key: MD5 hash of text
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        start_time = time.perf_counter()

        # Check cache first
        if use_cache and self.cache:
            cache_key = self._get_cache_key(text)
            cached = await self._get_from_cache(cache_key)
            if cached:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Cache hit for text: {text[:50]}... ({elapsed:.1f}ms)")
                return cached

        # Ensure model is loaded (lazy loading)
        self._ensure_model_loaded()

        # Generate embedding
        gen_start = time.perf_counter()
        embedding = EmbeddingService._model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        ).tolist()
        gen_elapsed = (time.perf_counter() - gen_start) * 1000

        # Store in cache
        if use_cache and self.cache:
            await self._store_in_cache(cache_key, embedding)

        total_elapsed = (time.perf_counter() - start_time) * 1000
        logger.debug(
            f"Generated embedding for: {text[:50]}... "
            f"(gen: {gen_elapsed:.1f}ms, total: {total_elapsed:.1f}ms)"
        )

        return embedding

    async def embed_batch(
        self, texts: list[str], use_cache: bool = True, batch_size: int = 32
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of input texts.
            use_cache: Whether to use cache (default: True).
            batch_size: Number of texts to process at once (default: 32).

        Returns:
            List of embedding vectors.

        Example:
            >>> service = get_embedding_service()
            >>> texts = ["Add Netflix", "Cancel Spotify", "Show subscriptions"]
            >>> embeddings = await service.embed_batch(texts)
            >>> len(embeddings)
            3
            >>> len(embeddings[0])
            384

        Performance:
            - Batching is 5-10x faster than individual calls
            - Typical: 150ms for 32 texts vs 1500ms individual
        """
        if not texts:
            return []

        start_time = time.perf_counter()

        # Check cache for all texts
        embeddings: list[list[float] | None] = []
        texts_to_generate: list[str] = []
        indices_to_generate: list[int] = []
        cache_hits = 0

        if use_cache and self.cache:
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                cached = await self._get_from_cache(cache_key)
                if cached:
                    embeddings.append(cached)
                    cache_hits += 1
                else:
                    texts_to_generate.append(text)
                    indices_to_generate.append(i)
                    embeddings.append(None)  # Placeholder
        else:
            texts_to_generate = texts
            indices_to_generate = list(range(len(texts)))
            embeddings = [None] * len(texts)

        # Generate embeddings for non-cached texts
        gen_elapsed = 0.0
        if texts_to_generate:
            # Ensure model is loaded (lazy loading)
            self._ensure_model_loaded()

            gen_start = time.perf_counter()
            generated = EmbeddingService._model.encode(
                texts_to_generate,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=batch_size,
                show_progress_bar=False,
            ).tolist()
            gen_elapsed = (time.perf_counter() - gen_start) * 1000

            # Store generated embeddings
            for i, (text, embedding) in enumerate(zip(texts_to_generate, generated)):
                idx = indices_to_generate[i]
                embeddings[idx] = embedding

                # Cache the embedding
                if use_cache and self.cache:
                    cache_key = self._get_cache_key(text)
                    await self._store_in_cache(cache_key, embedding)

        total_elapsed = (time.perf_counter() - start_time) * 1000
        cache_rate = (cache_hits / len(texts) * 100) if texts else 0
        logger.debug(
            f"Batch embed: {len(texts)} texts, {cache_hits} cached ({cache_rate:.0f}%), "
            f"{len(texts_to_generate)} generated (gen: {gen_elapsed:.1f}ms, total: {total_elapsed:.1f}ms)"
        )

        return embeddings  # type: ignore[return-value]

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key from text.

        Args:
            text: Input text

        Returns:
            Cache key as MD5 hash

        Cache Key Format:
            emb:{model_name}:{md5_hash}
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"emb:{self.model_name}:{text_hash}"

    async def _get_from_cache(self, key: str) -> list[float] | None:
        """Retrieve embedding from cache.

        Works with CacheService which handles JSON serialization.

        Args:
            key: Cache key.

        Returns:
            Cached embedding or None if not found.
        """
        if not self.cache:
            return None

        try:
            # CacheService.get() returns deserialized data
            cached = await self.cache.get(key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _store_in_cache(self, key: str, embedding: list[float]) -> None:
        """Store embedding in cache.

        Works with CacheService which handles JSON serialization.

        Args:
            key: Cache key.
            embedding: Embedding vector.

        Cache TTL: Uses settings.rag_cache_ttl (default 1 hour).
        """
        if not self.cache:
            return

        try:
            # CacheService.set() handles JSON serialization
            await self.cache.set(key, embedding, ttl=settings.rag_cache_ttl)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the embedding model.

        Returns:
            Dictionary with model information including model name,
            embedding dimension, max sequence length, and device.

        Example:
            >>> service = get_embedding_service()
            >>> info = service.get_model_info()
            >>> info['model_name']
            'all-MiniLM-L6-v2'
            >>> info['embedding_dim']
            384
        """
        self._ensure_model_loaded()
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "max_seq_length": EmbeddingService._model.max_seq_length,
            "device": str(EmbeddingService._model.device),
        }

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance.

        This is primarily useful for testing to ensure a fresh instance.
        Should not be called in production code.
        """
        cls._instance = None
        cls._model = None
        logger.info("EmbeddingService reset")


def get_embedding_service(cache: Any | None = None) -> EmbeddingService:
    """Get the singleton EmbeddingService instance.

    This is the recommended way to access the embedding service.

    Args:
        cache: Optional Redis client for caching embeddings.

    Returns:
        The singleton EmbeddingService instance.

    Example:
        >>> service = get_embedding_service()
        >>> embedding = await service.embed("Hello")
    """
    return EmbeddingService(cache=cache)
