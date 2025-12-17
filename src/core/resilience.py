"""Resilience patterns for external service calls.

This module provides retry logic, circuit breaker patterns, and timeout handling
for external services like Claude API, Redis, and Qdrant.

Patterns implemented:
- Retry with exponential backoff (tenacity)
- Circuit breaker state management
- Configurable timeouts
- Fallback handlers

Usage:
    from src.core.resilience import (
        retry_with_backoff,
        circuit_breaker,
        with_timeout,
        resilient_call,
    )

    @retry_with_backoff(max_attempts=3)
    async def call_external_service():
        ...

    @circuit_breaker("claude_api")
    async def call_claude():
        ...

    result = await with_timeout(call_external_service(), timeout=5.0)
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class ResilienceConfig:
    """Configuration for resilience patterns.

    Attributes:
        retry_max_attempts: Maximum retry attempts before giving up.
        retry_min_wait: Minimum wait time between retries (seconds).
        retry_max_wait: Maximum wait time between retries (seconds).
        circuit_failure_threshold: Number of failures before opening circuit.
        circuit_recovery_timeout: Time to wait before attempting recovery (seconds).
        circuit_half_open_max_calls: Max calls allowed in half-open state.
        default_timeout: Default timeout for external calls (seconds).
    """

    retry_max_attempts: int = 3
    retry_min_wait: float = 0.5
    retry_max_wait: float = 10.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 30.0
    circuit_half_open_max_calls: int = 1
    default_timeout: float = 30.0


# Global configuration (can be overridden)
config = ResilienceConfig()


# =============================================================================
# Circuit Breaker Implementation
# =============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerState:
    """State for a circuit breaker.

    Attributes:
        state: Current circuit state.
        failure_count: Number of consecutive failures.
        last_failure_time: Timestamp of last failure.
        half_open_calls: Number of calls made in half-open state.
    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0


# Global circuit breaker registry
_circuits: dict[str, CircuitBreakerState] = {}


def get_circuit(name: str) -> CircuitBreakerState:
    """Get or create a circuit breaker state.

    Args:
        name: Unique identifier for the circuit.

    Returns:
        CircuitBreakerState instance.
    """
    if name not in _circuits:
        _circuits[name] = CircuitBreakerState()
    return _circuits[name]


def reset_circuit(name: str) -> None:
    """Reset a circuit breaker to closed state.

    Args:
        name: Unique identifier for the circuit.
    """
    if name in _circuits:
        _circuits[name] = CircuitBreakerState()
    logger.info(f"Circuit breaker '{name}' reset to CLOSED")


def get_all_circuits() -> dict[str, dict[str, Any]]:
    """Get status of all circuit breakers.

    Returns:
        Dictionary mapping circuit names to their status.
    """
    return {
        name: {
            "state": circuit.state.value,
            "failure_count": circuit.failure_count,
            "last_failure_time": circuit.last_failure_time,
        }
        for name, circuit in _circuits.items()
    }


class CircuitOpenError(ExternalServiceError):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, recovery_time: float):
        """Initialize CircuitOpenError.

        Args:
            circuit_name: Name of the open circuit.
            recovery_time: Seconds until recovery attempt.
        """
        super().__init__(
            f"Circuit '{circuit_name}' is open. Retry in {recovery_time:.1f}s",
            service_name=circuit_name,
        )
        self.circuit_name = circuit_name
        self.recovery_time = recovery_time


def _check_circuit(circuit: CircuitBreakerState, name: str) -> None:
    """Check if circuit allows the call.

    Args:
        circuit: Circuit breaker state.
        name: Circuit name for error messages.

    Raises:
        CircuitOpenError: If circuit is open.
    """
    if circuit.state == CircuitState.OPEN:
        time_since_failure = time.time() - circuit.last_failure_time
        if time_since_failure >= config.circuit_recovery_timeout:
            # Transition to half-open
            circuit.state = CircuitState.HALF_OPEN
            circuit.half_open_calls = 0
            logger.info(f"Circuit '{name}' transitioning to HALF_OPEN")
        else:
            recovery_time = config.circuit_recovery_timeout - time_since_failure
            raise CircuitOpenError(name, recovery_time)

    elif circuit.state == CircuitState.HALF_OPEN:
        if circuit.half_open_calls >= config.circuit_half_open_max_calls:
            # Too many half-open calls, stay open
            raise CircuitOpenError(name, config.circuit_recovery_timeout)
        circuit.half_open_calls += 1


def _record_success(circuit: CircuitBreakerState, name: str) -> None:
    """Record a successful call.

    Args:
        circuit: Circuit breaker state.
        name: Circuit name for logging.
    """
    if circuit.state == CircuitState.HALF_OPEN:
        # Success in half-open state, close circuit
        circuit.state = CircuitState.CLOSED
        circuit.failure_count = 0
        logger.info(f"Circuit '{name}' recovered, transitioning to CLOSED")
    elif circuit.state == CircuitState.CLOSED:
        # Reset failure count on success
        circuit.failure_count = 0


def _record_failure(circuit: CircuitBreakerState, name: str, error: Exception) -> None:
    """Record a failed call.

    Args:
        circuit: Circuit breaker state.
        name: Circuit name for logging.
        error: The exception that occurred.
    """
    circuit.failure_count += 1
    circuit.last_failure_time = time.time()

    if circuit.state == CircuitState.HALF_OPEN:
        # Failure in half-open state, open circuit again
        circuit.state = CircuitState.OPEN
        logger.warning(
            f"Circuit '{name}' failed in HALF_OPEN state, transitioning to OPEN",
            extra={"error": str(error)},
        )
    elif circuit.failure_count >= config.circuit_failure_threshold:
        # Too many failures, open circuit
        circuit.state = CircuitState.OPEN
        logger.warning(
            f"Circuit '{name}' opened after {circuit.failure_count} failures",
            extra={"error": str(error)},
        )


