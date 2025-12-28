"""Unit tests for IFTTT/Zapier integration system.

Tests cover:
- Integration models (APIKey, RestHookSubscription)
- Integration schemas (validation, serialization)
- Integration service (API keys, REST hooks, events)

Sprint 5.6 - IFTTT/Zapier Integration
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.integration import (
    APIKey,
    IntegrationStatus,
    IntegrationType,
    RestHookSubscription,
)
from src.schemas.integration import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyListResponse,
    APIKeyResponse,
    EventPayload,
    EventTypeInfo,
    IntegrationStatsResponse,
    IntegrationStatusEnum,
    IntegrationTypeEnum,
    PaymentEventData,
    RestHookListResponse,
    RestHookResponse,
    RestHookSubscribe,
    SampleDataResponse,
    SubscriptionEventData,
)
from src.services.integration_service import IntegrationService


# ============================================================================
# Model Tests
# ============================================================================


class TestIntegrationTypeEnum:
    """Tests for IntegrationType enum."""

    def test_zapier_value(self):
        """Test Zapier integration type value."""
        assert IntegrationType.ZAPIER.value == "zapier"

    def test_ifttt_value(self):
        """Test IFTTT integration type value."""
        assert IntegrationType.IFTTT.value == "ifttt"

    def test_custom_value(self):
        """Test custom integration type value."""
        assert IntegrationType.CUSTOM.value == "custom"

    def test_all_values(self):
        """Test all integration type values exist."""
        values = [e.value for e in IntegrationType]
        assert "zapier" in values
        assert "ifttt" in values
        assert "custom" in values


class TestIntegrationStatusEnum:
    """Tests for IntegrationStatus enum."""

    def test_active_value(self):
        """Test active status value."""
        assert IntegrationStatus.ACTIVE.value == "active"

    def test_paused_value(self):
        """Test paused status value."""
        assert IntegrationStatus.PAUSED.value == "paused"

    def test_expired_value(self):
        """Test expired status value."""
        assert IntegrationStatus.EXPIRED.value == "expired"

    def test_revoked_value(self):
        """Test revoked status value."""
        assert IntegrationStatus.REVOKED.value == "revoked"


class TestAPIKeyModel:
    """Tests for APIKey SQLAlchemy model."""

    def test_create_api_key(self):
        """Test creating an API key instance."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Test Key",
            key_hash="abc123" * 10 + "abcd",  # 64 chars
            key_prefix="mf_test_",
            integration_type=IntegrationType.ZAPIER,
            scopes="read:subscriptions",
        )
        assert key.name == "Test Key"
        assert key.integration_type == IntegrationType.ZAPIER
        assert key.scopes == "read:subscriptions"

    def test_api_key_with_is_active(self):
        """Test API key with is_active field."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Test",
            key_hash="a" * 64,
            key_prefix="mf_test_",
            integration_type=IntegrationType.IFTTT,
            is_active=True,
        )
        assert key.is_active is True

    def test_api_key_with_expiration(self):
        """Test API key with expiration date."""
        expires = datetime.now(UTC) + timedelta(days=30)
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Expiring Key",
            key_hash="b" * 64,
            key_prefix="mf_exp_",
            integration_type=IntegrationType.CUSTOM,
            expires_at=expires,
        )
        assert key.expires_at == expires

    def test_api_key_scopes_list(self):
        """Test parsing scopes as list."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Multi-scope",
            key_hash="c" * 64,
            key_prefix="mf_mult",
            integration_type=IntegrationType.ZAPIER,
            scopes="read:subscriptions,write:subscriptions,read:payments",
        )
        scopes = key.scopes.split(",") if key.scopes else []
        assert len(scopes) == 3
        assert "read:subscriptions" in scopes
        assert "write:subscriptions" in scopes

    def test_generate_key(self):
        """Test API key generation."""
        full_key, key_hash, key_prefix = APIKey.generate_key()

        assert full_key.startswith("mf_live_")
        assert len(key_hash) == 64  # SHA-256 hex
        assert key_prefix == full_key[:8]

        # Verify hash matches
        expected_hash = hashlib.sha256(full_key.encode()).hexdigest()
        assert key_hash == expected_hash

    def test_hash_key(self):
        """Test API key hashing."""
        test_key = "mf_test_abcdef123456"
        expected = hashlib.sha256(test_key.encode()).hexdigest()
        assert APIKey.hash_key(test_key) == expected

    def test_is_expired_not_set(self):
        """Test is_expired when no expiration."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="No Expiry",
            key_hash="d" * 64,
            key_prefix="mf_nexp",
            integration_type=IntegrationType.CUSTOM,
        )
        assert key.is_expired() is False

    def test_is_expired_future(self):
        """Test is_expired with future date."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Future Expiry",
            key_hash="e" * 64,
            key_prefix="mf_fut_",
            integration_type=IntegrationType.CUSTOM,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        assert key.is_expired() is False

    def test_is_expired_past(self):
        """Test is_expired with past date."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Past Expiry",
            key_hash="f" * 64,
            key_prefix="mf_past",
            integration_type=IntegrationType.CUSTOM,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        assert key.is_expired() is True

    def test_has_scope(self):
        """Test scope checking."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Scoped Key",
            key_hash="g" * 64,
            key_prefix="mf_scop",
            integration_type=IntegrationType.ZAPIER,
            scopes="read:subscriptions,write:subscriptions",
        )
        assert key.has_scope("read:subscriptions") is True
        assert key.has_scope("write:subscriptions") is True
        assert key.has_scope("delete:all") is False

    def test_record_usage(self):
        """Test recording API key usage."""
        key = APIKey(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Usage Key",
            key_hash="h" * 64,
            key_prefix="mf_use_",
            integration_type=IntegrationType.CUSTOM,
        )
        assert key.last_used_at is None
        key.record_usage()
        assert key.last_used_at is not None


