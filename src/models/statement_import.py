"""Statement import job and detected subscription models.

This module provides SQLAlchemy models for:
- StatementImportJob: Tracks the status of statement file processing
- DetectedSubscription: Stores AI-detected recurring payments from statements
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    from src.models.subscription import Subscription
    from src.models.user import User


class ImportJobStatus(str, Enum):
    """Status of an import job."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"  # Analysis complete, awaiting user confirmation
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileType(str, Enum):
    """Supported statement file types."""

    PDF = "pdf"
    CSV = "csv"
    OFX = "ofx"
    QFX = "qfx"
    QIF = "qif"


class DetectionStatus(str, Enum):
    """Status of a detected subscription."""

    PENDING = "pending"  # Awaiting user decision
    SELECTED = "selected"  # User selected for import
    SKIPPED = "skipped"  # User skipped
    IMPORTED = "imported"  # Successfully imported
    DUPLICATE = "duplicate"  # Matched existing subscription
    MERGED = "merged"  # Merged with existing subscription


class StatementImportJob(Base):
    """Model for tracking statement import jobs.

    Represents an uploaded statement file and its processing status.
    Each job can have multiple detected subscriptions.
    """

    __tablename__ = "statement_import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # NOTE: User model uses String(36) for id, not UUID
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        SQLEnum(FileType, name="file_type_enum"),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(nullable=True)  # Size in bytes

    # Bank information (optional)
    bank_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bank_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")

    # Processing status
    status: Mapped[ImportJobStatus] = mapped_column(
        SQLEnum(ImportJobStatus, name="import_job_status_enum"),
        default=ImportJobStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Processing results
    total_transactions: Mapped[int] = mapped_column(default=0)
    detected_count: Mapped[int] = mapped_column(default=0)
    imported_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    duplicate_count: Mapped[int] = mapped_column(default=0)

    # Statement period
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Raw data for debugging (optional)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="import_jobs")
    detected_subscriptions: Mapped[list[DetectedSubscription]] = relationship(
        "DetectedSubscription",
        back_populates="import_job",
        cascade="all, delete-orphan",
        order_by="DetectedSubscription.confidence.desc()",
    )

    __table_args__ = (
        Index("ix_import_jobs_user_status", "user_id", "status"),
        Index("ix_import_jobs_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<StatementImportJob(id={self.id}, filename={self.filename}, status={self.status})>"

    @property
    def is_processing(self) -> bool:
        """Check if job is currently processing."""
        return self.status in (ImportJobStatus.PENDING, ImportJobStatus.PROCESSING)

    @property
    def is_ready_for_review(self) -> bool:
        """Check if job is ready for user review."""
        return self.status == ImportJobStatus.READY

    @property
    def is_complete(self) -> bool:
        """Check if job is fully complete."""
        return self.status in (ImportJobStatus.COMPLETED, ImportJobStatus.CANCELLED)


class DetectedSubscription(Base):
    """Model for AI-detected subscriptions from statements.

    Stores potential recurring payments detected from bank statements,
    awaiting user confirmation before being imported.
    """

    __tablename__ = "detected_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statement_import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Detected information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")

    # Frequency and classification
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(50), default="subscription")

    # Detection confidence
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    amount_variance: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    transaction_count: Mapped[int] = mapped_column(default=0)

    # Date range seen
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # User selection status
    status: Mapped[DetectionStatus] = mapped_column(
        SQLEnum(DetectionStatus, name="detection_status_enum"),
        default=DetectionStatus.PENDING,
        nullable=False,
    )
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)

    # Duplicate handling
    # NOTE: Subscription model uses String(36) for id
    duplicate_of_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    duplicate_similarity: Mapped[float | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    # Created subscription reference (after import)
    # NOTE: Subscription model uses String(36) for id
    created_subscription_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Sample transaction descriptions
    sample_descriptions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Raw detection data for debugging
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    import_job: Mapped[StatementImportJob] = relationship(
        "StatementImportJob",
        back_populates="detected_subscriptions",
    )
    duplicate_of: Mapped[Subscription | None] = relationship(
        "Subscription",
        foreign_keys=[duplicate_of_id],
    )
    created_subscription: Mapped[Subscription | None] = relationship(
        "Subscription",
        foreign_keys=[created_subscription_id],
    )

    __table_args__ = (
        Index("ix_detected_subs_job_status", "job_id", "status"),
        Index("ix_detected_subs_job_confidence", "job_id", "confidence"),
    )

    def __repr__(self) -> str:
        return (
            f"<DetectedSubscription(id={self.id}, name={self.name}, confidence={self.confidence})>"
        )

    @property
    def is_high_confidence(self) -> bool:
        """Check if detection has high confidence."""
        return float(self.confidence) >= 0.8

    @property
    def is_duplicate(self) -> bool:
        """Check if this is a duplicate of an existing subscription."""
        return self.duplicate_of_id is not None