# =============================================================================
# Decorators
# =============================================================================


def retry_with_backoff(
    max_attempts: int | None = None,
    min_wait: float | None = None,
    max_wait: float | None = None,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for async functions with retry and exponential backoff.

    Args:
        max_attempts: Maximum retry attempts (default from config).
        min_wait: Minimum wait between retries (default from config).
        max_wait: Maximum wait between retries (default from config).
        retry_exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function with retry logic.

    Example:
        @retry_with_backoff(max_attempts=3)
        async def call_api():
            ...
    """
    attempts = max_attempts or config.retry_max_attempts
    min_w = min_wait or config.retry_min_wait
    max_w = max_wait or config.retry_max_wait

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None

            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(min=min_w, max=max_w),
                retry=retry_if_exception_type(retry_exceptions),
                reraise=True,
            ):
                with attempt:
                    try:
                        result = await func(*args, **kwargs)
                        if attempt.retry_state.attempt_number > 1:
                            logger.info(
                                f"{func.__name__} succeeded after "
                                f"{attempt.retry_state.attempt_number} attempts"
                            )
                        return result
                    except retry_exceptions as e:
                        last_exception = e
                        logger.warning(
                            f"{func.__name__} attempt "
                            f"{attempt.retry_state.attempt_number}/{attempts} failed: {e}"
                        )
                        raise

            # Should not reach here due to reraise=True
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error")

        return wrapper

    return decorator


def circuit_breaker(
    name: str,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for async functions with circuit breaker pattern.

    Args:
        name: Unique name for this circuit breaker.

    Returns:
        Decorated function with circuit breaker logic.

    Example:
        @circuit_breaker("claude_api")
        async def call_claude():
            ...
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            circuit = get_circuit(name)

            # Check if call is allowed
            _check_circuit(circuit, name)

            try:
                result = await func(*args, **kwargs)
                _record_success(circuit, name)
                return result
            except Exception as e:
                _record_failure(circuit, name, e)
                raise

        return wrapper

    return decorator


async def with_timeout(
    coro: Awaitable[T],
    timeout: float | None = None,
    timeout_message: str | None = None,
) -> T:
    """Execute a coroutine with timeout.

    Args:
        coro: The coroutine to execute.
        timeout: Timeout in seconds (default from config).
        timeout_message: Custom message for timeout error.

    Returns:
        Result of the coroutine.

    Raises:
        asyncio.TimeoutError: If timeout is exceeded.

    Example:
        result = await with_timeout(call_api(), timeout=5.0)
    """
    timeout_seconds = timeout or config.default_timeout
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except TimeoutError:
        msg = timeout_message or f"Operation timed out after {timeout_seconds}s"
        logger.error(msg)
        raise TimeoutError(msg)


def resilient(
    circuit_name: str | None = None,
    max_retries: int = 3,
    timeout: float | None = None,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Combined decorator for retry, circuit breaker, and timeout.

    This is the recommended decorator for external service calls as it
    combines all resilience patterns.

    Args:
        circuit_name: Optional circuit breaker name.
        max_retries: Maximum retry attempts.
        timeout: Timeout in seconds.
        retry_exceptions: Exception types to retry on.

    Returns:
        Decorated function with all resilience patterns.

    Example:
        @resilient(circuit_name="claude_api", max_retries=3, timeout=30)
        async def call_claude():
            ...
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Apply decorators in order: retry -> circuit_breaker
        wrapped = retry_with_backoff(
            max_attempts=max_retries,
            retry_exceptions=retry_exceptions,
        )(func)

        if circuit_name:
            wrapped = circuit_breaker(circuit_name)(wrapped)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await with_timeout(
                wrapped(*args, **kwargs),
                timeout=timeout,
            )

        return wrapper

    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


async def resilient_call(
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    circuit_name: str | None = None,
    max_retries: int = 3,
    timeout: float | None = None,
    fallback: T | None = None,
    **kwargs: P.kwargs,
) -> T:
    """Execute an async function with resilience patterns.

    This is an alternative to the decorator approach, useful for
    one-off calls or when you need dynamic configuration.

    Args:
        func: The async function to call.
        *args: Positional arguments for the function.
        circuit_name: Optional circuit breaker name.
        max_retries: Maximum retry attempts.
        timeout: Timeout in seconds.
        fallback: Value to return if all attempts fail.
        **kwargs: Keyword arguments for the function.

    Returns:
        Result of the function or fallback value.

    Example:
        result = await resilient_call(
            call_api,
            circuit_name="api",
            fallback="default_value",
        )
    """
    try:
        # Apply circuit breaker check
        if circuit_name:
            circuit = get_circuit(circuit_name)
            _check_circuit(circuit, circuit_name)

        # Execute with retry and timeout
        last_exception: Exception | None = None

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(min=config.retry_min_wait, max=config.retry_max_wait),
            reraise=True,
        ):
            with attempt:
                try:
                    result = await with_timeout(
                        func(*args, **kwargs),
                        timeout=timeout,
                    )
                    if circuit_name:
                        _record_success(get_circuit(circuit_name), circuit_name)
                    return result
                except Exception as e:
                    last_exception = e
                    if circuit_name:
                        _record_failure(get_circuit(circuit_name), circuit_name, e)
                    raise

        # Should not reach here
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic error")

    except Exception as e:
        if fallback is not None:
            logger.warning(f"Returning fallback value due to: {e}")
            return fallback
        raise
