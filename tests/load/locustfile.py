"""Locust Load Testing Configuration for Sprint 2.4.

Load testing scenarios for Money Flow API endpoints:
- Authentication endpoints
- Subscription CRUD operations
- Agent endpoint (AI commands)
- Summary and analytics endpoints

Usage:
    # Start backend first:
    docker-compose up -d

    # Run Locust Web UI:
    locust -f tests/load/locustfile.py --host=http://localhost:8001

    # Headless mode (10 users, spawn rate 1/sec, run for 60s):
    locust -f tests/load/locustfile.py --host=http://localhost:8001 \
           --headless -u 10 -r 1 -t 60s

    # CI mode with HTML report:
    locust -f tests/load/locustfile.py --host=http://localhost:8001 \
           --headless -u 50 -r 5 -t 5m --html=reports/load_test_report.html
"""

import random
import uuid
from datetime import date, timedelta

from locust import HttpUser, between, task


class AuthenticatedUser(HttpUser):
    """Base user class with authentication support.

    Handles login on start and includes auth headers in all requests.
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    # Class-level token cache to avoid re-authenticating
    _access_token: str | None = None
    _test_user_id: str | None = None

    def on_start(self):
        """Called when a simulated user starts. Handles authentication."""
        self._login_or_register()

    def _login_or_register(self):
        """Login with existing user or register a new one."""
        # Generate unique email for this virtual user
        unique_id = str(uuid.uuid4())[:8]
        self.email = f"loadtest_{unique_id}@example.com"
        self.password = "LoadTest123!@#"

        # Try to register first
        register_response = self.client.post(
            "/api/auth/register",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="/api/auth/register",
        )

        if register_response.status_code == 201:
            data = register_response.json()
            self._access_token = data.get("access_token")
            self._test_user_id = data.get("user", {}).get("id")
        elif register_response.status_code == 400:
            # User exists, try login
            login_response = self.client.post(
                "/api/auth/login",
                json={
                    "email": self.email,
                    "password": self.password,
                },
                name="/api/auth/login",
            )
            if login_response.status_code == 200:
                data = login_response.json()
                self._access_token = data.get("access_token")
                self._test_user_id = data.get("user", {}).get("id")

    @property
    def auth_headers(self):
        """Get authorization headers."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}


class SubscriptionCRUDUser(AuthenticatedUser):
    """User performing subscription CRUD operations.

    Tests:
    - GET /api/subscriptions (list)
    - POST /api/subscriptions (create)
    - GET /api/subscriptions/{id} (read)
    - PUT /api/subscriptions/{id} (update)
    - DELETE /api/subscriptions/{id} (delete)
    """

    weight = 3  # 3x more likely to be spawned

    # Track created subscription IDs for cleanup
    _created_ids: list[str] = []

    @task(5)
    def list_subscriptions(self):
        """List all subscriptions (most common operation)."""
        self.client.get(
            "/api/subscriptions",
            headers=self.auth_headers,
            name="/api/subscriptions [GET]",
        )

    @task(3)
    def create_subscription(self):
        """Create a new subscription."""
        subscription_data = {
            "name": f"LoadTest-{random.randint(1000, 9999)}",
            "amount": round(random.uniform(5.0, 50.0), 2),
            "currency": random.choice(["GBP", "USD", "EUR"]),
            "frequency": random.choice(["monthly", "yearly", "weekly"]),
            "payment_type": "subscription",
            "start_date": str(date.today()),
            "next_payment_date": str(date.today() + timedelta(days=30)),
        }

        response = self.client.post(
            "/api/subscriptions",
            json=subscription_data,
            headers=self.auth_headers,
            name="/api/subscriptions [POST]",
        )

        if response.status_code == 201:
            data = response.json()
            if isinstance(data, dict) and "id" in data:
                self._created_ids.append(data["id"])

    @task(2)
    def get_subscription(self):
        """Get a specific subscription."""
        if self._created_ids:
            sub_id = random.choice(self._created_ids)
            self.client.get(
                f"/api/subscriptions/{sub_id}",
                headers=self.auth_headers,
                name="/api/subscriptions/{id} [GET]",
            )

    @task(1)
    def update_subscription(self):
        """Update a subscription."""
        if self._created_ids:
            sub_id = random.choice(self._created_ids)
            update_data = {
                "name": f"Updated-{random.randint(1000, 9999)}",
                "amount": round(random.uniform(10.0, 100.0), 2),
            }
            self.client.put(
                f"/api/subscriptions/{sub_id}",
                json=update_data,
                headers=self.auth_headers,
                name="/api/subscriptions/{id} [PUT]",
            )

    @task(1)
    def delete_subscription(self):
        """Delete a subscription."""
        if len(self._created_ids) > 5:  # Keep some for other tests
            sub_id = self._created_ids.pop()
            self.client.delete(
                f"/api/subscriptions/{sub_id}",
                headers=self.auth_headers,
                name="/api/subscriptions/{id} [DELETE]",
            )


