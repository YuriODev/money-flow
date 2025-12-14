"""Prometheus metrics configuration.

This module provides Prometheus metrics collection with:
- HTTP request metrics (latency, count, size)
- Custom business metrics (subscriptions, payments, etc.)
- Database query metrics
- AI agent performance metrics

Usage:
    from src.core.metrics import setup_metrics

    # At application startup
    setup_metrics(app)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info

from src.core.config import settings
from src.core.logging import get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger(__name__)

# Custom business metrics

# Subscription operations
subscription_operations = Counter(
    "money_flow_subscription_operations_total",
    "Total subscription operations",
    ["operation", "payment_type"],
)

# Agent requests
agent_requests = Counter(
    "money_flow_agent_requests_total",
    "Total AI agent requests",
    ["intent", "success"],
)

agent_latency = Histogram(
    "money_flow_agent_latency_seconds",
    "AI agent request latency",
    ["intent"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Database operations
db_query_latency = Histogram(
    "money_flow_db_query_seconds",
    "Database query latency",
    ["operation"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# RAG operations
rag_operations = Counter(
    "money_flow_rag_operations_total",
    "Total RAG operations",
    ["operation", "success"],
)

rag_latency = Histogram(
    "money_flow_rag_latency_seconds",
    "RAG operation latency",
    ["operation"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

# Cache operations
cache_operations = Counter(
    "money_flow_cache_operations_total",
    "Total cache operations",
    ["operation", "hit"],
)


def _requests_by_endpoint() -> Callable[[Info], None]:
    """Create a metric for requests by endpoint.

    Returns:
        Instrumentation callback function.
    """
    requests_total = Counter(
        "money_flow_http_requests_by_endpoint_total",
        "Total HTTP requests by endpoint",
        ["method", "endpoint", "status"],
    )

    def instrumentation(info: Info) -> None:
        if info.modified_handler:
            endpoint = info.modified_handler
        else:
            endpoint = info.request.url.path

        requests_total.labels(
            method=info.request.method,
            endpoint=endpoint,
            status=info.response.status_code if info.response else "error",
        ).inc()

    return instrumentation


def _response_size() -> Callable[[Info], None]:
    """Create a metric for response sizes.

    Returns:
        Instrumentation callback function.
    """
    response_size = Histogram(
        "money_flow_http_response_size_bytes",
        "HTTP response size in bytes",
        ["method", "endpoint"],
        buckets=[100, 500, 1000, 5000, 10000, 50000, 100000],
    )

    def instrumentation(info: Info) -> None:
        if info.response:
            content_length = info.response.headers.get("content-length")
            if content_length:
                endpoint = info.modified_handler if info.modified_handler else info.request.url.path
                response_size.labels(
                    method=info.request.method,
                    endpoint=endpoint,
                ).observe(int(content_length))

    return instrumentation


def setup_metrics(app: FastAPI) -> Instrumentator:
    """Set up Prometheus metrics for the FastAPI application.

    This function should be called once during application startup.
    It configures:
    - Standard HTTP metrics (request count, latency, in-progress)
    - Custom endpoint-specific metrics
    - Response size tracking

    Args:
        app: The FastAPI application instance.

    Returns:
        The configured Instrumentator instance.

    Example:
        >>> app = FastAPI()
        >>> setup_metrics(app)
        >>> # Metrics now available at /metrics
    """
    if not settings.metrics_enabled:
        logger.info("Prometheus metrics disabled")
        return Instrumentator()

    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[
            "/health",
            "/health/live",
            "/health/ready",
            settings.metrics_endpoint,
        ],
        env_var_name="ENABLE_METRICS",
        inprogress_name="money_flow_http_requests_inprogress",
        inprogress_labels=True,
    )

    # Add standard metrics
    instrumentator.add(
        _requests_by_endpoint(),
    ).add(
        _response_size(),
    )

    # Instrument the app and expose metrics endpoint
    instrumentator.instrument(app).expose(
        app,
        endpoint=settings.metrics_endpoint,
        include_in_schema=True,
        tags=["monitoring"],
    )

    logger.info(
        "Prometheus metrics enabled",
        endpoint=settings.metrics_endpoint,
    )

    return instrumentator


# Convenience functions for recording metrics


def record_subscription_operation(operation: str, payment_type: str) -> None:
    """Record a subscription operation.

    Args:
        operation: The operation type (create, update, delete).
        payment_type: The payment type (subscription, debt, savings, etc.).

    Example:
        >>> record_subscription_operation("create", "subscription")
    """
    subscription_operations.labels(
        operation=operation,
        payment_type=payment_type,
    ).inc()


def record_agent_request(intent: str, success: bool, latency: float) -> None:
    """Record an AI agent request.

    Args:
        intent: The detected intent (add_subscription, query_spending, etc.).
        success: Whether the request was successful.
        latency: Request latency in seconds.

    Example:
        >>> record_agent_request("add_subscription", True, 0.5)
    """
    agent_requests.labels(
        intent=intent,
        success=str(success).lower(),
    ).inc()
    agent_latency.labels(intent=intent).observe(latency)


def record_db_query(operation: str, latency: float) -> None:
    """Record a database query.

    Args:
        operation: The query operation (select, insert, update, delete).
        latency: Query latency in seconds.

    Example:
        >>> record_db_query("select", 0.05)
    """
    db_query_latency.labels(operation=operation).observe(latency)


def record_rag_operation(operation: str, success: bool, latency: float) -> None:
    """Record a RAG operation.

    Args:
        operation: The RAG operation (embed, search, retrieve).
        success: Whether the operation was successful.
        latency: Operation latency in seconds.

    Example:
        >>> record_rag_operation("search", True, 0.1)
    """
    rag_operations.labels(
        operation=operation,
        success=str(success).lower(),
    ).inc()
    rag_latency.labels(operation=operation).observe(latency)


def record_cache_operation(operation: str, hit: bool) -> None:
    """Record a cache operation.

    Args:
        operation: The cache operation (get, set, delete).
        hit: Whether it was a cache hit (for get operations).

    Example:
        >>> record_cache_operation("get", True)  # Cache hit
        >>> record_cache_operation("get", False)  # Cache miss
    """
    cache_operations.labels(
        operation=operation,
        hit=str(hit).lower(),
    ).inc()


__all__ = [
    "record_agent_request",
    "record_cache_operation",
    "record_db_query",
    "record_rag_operation",
    "record_subscription_operation",
    "setup_metrics",
]