class TestRestHookSubscriptionModel:
    """Tests for RestHookSubscription SQLAlchemy model."""

    def test_create_subscription(self):
        """Test creating a REST hook subscription."""
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            target_url="https://hooks.zapier.com/test",
            event_type="subscription.created",
            integration_type=IntegrationType.ZAPIER,
        )
        assert sub.target_url == "https://hooks.zapier.com/test"
        assert sub.event_type == "subscription.created"

    def test_subscription_with_api_key(self):
        """Test subscription linked to API key."""
        api_key_id = str(uuid4())
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            api_key_id=api_key_id,
            target_url="https://hooks.zapier.com/xyz",
            event_type="subscription.updated",
            integration_type=IntegrationType.ZAPIER,
        )
        assert sub.api_key_id == api_key_id

    def test_record_success(self):
        """Test recording successful delivery."""
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            target_url="https://hooks.example.com/success",
            event_type="payment.due",
            integration_type=IntegrationType.CUSTOM,
            delivery_count=5,
        )
        sub.record_success()
        assert sub.delivery_count == 6
        assert sub.last_delivery_at is not None
        assert sub.last_error is None

    def test_record_failure(self):
        """Test recording failed delivery."""
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            target_url="https://hooks.example.com/fail",
            event_type="payment.completed",
            integration_type=IntegrationType.IFTTT,
            failure_count=2,
        )
        sub.record_failure("Connection timeout")
        assert sub.failure_count == 3
        assert sub.last_delivery_at is not None
        assert sub.last_error == "Connection timeout"

    def test_pause_resume(self):
        """Test pausing and resuming subscription."""
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            target_url="https://hooks.example.com/pause",
            event_type="subscription.deleted",
            integration_type=IntegrationType.ZAPIER,
            status=IntegrationStatus.ACTIVE,
        )
        assert sub.status == IntegrationStatus.ACTIVE

        sub.pause()
        assert sub.status == IntegrationStatus.PAUSED

        sub.resume()
        assert sub.status == IntegrationStatus.ACTIVE

    def test_revoke(self):
        """Test revoking subscription."""
        sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=str(uuid4()),
            target_url="https://hooks.example.com/revoke",
            event_type="budget.alert",
            integration_type=IntegrationType.CUSTOM,
            status=IntegrationStatus.ACTIVE,
        )
        sub.revoke()
        assert sub.status == IntegrationStatus.REVOKED


# ============================================================================
# Schema Tests
# ============================================================================


