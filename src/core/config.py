"""Application configuration using Pydantic Settings.

This module provides centralized configuration management for the application.
All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration values can be overridden via environment variables.
    The settings are cached using lru_cache for performance.

    Attributes:
        database_url: PostgreSQL connection URL for async operations.
        api_host: Host address for the FastAPI server.
        api_port: Port number for the FastAPI server.
        debug: Enable debug mode with detailed error messages.
        cors_origins: List of allowed CORS origins.
        anthropic_api_key: API key for Claude AI features.
        exchange_rate_api_key: API key for Open Exchange Rates API.
        default_currency: Default currency for the application.
        supported_currencies: List of supported currency codes.
        cache_ttl_exchange_rates: TTL for exchange rate cache in seconds.
        redis_url: Redis connection URL for caching.
        rag_enabled: Enable RAG (Retrieval-Augmented Generation) features.
        qdrant_host: Qdrant vector database host.
        qdrant_port: Qdrant HTTP API port.
        qdrant_grpc_port: Qdrant gRPC API port for faster operations.
        embedding_model: Sentence Transformers model for embeddings.
        embedding_dimension: Vector dimension for the embedding model.
        rag_top_k: Number of results to retrieve from vector search.
        rag_min_score: Minimum similarity score threshold for results.
        rag_context_window: Number of recent conversation turns to include.
        rag_cache_ttl: TTL for embedding cache in seconds.
        jwt_secret_key: Secret key for signing JWT tokens.
        jwt_algorithm: Algorithm for JWT encoding (default: HS256).
        jwt_access_token_expire_minutes: Access token expiration time in minutes.
        jwt_refresh_token_expire_days: Refresh token expiration time in days.
        gcp_project_id: Google Cloud Platform project ID.
        gcp_region: GCP region for deployment.

    Example:
        >>> from src.core.config import settings
        >>> print(settings.default_currency)
        'GBP'
        >>> print(settings.rag_enabled)
        True
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./subscriptions.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # CORS - Security hardened configuration
    # In production, set specific origins (no wildcards)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    # Production-only settings (override in .env for production)
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ]
    cors_max_age: int = 600  # 10 minutes preflight cache

    # Claude API for agentic features
    anthropic_api_key: str = ""

    # Currency Configuration
    exchange_rate_api_key: str = ""  # Open Exchange Rates API key
    default_currency: str = "GBP"
    supported_currencies: list[str] = ["GBP", "EUR", "USD", "UAH"]
    cache_ttl_exchange_rates: int = 3600  # 1 hour cache for exchange rates

    # Redis (for caching)
    redis_url: str = "redis://localhost:6379/0"

    # RAG Configuration
    rag_enabled: bool = True
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    rag_top_k: int = 5
    rag_min_score: float = 0.5
    rag_context_window: int = 5
    rag_cache_ttl: int = 3600  # 1 hour cache for embeddings

    # JWT Authentication
    jwt_secret_key: str = "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION"  # Override in .env
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 30 minutes
    jwt_refresh_token_expire_days: int = 7  # 7 days

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"  # Default rate limit
    rate_limit_get: str = "100/minute"  # GET endpoints
    rate_limit_write: str = "20/minute"  # POST/PUT/DELETE endpoints
    rate_limit_agent: str = "10/minute"  # AI agent endpoint (expensive)
    rate_limit_auth: str = "5/minute"  # Auth endpoints (prevent brute force)

    # GCP
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    # Sentry Error Tracking
    sentry_dsn: str = ""  # Set via SENTRY_DSN env var
    sentry_environment: str = "development"  # development, staging, production
    sentry_traces_sample_rate: float = 0.1  # 10% of requests traced
    sentry_profiles_sample_rate: float = 0.1  # 10% of transactions profiled

    # Prometheus Metrics
    metrics_enabled: bool = True  # Enable/disable Prometheus metrics
    metrics_endpoint: str = "/metrics"  # Metrics endpoint path


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached application settings loaded from environment.

    Example:
        >>> settings = get_settings()
        >>> settings.debug
        True
    """
    return Settings()


settings = get_settings()
