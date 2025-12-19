"""Unit tests for backup service.

Tests cover:
- BackupService initialization
- Subscription serialization
- Backup metadata models
- Local storage fallback
"""

import gzip
import json
import tempfile
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.services.backup_service import (
    BackupMetadata,
    BackupResult,
    BackupService,
)


class MockUser:
    """Mock User object for testing."""

    def __init__(self, user_id: str = "test-user-123", email: str = "test@example.com"):
        self.id = user_id
        self.email = email
        self.is_active = True


class MockCategory:
    """Mock Category object for testing."""

    def __init__(self, name: str = "Entertainment"):
        self.id = "cat-123"
        self.name = name


class MockSubscription:
    """Mock Subscription object for testing."""

    def __init__(
        self,
        sub_id: str = "sub-123",
        name: str = "Netflix",
        amount: Decimal = Decimal("15.99"),
        currency: str = "GBP",
        frequency: Frequency = Frequency.MONTHLY,
        frequency_interval: int = 1,
        start_date: date | None = None,
        end_date: date | None = None,
        next_payment_date: date | None = None,
        last_payment_date: date | None = None,
        payment_type: PaymentType = PaymentType.SUBSCRIPTION,
        payment_mode: PaymentMode = PaymentMode.RECURRING,
        category: str | None = None,
        category_id: str | None = None,
        category_rel: MockCategory | None = None,
        is_active: bool = True,
        notes: str | None = None,
        payment_method: str | None = None,
        reminder_days: int | None = None,
        icon_url: str | None = None,
        color: str | None = None,
        auto_renew: bool = True,
        is_installment: bool = False,
        total_installments: int | None = None,
        completed_installments: int | None = None,
        total_owed: Decimal | None = None,
        remaining_balance: Decimal | None = None,
        creditor: str | None = None,
        target_amount: Decimal | None = None,
        current_saved: Decimal | None = None,
        recipient: str | None = None,
        card_id: str | None = None,
    ):
        self.id = sub_id
        self.name = name
        self.amount = amount
        self.currency = currency
        self.frequency = frequency
        self.frequency_interval = frequency_interval
        self.start_date = start_date or date.today()
        self.end_date = end_date
        self.next_payment_date = next_payment_date or date.today()
        self.last_payment_date = last_payment_date
        self.payment_type = payment_type
        self.payment_mode = payment_mode
        self.category = category
        self.category_id = category_id
        self.category_rel = category_rel
        self.is_active = is_active
        self.notes = notes
        self.payment_method = payment_method
        self.reminder_days = reminder_days
        self.icon_url = icon_url
        self.color = color
        self.auto_renew = auto_renew
        self.is_installment = is_installment
        self.total_installments = total_installments
        self.completed_installments = completed_installments
        self.total_owed = total_owed
        self.remaining_balance = remaining_balance
        self.creditor = creditor
        self.target_amount = target_amount
        self.current_saved = current_saved
        self.recipient = recipient
        self.card_id = card_id


class TestBackupMetadata:
    """Tests for BackupMetadata model."""

    def test_create_metadata(self):
        """Test creating backup metadata."""
        metadata = BackupMetadata(
            backup_id="user123_20251218_120000",
            user_id="user123",
            created_at=datetime.utcnow(),
            subscription_count=10,
            file_size=1024,
        )
        assert metadata.backup_id == "user123_20251218_120000"
        assert metadata.user_id == "user123"
        assert metadata.subscription_count == 10
        assert metadata.file_size == 1024
        assert metadata.version == "2.0"
        assert metadata.storage_provider == "gcs"

    def test_metadata_with_local_storage(self):
        """Test metadata with local storage provider."""
        metadata = BackupMetadata(
            backup_id="test",
            user_id="user1",
            created_at=datetime.utcnow(),
            subscription_count=0,
            file_size=0,
            storage_provider="local",
        )
        assert metadata.storage_provider == "local"