class TestAPIKeySchemas:
    """Tests for API key Pydantic schemas."""

    def test_api_key_create_minimal(self):
        """Test creating API key with minimal data."""
        data = APIKeyCreate(name="My Key")
        assert data.name == "My Key"
        assert data.integration_type == IntegrationTypeEnum.CUSTOM
        assert data.scopes is None  # Defaults to None, service fills default

    def test_api_key_create_with_scopes(self):
        """Test creating API key with custom scopes."""
        data = APIKeyCreate(
            name="Full Access",
            integration_type=IntegrationTypeEnum.ZAPIER,
            scopes="read:subscriptions,write:subscriptions,read:payments",
        )
        assert "write:subscriptions" in data.scopes

    def test_api_key_create_with_expiration(self):
        """Test creating API key with expiration in days."""
        data = APIKeyCreate(
            name="Temporary Key",
            expires_in_days=90,
        )
        assert data.expires_in_days == 90

    def test_api_key_name_too_short(self):
        """Test validation rejects short names."""
        with pytest.raises(ValidationError):
            APIKeyCreate(name="")

    def test_api_key_name_too_long(self):
        """Test validation rejects long names."""
        with pytest.raises(ValidationError):
            APIKeyCreate(name="x" * 101)

    def test_api_key_response(self):
        """Test API key response schema."""
        now = datetime.now(UTC)
        response = APIKeyResponse(
            id=str(uuid4()),
            name="Test Key",
            key_prefix="mf_test_",
            integration_type=IntegrationTypeEnum.IFTTT,
            scopes="read:subscriptions",
            is_active=True,
            created_at=now,
            last_used_at=None,
            expires_at=None,
        )
        assert response.key_prefix == "mf_test_"
        assert response.is_active is True

    def test_api_key_created_response(self):
        """Test API key created response includes full key."""
        now = datetime.now(UTC)
        response = APIKeyCreatedResponse(
            id=str(uuid4()),
            name="New Key",
            api_key="mf_live_abcdef123456",
            key_prefix="mf_live_",
            integration_type=IntegrationTypeEnum.ZAPIER,
            scopes="read:subscriptions",
            expires_at=None,
            created_at=now,
        )
        assert response.api_key.startswith("mf_live_")

    def test_api_key_list_response(self):
        """Test API key list response."""
        now = datetime.now(UTC)
        response = APIKeyListResponse(
            keys=[
                APIKeyResponse(
                    id=str(uuid4()),
                    name="Key 1",
                    key_prefix="mf_k1__",
                    integration_type=IntegrationTypeEnum.ZAPIER,
                    scopes="read:subscriptions",
                    is_active=True,
                    created_at=now,
                    last_used_at=None,
                    expires_at=None,
                )
            ],
            total=1,
        )
        assert response.total == 1
        assert len(response.keys) == 1


class TestRestHookSchemas:
    """Tests for REST hook Pydantic schemas."""

    def test_subscribe_minimal(self):
        """Test subscription with minimal data."""
        data = RestHookSubscribe(
            target_url="https://hooks.zapier.com/abc123",
            event_type="subscription.created",
        )
        # HttpUrl is returned as object, convert to string
        assert str(data.target_url) == "https://hooks.zapier.com/abc123"
        assert data.event_type == "subscription.created"

    def test_subscribe_invalid_url(self):
        """Test validation rejects invalid URLs."""
        with pytest.raises(ValidationError):
            RestHookSubscribe(
                target_url="not-a-url",
                event_type="subscription.created",
            )

    def test_subscribe_invalid_event_type(self):
        """Test validation rejects invalid event types."""
        with pytest.raises(ValidationError):
            RestHookSubscribe(
                target_url="https://hooks.zapier.com/test",
                event_type="invalid.event.type",
            )

    def test_rest_hook_response(self):
        """Test REST hook response schema."""
        now = datetime.now(UTC)
        response = RestHookResponse(
            id=str(uuid4()),
            target_url="https://hooks.zapier.com/xyz",
            event_type="subscription.updated",
            integration_type=IntegrationTypeEnum.ZAPIER,
            status=IntegrationStatusEnum.ACTIVE,
            delivery_count=10,
            failure_count=2,
            created_at=now,
            last_delivery_at=None,
        )
        assert response.delivery_count == 10
        assert response.status == IntegrationStatusEnum.ACTIVE

    def test_rest_hook_list_response(self):
        """Test REST hook list response."""
        now = datetime.now(UTC)
        response = RestHookListResponse(
            subscriptions=[
                RestHookResponse(
                    id=str(uuid4()),
                    target_url="https://hooks.example.com/1",
                    event_type="subscription.created",
                    integration_type=IntegrationTypeEnum.CUSTOM,
                    status=IntegrationStatusEnum.ACTIVE,
                    delivery_count=5,
                    failure_count=0,
                    created_at=now,
                    last_delivery_at=None,
                )
            ],
            total=1,
        )
        assert response.total == 1


