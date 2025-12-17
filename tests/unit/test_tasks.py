"""Tests for the background task queue module.

Tests task registration, configuration, and basic functionality.
Note: Full integration tests require a running Redis instance.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.tasks import (
    TaskInfo,
    WorkerSettings,
    get_redis_settings,
    get_registered_tasks,
    task,
)


class TestTaskDecorator:
    """Tests for the @task decorator."""

    def test_task_registration(self):
        """Test that @task decorator registers functions."""
        # Get initial count
        initial_tasks = len(get_registered_tasks())

        @task(name="test_task_1")
        async def my_test_task(ctx):
            return "done"

        # Should have one more task registered
        assert len(get_registered_tasks()) == initial_tasks + 1
        assert "test_task_1" in get_registered_tasks()

    def test_task_default_name(self):
        """Test that task uses function name by default."""

        @task()
        async def another_test_task(ctx):
            return "done"

        assert "another_test_task" in get_registered_tasks()

    def test_task_stores_metadata(self):
        """Test that task stores configuration metadata."""

        @task(name="metadata_test", max_tries=5, timeout=120)
        async def task_with_metadata(ctx):
            return "done"

        assert task_with_metadata._task_name == "metadata_test"
        assert task_with_metadata._max_tries == 5
        assert task_with_metadata._timeout == 120


class TestRedisSettings:
    """Tests for Redis configuration."""

    def test_get_redis_settings_default(self):
        """Test parsing default Redis URL."""
        with patch("src.core.tasks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379/0"

            settings = get_redis_settings()

            assert settings.host == "localhost"
            assert settings.port == 6379
            assert settings.database == 0

    def test_get_redis_settings_custom_port(self):
        """Test parsing Redis URL with custom port."""
        with patch("src.core.tasks.settings") as mock_settings:
            mock_settings.redis_url = "redis://redis-server:6380/2"

            settings = get_redis_settings()

            assert settings.host == "redis-server"
            assert settings.port == 6380
            assert settings.database == 2

    def test_get_redis_settings_no_database(self):
        """Test parsing Redis URL without database number."""
        with patch("src.core.tasks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"

            settings = get_redis_settings()

            assert settings.host == "localhost"
            assert settings.port == 6379
            assert settings.database == 0


class TestTaskInfo:
    """Tests for TaskInfo model."""

    def test_task_info_creation(self):
        """Test creating TaskInfo instance."""
        from datetime import datetime

        info = TaskInfo(
            job_id="job-123",
            task_name="my_task",
            status="queued",
            enqueued_at=datetime.utcnow(),
        )

        assert info.job_id == "job-123"
        assert info.task_name == "my_task"
        assert info.status == "queued"
        assert info.scheduled_for is None

    def test_task_info_with_schedule(self):
        """Test TaskInfo with scheduled execution."""
        from datetime import datetime

        scheduled = datetime(2025, 1, 1, 12, 0, 0)
        info = TaskInfo(
            job_id="job-456",
            task_name="scheduled_task",
            status="queued",
            enqueued_at=datetime.utcnow(),
            scheduled_for=scheduled,
        )

        assert info.scheduled_for == scheduled


class TestWorkerSettings:
    """Tests for WorkerSettings configuration."""

    def test_worker_settings_exists(self):
        """Test that WorkerSettings class is properly configured."""
        assert hasattr(WorkerSettings, "redis_settings")
        assert hasattr(WorkerSettings, "functions")
        assert hasattr(WorkerSettings, "on_startup")
        assert hasattr(WorkerSettings, "on_shutdown")

    def test_worker_settings_defaults(self):
        """Test default worker configuration values."""
        assert WorkerSettings.max_jobs == 10
        assert WorkerSettings.job_timeout == 300
        assert WorkerSettings.keep_result == 3600
        assert WorkerSettings.poll_delay == 0.5


class TestBuiltInTasks:
    """Tests for built-in tasks."""

    def test_health_check_task_registered(self):
        """Test that health_check_task is registered."""
        assert "health_check_task" in get_registered_tasks()

    def test_cleanup_task_registered(self):
        """Test that cleanup_expired_sessions is registered."""
        assert "cleanup_expired_sessions" in get_registered_tasks()

    def test_payment_reminders_task_registered(self):
        """Test that send_payment_reminders is registered."""
        assert "send_payment_reminders" in get_registered_tasks()


class TestEnqueueTask:
    """Tests for task enqueuing (mocked)."""

    @pytest.mark.asyncio
    async def test_enqueue_unregistered_task_raises(self):
        """Test that enqueuing unregistered task raises ValueError."""
        from src.core.tasks import enqueue_task

        with pytest.raises(ValueError, match="not registered"):
            await enqueue_task("nonexistent_task")

    @pytest.mark.asyncio
    async def test_enqueue_task_success(self):
        """Test successful task enqueuing (mocked)."""
        from src.core.tasks import enqueue_task

        # Create a mock pool
        mock_job = MagicMock()
        mock_job.job_id = "test-job-123"

        mock_pool = AsyncMock()
        mock_pool.enqueue_job.return_value = mock_job

        with patch("src.core.tasks.get_task_pool", return_value=mock_pool):
            # Use a registered task
            result = await enqueue_task("health_check_task")

            assert result.job_id == "test-job-123"
            assert result.task_name == "health_check_task"
            assert result.status == "queued"


class TestGetQueueInfo:
    """Tests for queue info retrieval (mocked)."""

    @pytest.mark.asyncio
    async def test_get_queue_info(self):
        """Test getting queue information."""
        from src.core.tasks import get_queue_info

        mock_pool = AsyncMock()
        mock_pool.queued_jobs.return_value = ["job1", "job2"]
        mock_pool.all_job_results.return_value = ["result1"]

        with patch("src.core.tasks.get_task_pool", return_value=mock_pool):
            info = await get_queue_info()

            assert info["queued_jobs"] == 2
            assert info["completed_jobs"] == 1
            assert "registered_tasks" in info


class TestTaskExecution:
    """Tests for task execution logic."""

    @pytest.mark.asyncio
    async def test_health_check_task_execution(self):
        """Test health_check_task returns expected format."""
        from src.core.tasks import health_check_task

        ctx = {"job_id": "test-123"}
        result = await health_check_task(ctx)

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["worker_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_cleanup_task_execution(self):
        """Test cleanup_expired_sessions returns expected format."""
        from src.core.tasks import cleanup_expired_sessions

        ctx = {}
        result = await cleanup_expired_sessions(ctx)

        assert "cleaned_sessions" in result
        assert isinstance(result["cleaned_sessions"], int)

    @pytest.mark.asyncio
    async def test_payment_reminders_task_execution(self):
        """Test send_payment_reminders returns expected format."""
        from src.core.tasks import send_payment_reminders

        ctx = {}
        result = await send_payment_reminders(ctx, days_ahead=7)

        assert "reminders_sent" in result
        assert isinstance(result["reminders_sent"], int)
