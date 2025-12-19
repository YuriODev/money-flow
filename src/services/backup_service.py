"""Cloud Backup Service for Money Flow.

This module provides scheduled backup functionality to cloud storage.
Supports Google Cloud Storage as the primary backup destination.

Features:
- JSON export backup (all user data)
- Compressed backup files
- Retention policy (configurable days)
- Backup verification
- Restore functionality
"""

import gzip
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.models.subscription import Subscription

if TYPE_CHECKING:
    from src.models.user import User

logger = logging.getLogger(__name__)


class BackupMetadata(BaseModel):
    """Metadata about a backup file."""

    backup_id: str
    user_id: str
    created_at: datetime
    subscription_count: int
    file_size: int
    version: str = "2.0"
    storage_provider: str = "gcs"


class BackupResult(BaseModel):
    """Result of a backup operation."""

    success: bool
    backup_id: str | None = None
    file_path: str | None = None
    file_size: int = 0
    subscription_count: int = 0
    error: str | None = None


class BackupService:
    """Service for backing up user data to cloud storage.

    Supports:
    - Google Cloud Storage (primary)
    - Local file storage (fallback/dev)
    """

    def __init__(
        self,
        bucket_name: str | None = None,
        retention_days: int = 30,
    ):
        """Initialize backup service.

        Args:
            bucket_name: GCS bucket name. If None, uses config or local storage.
            retention_days: Number of days to retain backups.
        """
        self.bucket_name = bucket_name or getattr(settings, "gcs_backup_bucket", None)
        self.retention_days = retention_days
        self._gcs_client = None

    def _get_gcs_client(self) -> Any:
        """Get Google Cloud Storage client (lazy initialization).

        Returns:
            GCS client or None if GCS is not available.
        """
        if self._gcs_client is None:
            try:
                from google.cloud import storage

                self._gcs_client = storage.Client()
                logger.info("GCS client initialized")
            except ImportError:
                logger.warning("google-cloud-storage not installed, using local storage")
                return None
            except Exception as e:
                logger.warning(f"Failed to initialize GCS client: {e}")
                return None
        return self._gcs_client

    def _serialize_subscription(self, sub: Subscription) -> dict[str, Any]:
        """Serialize a subscription to a dictionary.

        Args:
            sub: Subscription model instance.

        Returns:
            Dictionary representation of the subscription.
        """

        def format_decimal(value: Decimal | None) -> str | None:
            if value is None:
                return None
            return str(value)

        def format_date(value: Any) -> str | None:
            if value is None:
                return None
            if hasattr(value, "isoformat"):
                return value.isoformat()
            return str(value)

        return {
            "id": str(sub.id),
            "name": sub.name,
            "amount": format_decimal(sub.amount),
            "currency": sub.currency,
            "frequency": sub.frequency.value,
            "frequency_interval": sub.frequency_interval,
            "start_date": format_date(sub.start_date),
            "end_date": format_date(sub.end_date),
            "next_payment_date": format_date(sub.next_payment_date),
            "last_payment_date": format_date(sub.last_payment_date),
            "payment_type": sub.payment_type.value if sub.payment_type else None,
            "payment_mode": sub.payment_mode.value if sub.payment_mode else None,
            "category": sub.category,
            "category_id": str(sub.category_id) if sub.category_id else None,
            "is_active": sub.is_active,
            "notes": sub.notes,
            "payment_method": sub.payment_method,
            "reminder_days": sub.reminder_days,
            "icon_url": sub.icon_url,
            "color": sub.color,
            "auto_renew": sub.auto_renew,
            "is_installment": sub.is_installment,
            "total_installments": sub.total_installments,
            "completed_installments": sub.completed_installments,
            "total_owed": format_decimal(sub.total_owed),
            "remaining_balance": format_decimal(sub.remaining_balance),
            "creditor": sub.creditor,
            "target_amount": format_decimal(sub.target_amount),
            "current_saved": format_decimal(sub.current_saved),
            "recipient": sub.recipient,
            "card_id": str(sub.card_id) if sub.card_id else None,
        }

    async def create_backup(
        self,
        db: AsyncSession,
        user: "User",
    ) -> BackupResult:
        """Create a backup of all user subscriptions.

        Args:
            db: Database session.
            user: User whose data to backup.

        Returns:
            BackupResult with backup details.
        """
        backup_id = f"{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating backup {backup_id} for user {user.id}")

        try:
            # Fetch all subscriptions for the user
            result = await db.execute(
                select(Subscription)
                .where(Subscription.user_id == str(user.id))
                .options(selectinload(Subscription.category_rel))
            )
            subscriptions = list(result.scalars().all())

            # Create backup data
            backup_data = {
                "version": "2.0",
                "backup_id": backup_id,
                "created_at": datetime.utcnow().isoformat(),
                "user_id": str(user.id),
                "user_email": user.email,
                "subscription_count": len(subscriptions),
                "subscriptions": [self._serialize_subscription(sub) for sub in subscriptions],
            }

            # Serialize to JSON
            json_data = json.dumps(backup_data, indent=2, default=str)

            # Compress
            compressed = gzip.compress(json_data.encode("utf-8"))
            file_size = len(compressed)

            # Upload to storage
            file_path = await self._upload_backup(
                backup_id=backup_id,
                data=compressed,
                user_id=str(user.id),
            )

            logger.info(
                f"Backup {backup_id} created successfully: "
                f"{len(subscriptions)} subscriptions, {file_size} bytes"
            )

            return BackupResult(
                success=True,
                backup_id=backup_id,
                file_path=file_path,
                file_size=file_size,
                subscription_count=len(subscriptions),
            )

        except Exception as e:
            logger.error(f"Backup failed for user {user.id}: {e}")
            return BackupResult(
                success=False,
                backup_id=backup_id,
                error=str(e),
            )

    async def _upload_backup(
        self,
        backup_id: str,
        data: bytes,
        user_id: str,
    ) -> str:
        """Upload backup to cloud storage or local file.

        Args:
            backup_id: Unique backup identifier.
            data: Compressed backup data.
            user_id: User ID for path organization.

        Returns:
            Path or URL to the uploaded file.
        """
        filename = f"{backup_id}.json.gz"
        blob_path = f"backups/{user_id}/{filename}"

        gcs_client = self._get_gcs_client()
        if gcs_client and self.bucket_name:
            try:
                bucket = gcs_client.bucket(self.bucket_name)
                blob = bucket.blob(blob_path)
                blob.upload_from_string(data, content_type="application/gzip")
                logger.info(f"Uploaded backup to gs://{self.bucket_name}/{blob_path}")
                return f"gs://{self.bucket_name}/{blob_path}"
            except Exception as e:
                logger.warning(f"GCS upload failed, falling back to local: {e}")

        # Fallback to local storage
        import os

        local_dir = f"backups/{user_id}"
        os.makedirs(local_dir, exist_ok=True)
        local_path = f"{local_dir}/{filename}"

        with open(local_path, "wb") as f:
            f.write(data)

        logger.info(f"Saved backup locally to {local_path}")
        return local_path

    async def list_backups(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[BackupMetadata]:
        """List available backups for a user.

        Args:
            user_id: User ID to list backups for.
            limit: Maximum number of backups to return.

        Returns:
            List of BackupMetadata objects.
        """
        backups: list[BackupMetadata] = []
        prefix = f"backups/{user_id}/"

        gcs_client = self._get_gcs_client()
        if gcs_client and self.bucket_name:
            try:
                bucket = gcs_client.bucket(self.bucket_name)
                blobs = bucket.list_blobs(prefix=prefix, max_results=limit)

                for blob in blobs:
                    if blob.name.endswith(".json.gz"):
                        backup_id = blob.name.split("/")[-1].replace(".json.gz", "")
                        backups.append(
                            BackupMetadata(
                                backup_id=backup_id,
                                user_id=user_id,
                                created_at=blob.time_created,
                                subscription_count=0,  # Would need to parse file
                                file_size=blob.size or 0,
                            )
                        )
                return backups
            except Exception as e:
                logger.warning(f"Failed to list GCS backups: {e}")

        # Fallback to local storage
        import os

        local_dir = f"backups/{user_id}"
        if os.path.exists(local_dir):
            files = sorted(os.listdir(local_dir), reverse=True)[:limit]
            for f in files:
                if f.endswith(".json.gz"):
                    backup_id = f.replace(".json.gz", "")
                    file_path = os.path.join(local_dir, f)
                    stat = os.stat(file_path)
                    backups.append(
                        BackupMetadata(
                            backup_id=backup_id,
                            user_id=user_id,
                            created_at=datetime.fromtimestamp(stat.st_mtime),
                            subscription_count=0,
                            file_size=stat.st_size,
                            storage_provider="local",
                        )
                    )

        return backups

    async def cleanup_old_backups(
        self,
        user_id: str,
    ) -> int:
        """Delete backups older than retention period.

        Args:
            user_id: User ID to clean up backups for.

        Returns:
            Number of backups deleted.
        """
        deleted = 0
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        prefix = f"backups/{user_id}/"

        gcs_client = self._get_gcs_client()
        if gcs_client and self.bucket_name:
            try:
                bucket = gcs_client.bucket(self.bucket_name)
                blobs = bucket.list_blobs(prefix=prefix)

                for blob in blobs:
                    if blob.time_created and blob.time_created.replace(tzinfo=None) < cutoff:
                        blob.delete()
                        deleted += 1
                        logger.info(f"Deleted old backup: {blob.name}")

                return deleted
            except Exception as e:
                logger.warning(f"Failed to cleanup GCS backups: {e}")

        # Fallback to local storage
        import os

        local_dir = f"backups/{user_id}"
        if os.path.exists(local_dir):
            for f in os.listdir(local_dir):
                if f.endswith(".json.gz"):
                    file_path = os.path.join(local_dir, f)
                    stat = os.stat(file_path)
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff:
                        os.remove(file_path)
                        deleted += 1
                        logger.info(f"Deleted old local backup: {file_path}")

        return deleted


async def run_scheduled_backup(
    db: AsyncSession,
    user: "User",
    backup_service: BackupService | None = None,
) -> BackupResult:
    """Run a scheduled backup for a user.

    This is the main entry point for the scheduled backup task.

    Args:
        db: Database session.
        user: User to backup.
        backup_service: Optional backup service instance.

    Returns:
        BackupResult with backup details.
    """
    service = backup_service or BackupService()

    # Create backup
    result = await service.create_backup(db, user)

    # Cleanup old backups if successful
    if result.success:
        deleted = await service.cleanup_old_backups(str(user.id))
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backups for user {user.id}")

    return result