class TestEventSchemas:
    """Tests for event payload schemas."""

    def test_subscription_event_data(self):
        """Test subscription event data."""
        data = SubscriptionEventData(
            subscription_id=str(uuid4()),
            name="Netflix",
            amount=15.99,
            currency="GBP",
            frequency="monthly",
            next_payment_date=datetime.now(UTC),
            category="Entertainment",
        )
        assert data.name == "Netflix"
        assert data.amount == 15.99

    def test_payment_event_data(self):
        """Test payment event data."""
        data = PaymentEventData(
            subscription_id=str(uuid4()),
            subscription_name="Spotify",
            amount=10.99,
            currency="GBP",
            payment_date=datetime.now(UTC),
            status="completed",
            days_until_due=None,
        )
        assert data.subscription_name == "Spotify"
        assert data.status == "completed"

    def test_event_payload(self):
        """Test event payload wrapper."""
        now = datetime.now(UTC)
        payload = EventPayload(
            id=str(uuid4()),
            event_type="subscription.created",
            timestamp=now,
            data={"name": "Test Sub", "amount": 9.99},
        )
        assert payload.event_type == "subscription.created"
        assert payload.data["name"] == "Test Sub"

    def test_event_type_info(self):
        """Test event type info."""
        info = EventTypeInfo(
            name="subscription.created",
            description="Triggered when a subscription is created",
            sample_payload={"name": "Example", "amount": 5.99},
        )
        assert info.name == "subscription.created"
        assert "Example" in str(info.sample_payload)

    def test_sample_data_response(self):
        """Test sample data response."""
        now = datetime.now(UTC)
        response = SampleDataResponse(
            samples=[
                EventPayload(
                    id="sample-1",
                    event_type="subscription.created",
                    timestamp=now,
                    data={"name": "Netflix", "amount": 15.99},
                ),
                EventPayload(
                    id="sample-2",
                    event_type="subscription.created",
                    timestamp=now,
                    data={"name": "Spotify", "amount": 10.99},
                ),
            ]
        )
        assert len(response.samples) == 2


class TestStatsSchemas:
    """Tests for integration statistics schemas."""

    def test_integration_stats_response(self):
        """Test integration stats response."""
        stats = IntegrationStatsResponse(
            total_api_keys=3,
            active_api_keys=2,
            total_subscriptions=5,
            active_subscriptions=4,
            total_deliveries=150,
            successful_deliveries=140,
            failed_deliveries=10,
            delivery_success_rate=93.33,
        )
        assert stats.total_api_keys == 3
        assert stats.active_api_keys == 2
        assert stats.total_deliveries == 150
        assert stats.delivery_success_rate == 93.33


# ============================================================================
# Service Tests
# ============================================================================


