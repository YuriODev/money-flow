"""Performance Benchmark Tests for Sprint 2.4.

Pytest-based performance benchmarks that measure:
- Response time percentiles (p50, p95, p99)
- Throughput (requests per second)
- Database query performance

Usage:
    # Run benchmarks (requires running backend):
    pytest tests/performance/test_benchmarks.py -v --benchmark-enable

    # With detailed output:
    pytest tests/performance/test_benchmarks.py -v -s

Note:
    These tests require a running backend at localhost:8001.
    They are skipped if the backend is not available.
"""

import statistics
import time
from collections.abc import Generator
from dataclasses import dataclass
from datetime import date, timedelta

import httpx
import pytest

# Backend URL
BASE_URL = "http://localhost:8001"


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    requests_per_second: float


def calculate_percentile(data: list[float], percentile: float) -> float:
    """Calculate the given percentile of a list of values."""
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def run_benchmark(
    func,
    iterations: int = 100,
    warmup: int = 5,
) -> BenchmarkResult:
    """Run a benchmark function multiple times and collect metrics."""
    # Warmup runs
    for _ in range(warmup):
        func()

    # Timed runs
    times_ms = []
    start_total = time.perf_counter()

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times_ms.append((end - start) * 1000)

    end_total = time.perf_counter()
    total_seconds = end_total - start_total

    return BenchmarkResult(
        name=func.__name__,
        iterations=iterations,
        min_ms=min(times_ms),
        max_ms=max(times_ms),
        mean_ms=statistics.mean(times_ms),
        median_ms=statistics.median(times_ms),
        p95_ms=calculate_percentile(times_ms, 95),
        p99_ms=calculate_percentile(times_ms, 99),
        std_dev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        requests_per_second=iterations / total_seconds,
    )


def print_benchmark_result(result: BenchmarkResult):
    """Pretty print benchmark results."""
    print(f"\n{'=' * 60}")
    print(f"Benchmark: {result.name}")
    print(f"{'=' * 60}")
    print(f"Iterations: {result.iterations}")
    print(f"Min:     {result.min_ms:8.2f} ms")
    print(f"Max:     {result.max_ms:8.2f} ms")
    print(f"Mean:    {result.mean_ms:8.2f} ms")
    print(f"Median:  {result.median_ms:8.2f} ms")
    print(f"P95:     {result.p95_ms:8.2f} ms")
    print(f"P99:     {result.p99_ms:8.2f} ms")
    print(f"Std Dev: {result.std_dev_ms:8.2f} ms")
    print(f"RPS:     {result.requests_per_second:8.2f} req/s")
    print(f"{'=' * 60}")


