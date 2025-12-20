"""Statement import API endpoints.

This module provides endpoints for:
- Uploading bank statement files
- Processing and analyzing statements
- Reviewing detected subscriptions
- Confirming imports
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_active_user
from src.core.dependencies import get_db
from src.models.statement_import import (
    DetectedSubscription,
    DetectionStatus,
    FileType,
    ImportJobStatus,
    StatementImportJob,
)
from src.models.subscription import Frequency, PaymentType, Subscription
from src.models.user import User
from src.schemas.statement import (
    BulkUpdateDetectedRequest,
    BulkUpdateDetectedResponse,
    ConfirmImportRequest,
    ConfirmImportResponse,
    DetectedSubscriptionResponse,
    DetectedSubscriptionUpdate,
    DuplicateCheckResponse,
    DuplicateMatch,
    ImportJobListResponse,
    ImportJobResponse,
    ImportJobStatusResponse,
    ImportPreviewResponse,
    ImportPreviewSummary,
    StatementUploadResponse,
)
from src.services.bank_service import BankService
from src.services.duplicate_detector import DuplicateDetector
from src.services.parsers import CSVStatementParser, OFXStatementParser, PDFStatementParser
from src.services.statement_ai_service import (
    FrequencyType,
    PaymentTypeClassification,
    StatementAIService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["statement-import"])


# File type mappings
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".ofx", ".qfx", ".qif"}
EXTENSION_TO_FILETYPE = {
    ".pdf": FileType.PDF,
    ".csv": FileType.CSV,
    ".ofx": FileType.OFX,
    ".qfx": FileType.QFX,
    ".qif": FileType.QIF,
}


def _get_file_type(filename: str) -> FileType | None:
    """Get FileType enum from filename extension."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_TO_FILETYPE.get(ext)


def _frequency_to_model(freq: FrequencyType) -> str:
    """Convert FrequencyType to Frequency model value."""
    mapping = {
        FrequencyType.WEEKLY: "weekly",
        FrequencyType.BIWEEKLY: "biweekly",
        FrequencyType.MONTHLY: "monthly",
        FrequencyType.QUARTERLY: "quarterly",
        FrequencyType.YEARLY: "yearly",
        FrequencyType.IRREGULAR: "monthly",  # Default to monthly
    }
    return mapping.get(freq, "monthly")


def _payment_type_to_model(ptype: PaymentTypeClassification) -> str:
    """Convert PaymentTypeClassification to PaymentType model value."""
    mapping = {
        PaymentTypeClassification.SUBSCRIPTION: "subscription",
        PaymentTypeClassification.HOUSING: "housing",
        PaymentTypeClassification.UTILITY: "utility",
        PaymentTypeClassification.INSURANCE: "insurance",
        PaymentTypeClassification.PROFESSIONAL: "professional",
        PaymentTypeClassification.DEBT: "debt",
        PaymentTypeClassification.SAVINGS: "savings",
        PaymentTypeClassification.TRANSFER: "transfer",
        PaymentTypeClassification.UNKNOWN: "subscription",
    }
    return mapping.get(ptype, "subscription")


# ============================================================================
# Upload and Process Endpoints
# ============================================================================


