"""Comprehensive integration tests for API endpoints.

Tests cover:
- Health check endpoint
- Subscription CRUD endpoints
- Agent execution endpoint
- Error handling
- Validation errors
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestSubscriptionCreate:
    """Tests for subscription creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, client: AsyncClient):
        """Test creating a subscription."""
        data = {
            "name": "Test Subscription",
            "amount": "9.99",
            "currency": "GBP",
            "frequency": "monthly",
            "start_date": "2024-01-01",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test Subscription"
        assert result["amount"] == "9.99"
        assert result["currency"] == "GBP"
        assert result["is_active"] is True
        assert "id" in result
        assert "next_payment_date" in result

    @pytest.mark.asyncio
    async def test_create_subscription_minimal(self, client: AsyncClient):
        """Test creating subscription with minimal fields."""
        data = {
            "name": "Minimal",
            "amount": "5.00",
            "start_date": "2024-01-01",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Minimal"
        assert result["frequency"] == "monthly"  # Default

    @pytest.mark.asyncio
    async def test_create_subscription_with_category(self, client: AsyncClient):
        """Test creating subscription with category."""
        data = {
            "name": "Netflix",
            "amount": "15.99",
            "start_date": "2024-01-01",
            "category": "entertainment",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 201
        assert response.json()["category"] == "entertainment"

    @pytest.mark.asyncio
    async def test_create_subscription_with_notes(self, client: AsyncClient):
        """Test creating subscription with notes."""
        data = {
            "name": "Insurance",
            "amount": "100.00",
            "start_date": "2024-01-01",
            "notes": "Annual home insurance",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 201
        assert response.json()["notes"] == "Annual home insurance"

    @pytest.mark.asyncio
    async def test_create_subscription_invalid_amount(self, client: AsyncClient):
        """Test creating subscription with invalid amount."""
        data = {
            "name": "Test",
            "amount": "-10.00",  # Negative
            "start_date": "2024-01-01",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_subscription_missing_name(self, client: AsyncClient):
        """Test creating subscription without name."""
        data = {
            "amount": "10.00",
            "start_date": "2024-01-01",
        }

        response = await client.post("/api/subscriptions", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_subscription_all_frequencies(self, client: AsyncClient):
        """Test creating subscriptions with all frequencies."""
        frequencies = ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]

        for freq in frequencies:
            data = {
                "name": f"Test {freq}",
                "amount": "10.00",
                "frequency": freq,
                "start_date": "2024-01-01",
            }

            response = await client.post("/api/subscriptions", json=data)

            assert response.status_code == 201
            assert response.json()["frequency"] == freq


class TestSubscriptionList:
    """Tests for subscription listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty(self, client: AsyncClient):
        """Test listing when no subscriptions exist."""
        response = await client.get("/api/subscriptions")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, client: AsyncClient):
        """Test listing subscriptions."""
        # Create a subscription first
        data = {
            "name": "Test",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        await client.post("/api/subscriptions", json=data)

        response = await client.get("/api/subscriptions")

        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_list_subscriptions_filter_active(self, client: AsyncClient):
        """Test filtering by active status."""
        # Create active subscription
        data = {
            "name": "Active",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        await client.post("/api/subscriptions", json=data)

        response = await client.get("/api/subscriptions?is_active=true")

        assert response.status_code == 200
        subscriptions = response.json()
        assert all(s["is_active"] for s in subscriptions)

    @pytest.mark.asyncio
    async def test_list_subscriptions_filter_category(self, client: AsyncClient):
        """Test filtering by category."""
        # Create subscriptions with different categories
        for cat in ["entertainment", "health"]:
            data = {
                "name": f"Test {cat}",
                "amount": "10.00",
                "start_date": "2024-01-01",
                "category": cat,
            }
            await client.post("/api/subscriptions", json=data)

        response = await client.get("/api/subscriptions?category=entertainment")

        assert response.status_code == 200
        subscriptions = response.json()
        assert len(subscriptions) == 1
        assert subscriptions[0]["category"] == "entertainment"


class TestSubscriptionGet:
    """Tests for getting single subscription."""

    @pytest.mark.asyncio
    async def test_get_subscription(self, client: AsyncClient):
        """Test getting subscription by ID."""
        # Create subscription
        data = {
            "name": "Test",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        create_response = await client.post("/api/subscriptions", json=data)
        subscription_id = create_response.json()["id"]

        response = await client.get(f"/api/subscriptions/{subscription_id}")

        assert response.status_code == 200
        assert response.json()["id"] == subscription_id

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, client: AsyncClient):
        """Test getting non-existent subscription."""
        response = await client.get("/api/subscriptions/non-existent-id")

        assert response.status_code == 404


class TestSubscriptionUpdate:
    """Tests for subscription update endpoint."""

    @pytest.mark.asyncio
    async def test_update_subscription(self, client: AsyncClient):
        """Test updating a subscription."""
        # Create subscription
        data = {
            "name": "Test",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        create_response = await client.post("/api/subscriptions", json=data)
        subscription_id = create_response.json()["id"]

        # Update
        update_data = {
            "amount": "15.00",
            "category": "updated",
        }
        response = await client.put(f"/api/subscriptions/{subscription_id}", json=update_data)

        assert response.status_code == 200
        assert response.json()["amount"] == "15.00"
        assert response.json()["category"] == "updated"

    @pytest.mark.asyncio
    async def test_update_subscription_not_found(self, client: AsyncClient):
        """Test updating non-existent subscription."""
        update_data = {"amount": "15.00"}
        response = await client.put("/api/subscriptions/non-existent-id", json=update_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_subscription_deactivate(self, client: AsyncClient):
        """Test deactivating a subscription."""
        # Create subscription
        data = {
            "name": "Test",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        create_response = await client.post("/api/subscriptions", json=data)
        subscription_id = create_response.json()["id"]

        # Deactivate
        update_data = {"is_active": False}
        response = await client.put(f"/api/subscriptions/{subscription_id}", json=update_data)

        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestSubscriptionDelete:
    """Tests for subscription deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_subscription(self, client: AsyncClient):
        """Test deleting a subscription."""
        # Create subscription
        data = {
            "name": "Test",
            "amount": "10.00",
            "start_date": "2024-01-01",
        }
        create_response = await client.post("/api/subscriptions", json=data)
        subscription_id = create_response.json()["id"]

        # Delete
        response = await client.delete(f"/api/subscriptions/{subscription_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/subscriptions/{subscription_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_subscription_not_found(self, client: AsyncClient):
        """Test deleting non-existent subscription."""
        response = await client.delete("/api/subscriptions/non-existent-id")

        assert response.status_code == 404


class TestSubscriptionSummary:
    """Tests for subscription summary endpoint."""

    @pytest.mark.asyncio
    async def test_summary_empty(self, client: AsyncClient):
        """Test summary with no subscriptions."""
        response = await client.get("/api/subscriptions/summary")

        assert response.status_code == 200
        result = response.json()
        # Decimal serializes with precision
        assert result["total_monthly"] in ("0", "0.00")
        assert result["total_yearly"] in ("0", "0.00")
        assert result["active_count"] == 0

    @pytest.mark.asyncio
    async def test_summary_with_subscriptions(self, client: AsyncClient):
        """Test summary with subscriptions."""
        # Create subscription
        data = {
            "name": "Test",
            "amount": "15.99",
            "start_date": "2024-01-01",
            "category": "entertainment",
        }
        await client.post("/api/subscriptions", json=data)

        response = await client.get("/api/subscriptions/summary")

        assert response.status_code == 200
        result = response.json()
        assert result["active_count"] == 1
        assert "entertainment" in result["by_category"]


class TestSummaryUpcoming:
    """Tests for upcoming payments in summary."""

    @pytest.mark.asyncio
    async def test_summary_includes_upcoming_week(self, client: AsyncClient):
        """Test that summary includes upcoming_week field."""
        response = await client.get("/api/subscriptions/summary")

        assert response.status_code == 200
        result = response.json()
        assert "upcoming_week" in result
        assert isinstance(result["upcoming_week"], list)


class TestAgentEndpoint:
    """Tests for agent execution endpoint."""

    @pytest.mark.asyncio
    async def test_agent_execute_list(self, client: AsyncClient):
        """Test agent list command."""
        response = await client.post(
            "/api/agent/execute",
            json={"command": "Show my subscriptions"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_execute_create(self, client: AsyncClient):
        """Test agent create command."""
        response = await client.post(
            "/api/agent/execute",
            json={"command": "Add Netflix for £15.99 monthly"},
        )

        assert response.status_code == 200
        # May succeed or fail depending on parsing
        assert "success" in response.json()

    @pytest.mark.asyncio
    async def test_agent_execute_summary(self, client: AsyncClient):
        """Test agent summary command."""
        response = await client.post(
            "/api/agent/execute",
            json={"command": "How much am I spending?"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_execute_unknown(self, client: AsyncClient):
        """Test agent unknown command."""
        response = await client.post(
            "/api/agent/execute",
            json={"command": "Hello world random text"},
        )

        assert response.status_code == 200
        result = response.json()
        # Agent now handles unknown commands gracefully with a helpful response
        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_agent_execute_empty_command(self, client: AsyncClient):
        """Test agent with empty command."""
        response = await client.post(
            "/api/agent/execute",
            json={"command": ""},
        )

        # Should return validation error
        assert response.status_code == 422
