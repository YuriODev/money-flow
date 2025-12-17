"""Background task queue using ARQ (Async Redis Queue).

This module provides a background task queue for executing long-running
or scheduled tasks asynchronously. It uses Redis as the message broker.

Features:
- Async task execution with retry support
- Scheduled/cron tasks
- Task status tracking
- Health monitoring
- Task result storage

Usage:
    # Define a task
    async def send_notification(ctx, user_id: str, message: str):
        # Task logic here
        pass

    # Enqueue a task
    from src.core.tasks import enqueue_task
    await enqueue_task("send_notification", user_id="123", message="Hello")

    # Run the worker (in a separate process)
    arq src.core.tasks.WorkerSettings
"""

import logging
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from arq.jobs import Job
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


def get_redis_settings() -> RedisSettings:
    """Get Redis settings for ARQ from application config.

    Returns:
        RedisSettings configured from environment.
    """
    # Parse redis URL (e.g., redis://localhost:6379/0)
    url = settings.redis_url
    if url.startswith("redis://"):
        url = url[8:]

    parts = url.split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0

    if ":" in host_port:
        host, port_str = host_port.split(":")
        port = int(port_str)
    else:
        host = host_port
        port = 6379

    return RedisSettings(
        host=host,
        port=port,
        database=database,
    )


# =============================================================================
# Task Registry
# =============================================================================

# Registry of available tasks
_task_registry: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}