class TestIntegrationServiceAPIKeys:
    """Tests for IntegrationService API key management."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return str(uuid4())

    @pytest.fixture
    def service(self, mock_db, user_id):
        """Create IntegrationService instance."""
        return IntegrationService(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_create_api_key(self, service, mock_db):
        """Test creating an API key."""
        data = APIKeyCreate(
            name="Test Key",
            integration_type=IntegrationTypeEnum.ZAPIER,
            scopes="read:subscriptions,write:subscriptions",
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        api_key, full_key = await service.create_api_key(data)

        assert api_key.name == "Test Key"
        assert full_key.startswith("mf_live_")
        assert len(full_key) > 20
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_key_hash_verification(self, service, mock_db):
        """Test API key hash is correctly computed."""
        data = APIKeyCreate(name="Hash Test")

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        api_key, full_key = await service.create_api_key(data)

        # Verify hash matches
        expected_hash = hashlib.sha256(full_key.encode()).hexdigest()
        assert api_key.key_hash == expected_hash

    @pytest.mark.asyncio
    async def test_api_key_prefix_stored(self, service, mock_db):
        """Test API key prefix is stored correctly."""
        data = APIKeyCreate(name="Prefix Test")

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        api_key, full_key = await service.create_api_key(data)

        assert api_key.key_prefix == full_key[:8]

    @pytest.mark.asyncio
    async def test_list_api_keys(self, service, mock_db, user_id):
        """Test listing API keys."""
        mock_keys = [
            APIKey(
                id=str(uuid4()),
                user_id=user_id,
                name="Key 1",
                key_hash="a" * 64,
                key_prefix="mf_k1__",
                integration_type=IntegrationType.ZAPIER,
            ),
            APIKey(
                id=str(uuid4()),
                user_id=user_id,
                name="Key 2",
                key_hash="b" * 64,
                key_prefix="mf_k2__",
                integration_type=IntegrationType.IFTTT,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        mock_db.execute = AsyncMock(return_value=mock_result)

        keys, total = await service.list_api_keys()

        assert len(keys) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, service, mock_db, user_id):
        """Test revoking an API key."""
        key_id = str(uuid4())
        mock_key = APIKey(
            id=key_id,
            user_id=user_id,
            name="To Revoke",
            key_hash="c" * 64,
            key_prefix="mf_rev_",
            integration_type=IntegrationType.CUSTOM,
            is_active=True,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        revoked = await service.revoke_api_key(key_id)

        assert revoked is True
        assert mock_key.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self, service, mock_db):
        """Test revoking a nonexistent key returns False."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        revoked = await service.revoke_api_key(str(uuid4()))

        assert revoked is False

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, service, mock_db, user_id):
        """Test validating a valid API key."""
        full_key = "mf_test_" + secrets.token_hex(16)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        mock_key = APIKey(
            id=str(uuid4()),
            user_id=user_id,
            name="Valid Key",
            key_hash=key_hash,
            key_prefix=full_key[:8],
            integration_type=IntegrationType.ZAPIER,
            is_active=True,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        api_key, error = await service.validate_api_key(full_key)

        assert api_key is not None
        assert error is None
        assert api_key.last_used_at is not None

    @pytest.mark.asyncio
    async def test_validate_api_key_not_found(self, service, mock_db):
        """Test validating a nonexistent API key."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        api_key, error = await service.validate_api_key("mf_fake_abcdef123456")

        assert api_key is None
        assert error == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_api_key_revoked(self, service, mock_db, user_id):
        """Test validating a revoked API key."""
        full_key = "mf_rev__" + secrets.token_hex(16)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        mock_key = APIKey(
            id=str(uuid4()),
            user_id=user_id,
            name="Revoked Key",
            key_hash=key_hash,
            key_prefix=full_key[:8],
            integration_type=IntegrationType.ZAPIER,
            is_active=False,  # Key is revoked
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute = AsyncMock(return_value=mock_result)

        api_key, error = await service.validate_api_key(full_key)

        assert api_key is None
        assert error == "API key has been revoked"

    @pytest.mark.asyncio
    async def test_validate_api_key_expired(self, service, mock_db, user_id):
        """Test validating an expired API key."""
        full_key = "mf_exp__" + secrets.token_hex(16)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        mock_key = APIKey(
            id=str(uuid4()),
            user_id=user_id,
            name="Expired Key",
            key_hash=key_hash,
            key_prefix=full_key[:8],
            integration_type=IntegrationType.ZAPIER,
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        api_key, error = await service.validate_api_key(full_key)

        assert api_key is None
        assert error == "API key has expired"


class TestIntegrationServiceRestHooks:
    """Tests for IntegrationService REST hook management."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return str(uuid4())

    @pytest.fixture
    def service(self, mock_db, user_id):
        """Create IntegrationService instance."""
        return IntegrationService(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_subscribe(self, service, mock_db):
        """Test subscribing to events."""
        data = RestHookSubscribe(
            target_url="https://hooks.zapier.com/test123",
            event_type="subscription.created",
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        subscription = await service.subscribe(data, IntegrationType.ZAPIER)

        assert subscription.target_url == "https://hooks.zapier.com/test123"
        assert subscription.event_type == "subscription.created"
        assert subscription.integration_type == IntegrationType.ZAPIER
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_with_api_key(self, service, mock_db):
        """Test subscribing with linked API key."""
        api_key_id = str(uuid4())
        data = RestHookSubscribe(
            target_url="https://hooks.zapier.com/with-key",
            event_type="payment.due",
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        subscription = await service.subscribe(
            data,
            IntegrationType.ZAPIER,
            api_key_id=api_key_id,
        )

        assert subscription.api_key_id == api_key_id

    @pytest.mark.asyncio
    async def test_unsubscribe(self, service, mock_db, user_id):
        """Test unsubscribing from events."""
        sub_id = str(uuid4())
        mock_sub = RestHookSubscription(
            id=sub_id,
            user_id=user_id,
            target_url="https://hooks.example.com/unsub",
            event_type="subscription.deleted",
            integration_type=IntegrationType.IFTTT,
            status=IntegrationStatus.ACTIVE,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        unsubscribed = await service.unsubscribe(sub_id)

        assert unsubscribed is True
        assert mock_sub.status == IntegrationStatus.REVOKED

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, service, mock_db):
        """Test unsubscribing from nonexistent subscription."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        unsubscribed = await service.unsubscribe(str(uuid4()))

        assert unsubscribed is False

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, service, mock_db, user_id):
        """Test listing subscriptions."""
        mock_subs = [
            RestHookSubscription(
                id=str(uuid4()),
                user_id=user_id,
                target_url="https://hooks.zapier.com/1",
                event_type="subscription.created",
                integration_type=IntegrationType.ZAPIER,
            ),
            RestHookSubscription(
                id=str(uuid4()),
                user_id=user_id,
                target_url="https://maker.ifttt.com/2",
                event_type="payment.due",
                integration_type=IntegrationType.IFTTT,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subs
        mock_db.execute = AsyncMock(return_value=mock_result)

        subs, total = await service.list_subscriptions()

        assert len(subs) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_list_subscriptions_by_event_type(self, service, mock_db, user_id):
        """Test listing subscriptions filtered by event type."""
        mock_subs = [
            RestHookSubscription(
                id=str(uuid4()),
                user_id=user_id,
                target_url="https://hooks.zapier.com/only",
                event_type="subscription.created",
                integration_type=IntegrationType.ZAPIER,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subs
        mock_db.execute = AsyncMock(return_value=mock_result)

        subs, total = await service.list_subscriptions(event_type="subscription.created")

        assert len(subs) == 1
        assert subs[0].event_type == "subscription.created"


class TestIntegrationServiceEvents:
    """Tests for IntegrationService event triggering."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return str(uuid4())

    @pytest.fixture
    def service(self, mock_db, user_id):
        """Create IntegrationService instance."""
        return IntegrationService(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_trigger_event_no_subscribers(self, service, mock_db):
        """Test triggering event with no subscribers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        successful = await service.trigger_event(
            "subscription.created",
            {"name": "Test", "amount": 9.99},
        )

        assert successful == 0

    @pytest.mark.asyncio
    @patch("src.services.integration_service.httpx.AsyncClient")
    async def test_trigger_event_with_subscriber(
        self, mock_httpx, service, mock_db, user_id
    ):
        """Test triggering event with active subscriber."""
        mock_sub = RestHookSubscription(
            id=str(uuid4()),
            user_id=user_id,
            target_url="https://hooks.zapier.com/success",
            event_type="subscription.created",
            integration_type=IntegrationType.ZAPIER,
            status=IntegrationStatus.ACTIVE,
            delivery_count=5,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        successful = await service.trigger_event(
            "subscription.created",
            {"name": "Netflix", "amount": 15.99},
        )

        assert successful == 1
        assert mock_sub.delivery_count == 6  # Incremented
        assert mock_sub.last_delivery_at is not None

    @pytest.mark.asyncio
    async def test_get_sample_data_fallback(self, service, mock_db):
        """Test sample data fallback when no real data."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        samples = await service.get_sample_data("subscription.created", limit=3)

        # Should return example sample data
        assert len(samples) > 0
        assert samples[0].event_type == "subscription.created"

    def test_static_samples_subscription_created(self, service):
        """Test static samples for subscription.created."""
        samples = service._get_static_samples("subscription.created", 3)
        assert len(samples) == 3
        assert samples[0].data["name"] == "Netflix"

    def test_static_samples_payment_due(self, service):
        """Test static samples for payment.due."""
        samples = service._get_static_samples("payment.due", 2)
        assert len(samples) == 2
        assert samples[0].data["status"] == "due"

    def test_static_samples_budget_alert(self, service):
        """Test static samples for budget.alert."""
        samples = service._get_static_samples("budget.alert", 1)
        assert len(samples) == 1
        assert "budget_limit" in samples[0].data


class TestIntegrationServiceStats:
    """Tests for IntegrationService statistics."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def user_id(self):
        """Create test user ID."""
        return str(uuid4())

    @pytest.fixture
    def service(self, mock_db, user_id):
        """Create IntegrationService instance."""
        return IntegrationService(mock_db, user_id)

    @pytest.mark.asyncio
    async def test_get_stats(self, service, mock_db, user_id):
        """Test getting integration statistics."""
        # Mock API keys aggregation result
        mock_key_row = MagicMock()
        mock_key_row.total = 2
        mock_key_row.active = 1

        mock_key_result = MagicMock()
        mock_key_result.one.return_value = mock_key_row

        # Mock subscriptions aggregation result
        mock_sub_row = MagicMock()
        mock_sub_row.total = 3
        mock_sub_row.active = 2
        mock_sub_row.deliveries = 100
        mock_sub_row.failures = 10

        mock_sub_result = MagicMock()
        mock_sub_result.one.return_value = mock_sub_row

        # Configure mock to return different results
        call_count = [0]

        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_key_result
            return mock_sub_result

        mock_db.execute = mock_execute

        stats = await service.get_stats()

        assert stats["total_api_keys"] == 2
        assert stats["active_api_keys"] == 1
        assert stats["total_subscriptions"] == 3
        assert stats["active_subscriptions"] == 2
        assert stats["total_deliveries"] == 110  # 100 + 10
        assert stats["successful_deliveries"] == 100
        assert stats["failed_deliveries"] == 10
        assert stats["delivery_success_rate"] == 90.91  # 100/110 * 100


# ============================================================================
# Additional Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_api_key_create_default_scopes(self):
        """Test API key creation defaults."""
        data = APIKeyCreate(name="Default Scopes")
        # Schema allows None, service will fill default
        assert data.scopes is None

    def test_all_event_types(self):
        """Test all supported event types."""
        event_types = [
            "subscription.created",
            "subscription.updated",
            "subscription.deleted",
            "payment.due",
            "payment.overdue",
            "payment.completed",
            "payment.skipped",
            "budget.alert",
            "import.completed",
            "calendar.synced",
        ]
        for event_type in event_types:
            data = RestHookSubscribe(
                target_url="https://hooks.example.com/test",
                event_type=event_type,
            )
            assert data.event_type == event_type

    def test_integration_type_enum_conversion(self):
        """Test enum conversion between model and schema."""
        model_type = IntegrationType.ZAPIER
        schema_type = IntegrationTypeEnum(model_type.value)
        assert schema_type == IntegrationTypeEnum.ZAPIER

    def test_status_enum_conversion(self):
        """Test status enum conversion."""
        model_status = IntegrationStatus.ACTIVE
        schema_status = IntegrationStatusEnum(model_status.value)
        assert schema_status == IntegrationStatusEnum.ACTIVE

    def test_long_target_url(self):
        """Test handling of long webhook URLs."""
        long_url = "https://hooks.zapier.com/" + "a" * 1900
        data = RestHookSubscribe(
            target_url=long_url,
            event_type="subscription.created",
        )
        assert len(str(data.target_url)) <= 2000

    def test_special_characters_in_name(self):
        """Test API key name with special characters."""
        data = APIKeyCreate(name="My Key (Production) - v2.0")
        assert data.name == "My Key (Production) - v2.0"

    def test_expires_in_days_validation(self):
        """Test expiration days validation."""
        # Valid range
        data = APIKeyCreate(name="Valid", expires_in_days=365)
        assert data.expires_in_days == 365

        # Too high
        with pytest.raises(ValidationError):
            APIKeyCreate(name="Invalid", expires_in_days=366)

        # Too low
        with pytest.raises(ValidationError):
            APIKeyCreate(name="Invalid", expires_in_days=0)
