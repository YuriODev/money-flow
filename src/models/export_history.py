"""Export history ORM model.

This module defines the SQLAlchemy ORM model for tracking all export
operations (JSON, CSV, PDF) for audit and compliance purposes.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class ExportFormat(str, Enum):
    """Export file format."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ExportType(str, Enum):
    """Type of export."""

    FULL_BACKUP = "full_backup"
    SUBSCRIPTIONS = "subscriptions"
    REPORT = "report"
    PAYMENT_HISTORY = "payment_history"


class ExportStatus(str, Enum):
    """Export operation status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportHistory(Base):
    """Export history/audit log model.

    Tracks all export operations for audit and compliance purposes.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: Foreign key to users table.
        export_type: Type of export (full_backup, subscriptions, report).
        export_format: File format (json, csv, pdf).
        filename: Generated filename.
        file_size: Size of the exported file in bytes.
        record_count: Number of records exported.
        status: Export status (pending, completed, failed).
        error_message: Error message if export failed.
        ip_address: IP address of the requester.
        user_agent: User agent string.
        created_at: When the export was initiated.
        completed_at: When the export completed.
        extra_data: Additional JSON data (filters, options, etc.).

    Example:
        >>> export = ExportHistory(
        ...     user_id="user-uuid",
        ...     export_type=ExportType.FULL_BACKUP,
        ...     export_format=ExportFormat.JSON,
        ...     filename="backup_20251219.json",
        ...     status=ExportStatus.COMPLETED,
        ... )
    """

    __tablename__ = "export_history"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Export details
    export_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    export_format: Mapped[str] = mapped_column(String(10), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=ExportStatus.PENDING.value)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Additional data (JSON string)
    extra_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        """Return string representation of export history."""
        return (
            f"<ExportHistory(user_id='{self.user_id}', "
            f"type='{self.export_type}', format='{self.export_format}')>"
        )

    def mark_completed(self, filename: str, file_size: int, record_count: int) -> None:
        """Mark export as completed.

        Args:
            filename: The generated filename.
            file_size: Size of the file in bytes.
            record_count: Number of records exported.
        """
        self.status = ExportStatus.COMPLETED.value
        self.filename = filename
        self.file_size = file_size
        self.record_count = record_count
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark export as failed.

        Args:
            error: Error message describing the failure.
        """
        self.status = ExportStatus.FAILED.value
        self.error_message = error
        self.completed_at = datetime.utcnow()

    def get_extra_data_dict(self) -> dict | None:
        """Get extra data as a dictionary.

        Returns:
            The extra data parsed from JSON, or None if not set.
        """
        import json

        if not self.extra_data:
            return None
        try:
            return json.loads(self.extra_data)
        except json.JSONDecodeError:
            return None

    def set_extra_data(self, data: dict) -> None:
        """Set extra data from a dictionary.

        Args:
            data: The extra data to store.
        """
        import json

        self.extra_data = json.dumps(data)

    @property
    def duration_seconds(self) -> float | None:
        """Calculate export duration in seconds.

        Returns:
            Duration in seconds, or None if not completed.
        """
        if not self.completed_at:
            return None
        return (self.completed_at - self.created_at).total_seconds()