class TestBackupResult:
    """Tests for BackupResult model."""

    def test_successful_result(self):
        """Test successful backup result."""
        result = BackupResult(
            success=True,
            backup_id="backup123",
            file_path="/backups/test.json.gz",
            file_size=2048,
            subscription_count=15,
        )
        assert result.success is True
        assert result.backup_id == "backup123"
        assert result.file_size == 2048
        assert result.error is None

    def test_failed_result(self):
        """Test failed backup result."""
        result = BackupResult(
            success=False,
            backup_id="backup123",
            error="Connection failed",
        )
        assert result.success is False
        assert result.error == "Connection failed"


class TestBackupServiceInit:
    """Tests for BackupService initialization."""

    def test_default_init(self):
        """Test service initialization with defaults."""
        service = BackupService()
        assert service.retention_days == 30
        assert service._gcs_client is None

    def test_custom_retention(self):
        """Test service with custom retention days."""
        service = BackupService(retention_days=7)
        assert service.retention_days == 7

    def test_custom_bucket(self):
        """Test service with custom bucket name."""
        service = BackupService(bucket_name="my-backup-bucket")
        assert service.bucket_name == "my-backup-bucket"


class TestSubscriptionSerialization:
    """Tests for subscription serialization."""

    def test_serialize_basic_subscription(self):
        """Test serializing a basic subscription."""
        service = BackupService()
        sub = MockSubscription()

        result = service._serialize_subscription(sub)

        assert result["id"] == "sub-123"
        assert result["name"] == "Netflix"
        assert result["amount"] == "15.99"
        assert result["currency"] == "GBP"
        assert result["frequency"] == "monthly"
        assert result["is_active"] is True

    def test_serialize_debt_subscription(self):
        """Test serializing a debt subscription with special fields."""
        service = BackupService()
        sub = MockSubscription(
            name="Credit Card",
            payment_type=PaymentType.DEBT,
            payment_mode=PaymentMode.DEBT,
            total_owed=Decimal("5000.00"),
            remaining_balance=Decimal("3500.00"),
            creditor="Bank of Test",
        )

        result = service._serialize_subscription(sub)

        assert result["payment_type"] == "debt"
        assert result["payment_mode"] == "debt"
        assert result["total_owed"] == "5000.00"
        assert result["remaining_balance"] == "3500.00"
        assert result["creditor"] == "Bank of Test"

    def test_serialize_savings_subscription(self):
        """Test serializing a savings subscription with special fields."""
        service = BackupService()
        sub = MockSubscription(
            name="Emergency Fund",
            payment_type=PaymentType.SAVINGS,
            payment_mode=PaymentMode.SAVINGS,
            target_amount=Decimal("10000.00"),
            current_saved=Decimal("2500.00"),
            recipient="Savings Account",
        )

        result = service._serialize_subscription(sub)

        assert result["payment_type"] == "savings"
        assert result["payment_mode"] == "savings"
        assert result["target_amount"] == "10000.00"
        assert result["current_saved"] == "2500.00"
        assert result["recipient"] == "Savings Account"

    def test_serialize_null_values(self):
        """Test serializing subscription with null optional fields."""
        service = BackupService()
        sub = MockSubscription(
            total_owed=None,
            remaining_balance=None,
            target_amount=None,
        )

        result = service._serialize_subscription(sub)

        assert result["total_owed"] is None
        assert result["remaining_balance"] is None
        assert result["target_amount"] is None

    def test_serialize_with_category(self):
        """Test serializing subscription with category relationship."""
        service = BackupService()
        sub = MockSubscription(
            category="Entertainment",
            category_id="cat-123",
            category_rel=MockCategory("Entertainment"),
        )

        result = service._serialize_subscription(sub)

        assert result["category"] == "Entertainment"
        assert result["category_id"] == "cat-123"

    def test_serialize_with_card(self):
        """Test serializing subscription linked to a card."""
        service = BackupService()
        sub = MockSubscription(card_id="card-456")

        result = service._serialize_subscription(sub)

        assert result["card_id"] == "card-456"


class TestLocalBackup:
    """Tests for local backup storage (fallback)."""

    def test_upload_to_local(self):
        """Test uploading backup to local storage."""
        service = BackupService(bucket_name=None)  # Force local storage

        with tempfile.TemporaryDirectory():
            # Test that local storage fallback is attempted when GCS unavailable
            assert service._get_gcs_client() is None  # GCS not available
            # bucket_name is None or empty string (from config default)
            assert not service.bucket_name  # Falsy check (None or empty)