def task(
    name: str | None = None,
    max_tries: int = 3,
    timeout: int = 300,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """Decorator to register a function as a background task.

    Args:
        name: Optional custom name for the task. Defaults to function name.
        max_tries: Maximum number of retry attempts.
        timeout: Task timeout in seconds.

    Returns:
        Decorated function registered as a task.

    Example:
        @task(name="send_email", max_tries=3)
        async def send_email_task(ctx, to: str, subject: str, body: str):
            # Send email logic
            pass
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        task_name = name or func.__name__

        # Store metadata on the function
        func._task_name = task_name  # type: ignore[attr-defined]
        func._max_tries = max_tries  # type: ignore[attr-defined]
        func._timeout = timeout  # type: ignore[attr-defined]

        # Register the task
        _task_registry[task_name] = func
        logger.debug(f"Registered task: {task_name}")

        return func

    return decorator


def get_registered_tasks() -> list[str]:
    """Get list of registered task names.

    Returns:
        List of task names.
    """
    return list(_task_registry.keys())


# =============================================================================
# Task Pool Management
# =============================================================================

# Global connection pool
_pool: ArqRedis | None = None


async def get_task_pool() -> ArqRedis:
    """Get or create the ARQ connection pool.

    Returns:
        ArqRedis connection pool.

    Raises:
        RuntimeError: If Redis is not available.
    """
    global _pool

    if _pool is None:
        try:
            _pool = await create_pool(get_redis_settings())
            logger.info("ARQ task pool created")
        except Exception as e:
            logger.error(f"Failed to create ARQ pool: {e}")
            raise RuntimeError(f"Failed to connect to Redis for task queue: {e}") from e

    return _pool


async def close_task_pool() -> None:
    """Close the ARQ connection pool.

    Should be called during application shutdown.
    """
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("ARQ task pool closed")


# =============================================================================
# Task Enqueuing
# =============================================================================


class TaskInfo(BaseModel):
    """Information about an enqueued task."""

    job_id: str
    task_name: str
    status: str
    enqueued_at: datetime
    scheduled_for: datetime | None = None


async def enqueue_task(
    task_name: str,
    *args: Any,
    _defer_by: timedelta | None = None,
    _defer_until: datetime | None = None,
    _job_id: str | None = None,
    **kwargs: Any,
) -> TaskInfo:
    """Enqueue a task for background execution.

    Args:
        task_name: Name of the registered task.
        *args: Positional arguments for the task.
        _defer_by: Delay execution by this timedelta.
        _defer_until: Execute at this specific time.
        _job_id: Custom job ID (for idempotency).
        **kwargs: Keyword arguments for the task.

    Returns:
        TaskInfo with job details.

    Raises:
        ValueError: If task is not registered.
        RuntimeError: If Redis is not available.

    Example:
        # Execute immediately
        await enqueue_task("send_email", to="user@example.com", subject="Hello")

        # Execute in 5 minutes
        await enqueue_task("send_email", to="user@example.com", _defer_by=timedelta(minutes=5))
    """
    if task_name not in _task_registry:
        raise ValueError(f"Task '{task_name}' is not registered")

    pool = await get_task_pool()

    job = await pool.enqueue_job(
        task_name,
        *args,
        _defer_by=_defer_by,
        _defer_until=_defer_until,
        _job_id=_job_id,
        **kwargs,
    )

    if job is None:
        # Job already exists with this ID
        raise ValueError("Job with ID already exists")

    return TaskInfo(
        job_id=job.job_id,
        task_name=task_name,
        status="queued",
        enqueued_at=datetime.utcnow(),
        scheduled_for=_defer_until,
    )


async def get_task_status(job_id: str) -> dict[str, Any]:
    """Get the status of a task by job ID.

    Args:
        job_id: The job ID returned when enqueuing.

    Returns:
        Dictionary with job status and result.
    """
    pool = await get_task_pool()
    job = Job(job_id, pool)

    status = await job.status()
    info = await job.info()

    result: dict[str, Any] = {
        "job_id": job_id,
        "status": status.value if status else "unknown",
    }

    if info:
        result.update(
            {
                "function": info.function,
                "enqueue_time": info.enqueue_time,
                "start_time": info.start_time,
                "finish_time": info.finish_time,
                "success": info.success,
                "result": info.result if info.success else None,
                "error": str(info.result) if info.success is False else None,
            }
        )

    return result


async def get_queue_info() -> dict[str, Any]:
    """Get information about the task queue.

    Returns:
        Dictionary with queue statistics.
    """
    pool = await get_task_pool()

    # Get queue length
    queued = await pool.queued_jobs()
    results = await pool.all_job_results()

    return {
        "queued_jobs": len(queued) if queued else 0,
        "completed_jobs": len(results) if results else 0,
        "registered_tasks": get_registered_tasks(),
    }


# =============================================================================
# Built-in Tasks
# =============================================================================


@task(name="health_check_task", max_tries=1, timeout=30)
async def health_check_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Simple health check task for testing the queue.

    Args:
        ctx: ARQ context dictionary.

    Returns:
        Dictionary with timestamp and status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": ctx.get("job_id", "unknown"),
    }


@task(name="cleanup_expired_sessions", max_tries=3, timeout=300)
async def cleanup_expired_sessions(ctx: dict[str, Any]) -> dict[str, int]:
    """Clean up expired user sessions.

    This task should be scheduled to run periodically.

    Args:
        ctx: ARQ context dictionary.

    Returns:
        Dictionary with count of cleaned sessions.
    """
    # TODO: Implement actual session cleanup
    logger.info("Running cleanup_expired_sessions task")
    return {"cleaned_sessions": 0}


@task(name="send_payment_reminders", max_tries=3, timeout=600)
async def send_payment_reminders(ctx: dict[str, Any], days_ahead: int = 3) -> dict[str, int]:
    """Send reminders for upcoming payments.

    Args:
        ctx: ARQ context dictionary.
        days_ahead: Number of days to look ahead.

    Returns:
        Dictionary with count of reminders sent.
    """
    # TODO: Implement actual reminder logic
    logger.info(f"Running send_payment_reminders task for {days_ahead} days ahead")
    return {"reminders_sent": 0}


# =============================================================================
# Worker Settings
# =============================================================================


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook.

    Called when the worker starts. Use for initializing connections.

    Args:
        ctx: ARQ context dictionary.
    """
    logger.info("ARQ worker starting up")
    # Initialize any connections needed by tasks
    ctx["startup_time"] = datetime.utcnow()


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook.

    Called when the worker shuts down. Use for cleanup.

    Args:
        ctx: ARQ context dictionary.
    """
    logger.info("ARQ worker shutting down")
    # Clean up any connections


class WorkerSettings:
    """ARQ worker configuration.

    This class is used by the ARQ worker process.

    Run the worker with:
        arq src.core.tasks.WorkerSettings
    """

    # Redis connection settings
    redis_settings = get_redis_settings()

    # Functions available to the worker
    functions = list(_task_registry.values())

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10  # Max concurrent jobs
    job_timeout = 300  # Default timeout in seconds
    keep_result = 3600  # Keep results for 1 hour
    poll_delay = 0.5  # Poll interval in seconds

    # Health check interval
    health_check_interval = 60

    # Cron jobs (scheduled tasks)
    cron_jobs = [
        # Example: Run cleanup every day at 3 AM
        # cron(cleanup_expired_sessions, hour=3, minute=0),
        # Example: Send payment reminders daily at 9 AM
        # cron(send_payment_reminders, hour=9, minute=0),
    ]