class SummaryUser(AuthenticatedUser):
    """User viewing summary and analytics.

    Tests:
    - GET /api/subscriptions/summary
    - GET /api/subscriptions/upcoming
    """

    weight = 2

    @task(3)
    def get_summary(self):
        """Get subscription summary."""
        self.client.get(
            "/api/subscriptions/summary",
            headers=self.auth_headers,
            name="/api/subscriptions/summary [GET]",
        )

    @task(2)
    def get_upcoming_payments(self):
        """Get upcoming payments."""
        days = random.choice([7, 14, 30])
        self.client.get(
            f"/api/subscriptions/upcoming?days={days}",
            headers=self.auth_headers,
            name="/api/subscriptions/upcoming [GET]",
        )


class AgentUser(AuthenticatedUser):
    """User using the AI agent interface.

    Tests:
    - POST /api/agent/execute (natural language commands)

    Note: This is the most expensive operation (AI inference).
    """

    weight = 1  # Less common due to cost

    # Sample commands for testing
    _commands = [
        "Show my subscriptions",
        "What's my total spending?",
        "List all monthly subscriptions",
        "How much do I spend on entertainment?",
        "Show subscriptions under £20",
    ]

    @task(1)
    def execute_agent_command(self):
        """Execute an AI agent command."""
        command = random.choice(self._commands)
        self.client.post(
            "/api/agent/execute",
            json={"command": command},
            headers=self.auth_headers,
            name="/api/agent/execute [POST]",
        )


class HealthCheckUser(HttpUser):
    """User checking health endpoints (unauthenticated).

    Tests:
    - GET /health
    - GET /health/live
    - GET /health/ready
    """

    wait_time = between(2, 5)
    weight = 1

    @task(1)
    def health_check(self):
        """Check basic health."""
        self.client.get("/health", name="/health [GET]")

    @task(1)
    def liveness_check(self):
        """Check liveness probe."""
        self.client.get("/health/live", name="/health/live [GET]")

    @task(1)
    def readiness_check(self):
        """Check readiness probe."""
        self.client.get("/health/ready", name="/health/ready [GET]")


class MixedWorkloadUser(AuthenticatedUser):
    """User with mixed workload simulating real usage patterns.

    Combines various operations with realistic weights.
    """

    weight = 2

    @task(10)
    def view_dashboard(self):
        """Simulate dashboard view (list + summary)."""
        self.client.get(
            "/api/subscriptions",
            headers=self.auth_headers,
            name="/api/subscriptions [GET]",
        )
        self.client.get(
            "/api/subscriptions/summary",
            headers=self.auth_headers,
            name="/api/subscriptions/summary [GET]",
        )

    @task(3)
    def add_subscription(self):
        """Add a new subscription."""
        subscription_data = {
            "name": f"TestSub-{random.randint(1000, 9999)}",
            "amount": round(random.uniform(5.0, 100.0), 2),
            "currency": "GBP",
            "frequency": "monthly",
            "payment_type": random.choice(["subscription", "utility", "housing", "insurance"]),
            "start_date": str(date.today()),
            "next_payment_date": str(date.today() + timedelta(days=30)),
        }
        self.client.post(
            "/api/subscriptions",
            json=subscription_data,
            headers=self.auth_headers,
            name="/api/subscriptions [POST]",
        )

    @task(2)
    def check_upcoming(self):
        """Check upcoming payments."""
        self.client.get(
            "/api/subscriptions/upcoming?days=30",
            headers=self.auth_headers,
            name="/api/subscriptions/upcoming [GET]",
        )

    @task(1)
    def use_agent(self):
        """Use AI agent."""
        commands = [
            "Show my subscriptions",
            "What do I spend monthly?",
            "List my streaming services",
        ]
        self.client.post(
            "/api/agent/execute",
            json={"command": random.choice(commands)},
            headers=self.auth_headers,
            name="/api/agent/execute [POST]",
        )