@router.post("/upload", response_model=StatementUploadResponse)
async def upload_statement(
    file: Annotated[UploadFile, File(description="Bank statement file")],
    bank_id: Annotated[str | None, Form()] = None,
    currency: Annotated[str, Form()] = "GBP",
    use_ai: Annotated[bool, Form()] = True,
    min_confidence: Annotated[float, Form()] = 0.5,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StatementUploadResponse:
    """Upload and process a bank statement file.

    Supported formats: PDF, CSV, OFX, QFX, QIF
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Validate file type
    file_type = _get_file_type(file.filename)
    if not file_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Create import job
    job = StatementImportJob(
        id=uuid.uuid4(),
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        bank_id=uuid.UUID(bank_id) if bank_id else None,
        currency=currency,
        status=ImportJobStatus.PROCESSING,
        processing_started_at=datetime.now(UTC),
    )
    db.add(job)
    await db.flush()

    try:
        # Parse the statement based on file type
        bank_service = BankService(db)

        if file_type == FileType.PDF:
            parser = PDFStatementParser(currency=currency)
            statement = parser.parse(BytesIO(content))
        elif file_type == FileType.CSV:
            # Get bank profile if specified
            bank_profile = None
            if bank_id:
                bank_profile = await bank_service.get_by_id(uuid.UUID(bank_id))
            parser = CSVStatementParser(
                bank_service=bank_service,
                bank_profile=bank_profile,
                currency=currency,
            )
            statement = await parser.parse_async(BytesIO(content))
        else:
            parser = OFXStatementParser(currency=currency)
            statement = parser.parse(BytesIO(content))

        # Update job with statement info
        job.total_transactions = len(statement.transactions)
        job.bank_name = statement.bank_name
        if statement.period_start:
            job.period_start = datetime.combine(statement.period_start, datetime.min.time())
        if statement.period_end:
            job.period_end = datetime.combine(statement.period_end, datetime.min.time())

        # Analyze for recurring patterns
        ai_service = StatementAIService()
        patterns = await ai_service.analyze_statement(
            statement,
            min_confidence=min_confidence,
            use_ai=use_ai,
        )

        # Get existing subscriptions for duplicate detection
        existing_subs_result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == current_user.id,
                Subscription.is_active == True,  # noqa: E712
            )
        )
        existing_subs = list(existing_subs_result.scalars().all())

        # Detect duplicates
        duplicate_detector = DuplicateDetector()

        # Create detected subscriptions
        for pattern in patterns:
            # Check for duplicates
            best_match = duplicate_detector.find_best_match(pattern, existing_subs)

            detected = DetectedSubscription(
                id=uuid.uuid4(),
                job_id=job.id,
                name=pattern.merchant_name,
                normalized_name=pattern.normalized_name,
                amount=pattern.amount,
                currency=currency,
                frequency=_frequency_to_model(pattern.frequency),
                payment_type=_payment_type_to_model(pattern.payment_type),
                confidence=pattern.confidence,
                amount_variance=pattern.amount_variance,
                transaction_count=pattern.transaction_count,
                first_seen=datetime.combine(pattern.first_seen, datetime.min.time()),
                last_seen=datetime.combine(pattern.last_seen, datetime.min.time()),
                status=DetectionStatus.PENDING,
                is_selected=True,
                sample_descriptions=pattern.sample_descriptions[:5],
                raw_data=pattern.to_dict(),
            )

            # Mark duplicates
            if best_match and best_match.similarity_score >= 0.7:
                detected.duplicate_of_id = best_match.existing_subscription.id
                detected.duplicate_similarity = best_match.similarity_score
                detected.status = DetectionStatus.DUPLICATE
                detected.is_selected = False
                job.duplicate_count += 1

            db.add(detected)

        job.detected_count = len(patterns)
        job.status = ImportJobStatus.READY
        await db.commit()

        return StatementUploadResponse(
            job_id=str(job.id),
            filename=job.filename,
            file_type=job.file_type.value,
            status=job.status.value,
            message=f"Detected {len(patterns)} potential recurring payments",
        )

    except Exception as e:
        logger.error(f"Failed to process statement: {e}")
        job.status = ImportJobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process statement: {e}",
        )


# ============================================================================
# Job Management Endpoints
# ============================================================================


@router.get("/jobs", response_model=ImportJobListResponse)
async def list_import_jobs(
    limit: int = 20,
    offset: int = 0,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobListResponse:
    """List user's import jobs."""
    query = select(StatementImportJob).where(StatementImportJob.user_id == current_user.id)

    if status_filter:
        try:
            status_enum = ImportJobStatus(status_filter)
            query = query.where(StatementImportJob.status == status_enum)
        except ValueError:
            pass

    query = query.order_by(StatementImportJob.created_at.desc())

    # Count total
    count_query = select(StatementImportJob).where(StatementImportJob.user_id == current_user.id)
    count_result = await db.execute(count_query)
    total = len(list(count_result.scalars().all()))

    # Get paginated results
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = list(result.scalars().all())

    return ImportJobListResponse(
        jobs=[ImportJobResponse.model_validate(job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobResponse:
    """Get a specific import job."""
    result = await db.execute(
        select(StatementImportJob).where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    return ImportJobResponse.model_validate(job)


@router.get("/jobs/{job_id}/status", response_model=ImportJobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobStatusResponse:
    """Get job processing status (for polling)."""
    result = await db.execute(
        select(StatementImportJob).where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    return ImportJobStatusResponse(
        id=str(job.id),
        status=job.status.value,
        detected_count=job.detected_count,
        error_message=job.error_message,
        is_ready=job.status == ImportJobStatus.READY,
    )


@router.delete("/jobs/{job_id}")
async def cancel_import_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel an import job."""
    result = await db.execute(
        select(StatementImportJob).where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    if job.status == ImportJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed job",
        )

    job.status = ImportJobStatus.CANCELLED
    job.completed_at = datetime.now(UTC)
    await db.commit()

    return {"message": "Import job cancelled", "job_id": str(job.id)}


# ============================================================================
# Preview and Detection Endpoints
# ============================================================================


@router.get("/jobs/{job_id}/preview", response_model=ImportPreviewResponse)
async def get_import_preview(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    """Get preview of detected subscriptions for review."""
    result = await db.execute(
        select(StatementImportJob)
        .options(selectinload(StatementImportJob.detected_subscriptions))
        .where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    detected = job.detected_subscriptions

    # Build summary
    selected = [d for d in detected if d.is_selected]
    duplicates = [d for d in detected if d.duplicate_of_id is not None]
    high_conf = [d for d in detected if float(d.confidence) >= 0.8]
    low_conf = [d for d in detected if float(d.confidence) < 0.5]

    total_monthly = Decimal("0")
    currencies = set()
    payment_types: dict[str, int] = {}
    frequencies: dict[str, int] = {}

    for d in selected:
        currencies.add(d.currency)
        payment_types[d.payment_type] = payment_types.get(d.payment_type, 0) + 1
        frequencies[d.frequency] = frequencies.get(d.frequency, 0) + 1
        # Normalize to monthly for total
        if d.frequency == "yearly":
            total_monthly += d.amount / 12
        elif d.frequency == "quarterly":
            total_monthly += d.amount / 3
        elif d.frequency == "weekly":
            total_monthly += d.amount * 4
        elif d.frequency == "biweekly":
            total_monthly += d.amount * 2
        else:
            total_monthly += d.amount

    summary = ImportPreviewSummary(
        total_detected=len(detected),
        selected_count=len(selected),
        duplicate_count=len(duplicates),
        high_confidence_count=len(high_conf),
        low_confidence_count=len(low_conf),
        total_monthly_amount=total_monthly.quantize(Decimal("0.01")),
        currencies=list(currencies),
        payment_types=payment_types,
        frequencies=frequencies,
    )

    return ImportPreviewResponse(
        job=ImportJobResponse.model_validate(job),
        detected_subscriptions=[DetectedSubscriptionResponse.model_validate(d) for d in detected],
        summary=summary,
    )


@router.get("/jobs/{job_id}/detected", response_model=list[DetectedSubscriptionResponse])
async def list_detected_subscriptions(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[DetectedSubscriptionResponse]:
    """List detected subscriptions for a job."""
    result = await db.execute(
        select(DetectedSubscription)
        .join(StatementImportJob)
        .where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
        .order_by(DetectedSubscription.confidence.desc())
    )
    detected = list(result.scalars().all())

    return [DetectedSubscriptionResponse.model_validate(d) for d in detected]


@router.patch("/detected/{detected_id}", response_model=DetectedSubscriptionResponse)
async def update_detected_subscription(
    detected_id: str,
    update: DetectedSubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DetectedSubscriptionResponse:
    """Update a detected subscription (selection, name, amount, etc.)."""
    result = await db.execute(
        select(DetectedSubscription)
        .join(StatementImportJob)
        .where(
            DetectedSubscription.id == uuid.UUID(detected_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    detected = result.scalar_one_or_none()

    if not detected:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detected subscription not found",
        )

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(detected, field, value)

    await db.commit()
    await db.refresh(detected)

    return DetectedSubscriptionResponse.model_validate(detected)


@router.post("/detected/bulk-update", response_model=BulkUpdateDetectedResponse)
async def bulk_update_detected(
    request: BulkUpdateDetectedRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BulkUpdateDetectedResponse:
    """Bulk update detected subscription selection."""
    ids = [uuid.UUID(sid) for sid in request.subscription_ids]

    result = await db.execute(
        select(DetectedSubscription)
        .join(StatementImportJob)
        .where(
            DetectedSubscription.id.in_(ids),
            StatementImportJob.user_id == current_user.id,
        )
    )
    detected_list = list(result.scalars().all())

    for detected in detected_list:
        if request.is_selected is not None:
            detected.is_selected = request.is_selected
        if request.status is not None:
            try:
                detected.status = DetectionStatus(request.status)
            except ValueError:
                pass

    await db.commit()

    return BulkUpdateDetectedResponse(
        updated_count=len(detected_list),
        subscription_ids=[str(d.id) for d in detected_list],
    )


# ============================================================================
# Import Confirmation Endpoints
# ============================================================================


@router.post("/jobs/{job_id}/confirm", response_model=ConfirmImportResponse)
async def confirm_import(
    job_id: str,
    request: ConfirmImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConfirmImportResponse:
    """Confirm and import selected subscriptions."""
    # Get job with detected subscriptions
    result = await db.execute(
        select(StatementImportJob)
        .options(selectinload(StatementImportJob.detected_subscriptions))
        .where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    if job.status != ImportJobStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job not ready for import. Current status: {job.status.value}",
        )

    # Get subscriptions to import
    if request.subscription_ids:
        # Specific IDs provided
        ids_to_import = set(request.subscription_ids)
        to_import = [
            d
            for d in job.detected_subscriptions
            if str(d.id) in ids_to_import and d.status != DetectionStatus.DUPLICATE
        ]
    else:
        # Import all selected
        to_import = [
            d
            for d in job.detected_subscriptions
            if d.is_selected
            and d.status not in (DetectionStatus.DUPLICATE, DetectionStatus.SKIPPED)
        ]

    created_ids: list[str] = []
    imported_count = 0
    skipped_count = 0

    for detected in to_import:
        try:
            # Create subscription
            sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name=detected.name,
                amount=detected.amount,
                currency=detected.currency,
                frequency=Frequency(detected.frequency),
                payment_type=PaymentType(detected.payment_type),
                is_active=True,
                card_id=request.card_id,
                category_id=request.category_id,
            )
            db.add(sub)

            # Update detected subscription
            detected.status = DetectionStatus.IMPORTED
            detected.created_subscription_id = sub.id
            created_ids.append(sub.id)
            imported_count += 1

        except Exception as e:
            logger.warning(f"Failed to import subscription {detected.name}: {e}")
            detected.status = DetectionStatus.SKIPPED
            skipped_count += 1

    # Update job
    job.imported_count = imported_count
    job.skipped_count = skipped_count
    job.status = ImportJobStatus.COMPLETED
    job.completed_at = datetime.now(UTC)

    await db.commit()

    return ConfirmImportResponse(
        job_id=str(job.id),
        imported_count=imported_count,
        skipped_count=skipped_count,
        duplicate_count=job.duplicate_count,
        created_subscription_ids=created_ids,
    )


# ============================================================================
# Duplicate Detection Endpoints
# ============================================================================


@router.get("/jobs/{job_id}/duplicates", response_model=DuplicateCheckResponse)
async def check_duplicates(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DuplicateCheckResponse:
    """Get all duplicate matches for a job."""
    result = await db.execute(
        select(DetectedSubscription)
        .join(StatementImportJob)
        .where(
            StatementImportJob.id == uuid.UUID(job_id),
            StatementImportJob.user_id == current_user.id,
            DetectedSubscription.duplicate_of_id.isnot(None),
        )
    )
    duplicates = list(result.scalars().all())

    matches: list[DuplicateMatch] = []
    for d in duplicates:
        # Get the existing subscription
        existing_result = await db.execute(
            select(Subscription).where(Subscription.id == d.duplicate_of_id)
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            matches.append(
                DuplicateMatch(
                    detected_id=str(d.id),
                    detected_name=d.name,
                    existing_id=str(existing.id),
                    existing_name=existing.name,
                    similarity=float(d.duplicate_similarity) if d.duplicate_similarity else 0.0,
                    match_reasons=["Name similarity", "Amount match"],
                )
            )

    return DuplicateCheckResponse(
        duplicates=matches,
        total_matches=len(matches),
    )