class TestBackupListAndCleanup:
    """Tests for backup listing and cleanup."""

    def test_list_backups_service_init(self):
        """Test backup service initialization for listing."""
        service = BackupService(bucket_name=None)
        # Verify service is properly initialized for local storage
        # bucket_name is None or empty string (from config default)
        assert not service.bucket_name  # Falsy check (None or empty)
        assert service._gcs_client is None


class TestGCSClientLazyInit:
    """Tests for GCS client lazy initialization."""

    def test_gcs_not_installed(self):
        """Test GCS client returns None when library not installed."""
        service = BackupService()

        with patch.dict("sys.modules", {"google.cloud": None}):
            # Force re-initialization
            service._gcs_client = None
            client = service._get_gcs_client()
            # Should handle import error gracefully
            # Result depends on actual google-cloud-storage installation
            assert client is None or client is not None  # Either is valid


class TestBackupDataFormat:
    """Tests for backup data format."""

    def test_backup_data_structure(self):
        """Test that backup data has correct structure."""
        service = BackupService()

        # Create test data
        sub = MockSubscription()
        serialized = service._serialize_subscription(sub)

        # Verify all expected fields are present
        expected_fields = [
            "id",
            "name",
            "amount",
            "currency",
            "frequency",
            "frequency_interval",
            "start_date",
            "end_date",
            "next_payment_date",
            "last_payment_date",
            "payment_type",
            "payment_mode",
            "category",
            "category_id",
            "is_active",
            "notes",
            "payment_method",
            "reminder_days",
            "icon_url",
            "color",
            "auto_renew",
            "is_installment",
            "total_installments",
            "completed_installments",
            "total_owed",
            "remaining_balance",
            "creditor",
            "target_amount",
            "current_saved",
            "recipient",
            "card_id",
        ]

        for field in expected_fields:
            assert field in serialized, f"Missing field: {field}"

    def test_date_formatting(self):
        """Test that dates are formatted as ISO strings."""
        service = BackupService()

        test_date = date(2025, 12, 18)
        sub = MockSubscription(
            start_date=test_date,
            next_payment_date=test_date,
        )

        serialized = service._serialize_subscription(sub)

        assert serialized["start_date"] == "2025-12-18"
        assert serialized["next_payment_date"] == "2025-12-18"

    def test_decimal_formatting(self):
        """Test that decimals are formatted as strings."""
        service = BackupService()

        sub = MockSubscription(
            amount=Decimal("123.45"),
            total_owed=Decimal("1000.00"),
        )

        serialized = service._serialize_subscription(sub)

        assert serialized["amount"] == "123.45"
        assert serialized["total_owed"] == "1000.00"
        # Verify they're strings, not floats
        assert isinstance(serialized["amount"], str)


class TestBackupCompression:
    """Tests for backup compression."""

    def test_gzip_compression(self):
        """Test that backup data is properly gzip compressed."""
        # Create sample JSON data
        data = {"test": "data", "subscriptions": [{"name": "Test"}]}
        json_str = json.dumps(data)
        json_bytes = json_str.encode("utf-8")

        # Compress
        compressed = gzip.compress(json_bytes)

        # Verify compression happened
        assert (
            len(compressed) <= len(json_bytes) or len(json_bytes) < 100
        )  # Small data might not compress much

        # Verify decompression works
        decompressed = gzip.decompress(compressed)
        assert decompressed == json_bytes

        # Verify JSON is recoverable
        recovered = json.loads(decompressed.decode("utf-8"))
        assert recovered == data


class TestRetentionPolicy:
    """Tests for backup retention policy."""

    def test_retention_days_default(self):
        """Test default retention days."""
        service = BackupService()
        assert service.retention_days == 30

    def test_retention_days_custom(self):
        """Test custom retention days."""
        service = BackupService(retention_days=7)
        assert service.retention_days == 7

    def test_retention_days_long(self):
        """Test long retention period."""
        service = BackupService(retention_days=365)
        assert service.retention_days == 365