@pytest.fixture(scope="module")
def backend_available() -> bool:
    """Check if backend is available."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module")
def auth_token(backend_available: bool) -> Generator[str | None, None, None]:
    """Get authentication token for tests."""
    if not backend_available:
        yield None
        return

    # Register and login
    import uuid

    email = f"benchmark_{uuid.uuid4().hex[:8]}@example.com"
    password = "BenchmarkTest123!@#"

    try:
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            # Register
            response = client.post(
                "/api/auth/register",
                json={"email": email, "password": password},
            )

            if response.status_code == 201:
                data = response.json()
                yield data.get("access_token")
            elif response.status_code == 400:
                # User exists, try login
                response = client.post(
                    "/api/auth/login",
                    json={"email": email, "password": password},
                )
                if response.status_code == 200:
                    data = response.json()
                    yield data.get("access_token")
                else:
                    yield None
            else:
                yield None
    except Exception:
        yield None


@pytest.fixture(scope="module")
def client_with_auth(
    backend_available: bool, auth_token: str | None
) -> Generator[httpx.Client | None, None, None]:
    """Create authenticated HTTP client."""
    if not backend_available or not auth_token:
        yield None
        return

    headers = {"Authorization": f"Bearer {auth_token}"}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=30) as client:
        yield client


class TestHealthEndpointBenchmarks:
    """Benchmarks for health check endpoints."""

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, backend_available):
        """Skip tests if backend is not available."""
        if not backend_available:
            pytest.skip("Backend not available at localhost:8001")

    def test_health_endpoint_performance(self):
        """Benchmark GET /health endpoint."""
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:

            def health_request():
                client.get("/health")

            result = run_benchmark(health_request, iterations=100)
            print_benchmark_result(result)

            # Performance assertions
            assert result.p95_ms < 100, f"P95 latency {result.p95_ms}ms exceeds 100ms"
            assert result.mean_ms < 50, f"Mean latency {result.mean_ms}ms exceeds 50ms"

    def test_health_live_endpoint_performance(self):
        """Benchmark GET /health/live endpoint."""
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:

            def liveness_request():
                client.get("/health/live")

            result = run_benchmark(liveness_request, iterations=100)
            print_benchmark_result(result)

            # Performance assertions
            assert result.p95_ms < 50, f"P95 latency {result.p95_ms}ms exceeds 50ms"


class TestSubscriptionEndpointBenchmarks:
    """Benchmarks for subscription CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, client_with_auth):
        """Skip tests if client is not available."""
        if not client_with_auth:
            pytest.skip("Authenticated client not available")

    def test_list_subscriptions_performance(self, client_with_auth: httpx.Client):
        """Benchmark GET /api/subscriptions endpoint."""

        def list_request():
            client_with_auth.get("/api/subscriptions")

        result = run_benchmark(list_request, iterations=50)
        print_benchmark_result(result)

        # Performance assertions
        assert result.p95_ms < 200, f"P95 latency {result.p95_ms}ms exceeds 200ms"

    def test_create_subscription_performance(self, client_with_auth: httpx.Client):
        """Benchmark POST /api/subscriptions endpoint."""
        import random

        def create_request():
            client_with_auth.post(
                "/api/subscriptions",
                json={
                    "name": f"Benchmark-{random.randint(1000, 9999)}",
                    "amount": 19.99,
                    "currency": "GBP",
                    "frequency": "monthly",
                    "payment_type": "subscription",
                    "start_date": str(date.today()),
                    "next_payment_date": str(date.today() + timedelta(days=30)),
                },
            )

        result = run_benchmark(create_request, iterations=30)
        print_benchmark_result(result)

        # Performance assertions
        assert result.p95_ms < 300, f"P95 latency {result.p95_ms}ms exceeds 300ms"

    def test_summary_endpoint_performance(self, client_with_auth: httpx.Client):
        """Benchmark GET /api/subscriptions/summary endpoint."""

        def summary_request():
            client_with_auth.get("/api/subscriptions/summary")

        result = run_benchmark(summary_request, iterations=50)
        print_benchmark_result(result)

        # Performance assertions (summary is more complex)
        assert result.p95_ms < 500, f"P95 latency {result.p95_ms}ms exceeds 500ms"


class TestAgentEndpointBenchmarks:
    """Benchmarks for AI agent endpoint.

    Note: Agent endpoint is expensive due to AI inference.
    Lower iteration count and higher latency thresholds.
    """

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, client_with_auth):
        """Skip tests if client is not available."""
        if not client_with_auth:
            pytest.skip("Authenticated client not available")

    @pytest.mark.slow
    def test_agent_execute_performance(self, client_with_auth: httpx.Client):
        """Benchmark POST /api/agent/execute endpoint."""

        def agent_request():
            client_with_auth.post(
                "/api/agent/execute",
                json={"command": "Show my subscriptions"},
            )

        # Lower iterations due to AI cost
        result = run_benchmark(agent_request, iterations=10, warmup=2)
        print_benchmark_result(result)

        # Higher threshold for AI endpoint
        assert result.p95_ms < 5000, f"P95 latency {result.p95_ms}ms exceeds 5000ms"


class TestDatabaseQueryBenchmarks:
    """Benchmarks for database query performance.

    Uses direct database queries to measure raw DB performance.
    """

    @pytest.mark.asyncio
    async def test_subscription_query_performance(self):
        """Benchmark direct database subscription queries."""
        pytest.skip("Requires database connection - run with integration test setup")
