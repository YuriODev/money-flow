"""Subscription CRUD API endpoints.

This module provides RESTful API endpoints for subscription management,
including listing, creating, updating, deleting, and import/export of subscriptions.

All endpoints use async/await for non-blocking I/O operations.
"""

import csv
import io
import json
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.core.config import settings
from src.core.dependencies import get_db
from src.models.subscription import Frequency, PaymentMode, PaymentType
from src.models.user import User
from src.schemas.subscription import (
    ExportData,
    ImportResult,
    SubscriptionCreate,
    SubscriptionExport,
    SubscriptionResponse,
    SubscriptionSummary,
    SubscriptionUpdate,
)
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.currency_service import CurrencyService
from src.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[SubscriptionResponse])
@limiter.limit(rate_limit_get)
async def list_subscriptions(
    request: Request,
    is_active: bool | None = None,
    category: str | None = None,
    payment_type: PaymentType | None = Query(
        default=None, description="Filter by payment type (deprecated, use payment_mode)"
    ),
    payment_mode: PaymentMode | None = Query(
        default=None, description="Filter by payment mode (recurring, one_time, debt, savings)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SubscriptionResponse]:
    """List all subscriptions/payments with optional filters.

    Retrieves all payments from the database with optional filtering
    by active status, category, payment type, and/or payment mode.
    Results are ordered by next payment date.

    Args:
        is_active: Filter by active status. If not provided, returns all.
        category: Filter by subcategory name. If not provided, returns all categories.
        payment_type: Filter by payment type (deprecated, use payment_mode).
        payment_mode: Filter by payment mode (recurring, one_time, debt, savings).
        db: Database session (injected by dependency).
        current_user: Authenticated user (injected by dependency).

    Returns:
        List of SubscriptionResponse objects matching the filters.

    Example:
        GET /api/subscriptions
        GET /api/subscriptions?is_active=true
        GET /api/subscriptions?payment_mode=debt
        GET /api/subscriptions?category=entertainment
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    subscriptions = await service.get_all(
        is_active=is_active,
        category=category,
        payment_type=payment_type,
        payment_mode=payment_mode,
    )
    return [SubscriptionResponse.model_validate(s) for s in subscriptions]


@router.get("/summary", response_model=SubscriptionSummary)
@limiter.limit(rate_limit_get)
async def get_summary(
    request: Request,
    payment_type: PaymentType | None = Query(
        default=None, description="Filter summary by payment type"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionSummary:
    """Get spending summary for all active subscriptions/payments.

    Calculates and returns comprehensive spending analytics including
    total monthly and yearly costs, breakdown by category and payment type,
    and upcoming payments. All amounts are converted to the default currency (GBP).

    Includes Money Flow totals:
    - total_debt: Sum of all remaining debt balances
    - total_savings_target: Sum of all savings goals
    - total_current_saved: Sum of all current savings

    Args:
        payment_type: Optional filter for specific payment type.
        db: Database session (injected by dependency).
        current_user: Authenticated user (injected by dependency).

    Returns:
        SubscriptionSummary with total costs, breakdowns, and upcoming payments.

    Example:
        GET /api/subscriptions/summary
        GET /api/subscriptions/summary?payment_type=debt
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    currency_service = CurrencyService(api_key=settings.exchange_rate_api_key or None)
    return await service.get_summary(currency_service=currency_service, payment_type=payment_type)


@router.get("/exchange-rates", response_model=dict)
@limiter.limit(rate_limit_get)
async def get_exchange_rates(
    request: Request,
) -> dict:
    """Get current exchange rates (USD-based).

    Fetches live exchange rates from the currency API.
    Rates are relative to USD (1 USD = X currency).

    Returns:
        Dictionary with "rates" containing currency code to rate mapping.

    Example:
        GET /api/subscriptions/exchange-rates
        Returns: {"rates": {"USD": 1.0, "GBP": 0.79, "EUR": 0.92, ...}}
    """
    currency_service = CurrencyService(api_key=settings.exchange_rate_api_key or None)
    try:
        rates = await currency_service._get_rates()
        # Convert Decimal to float for JSON serialization
        float_rates = {code: float(rate) for code, rate in rates.items()}
        return {"rates": float_rates, "base": "USD"}
    except Exception as e:
        logger.error(f"Failed to fetch exchange rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch exchange rates",
        )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
@limiter.limit(rate_limit_get)
async def get_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionResponse:
    """Get a single subscription by ID.

    Retrieves detailed information about a specific subscription.

    Args:
        subscription_id: UUID of the subscription to retrieve.
        db: Database session (injected by dependency).

    Returns:
        SubscriptionResponse with full subscription details.

    Raises:
        HTTPException 404: If subscription not found.

    Example:
        GET /api/subscriptions/123e4567-e89b-12d3-a456-426614174000
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    subscription = await service.get_by_id(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    return SubscriptionResponse.model_validate(subscription)


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(rate_limit_write)
async def create_subscription(
    request: Request,
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionResponse:
    """Create a new subscription.

    Creates a new subscription record with automatically calculated
    next payment date based on start date and frequency.

    Args:
        data: Subscription creation data including name, amount, currency,
            frequency, and start date.
        db: Database session (injected by dependency).

    Returns:
        SubscriptionResponse with the created subscription details.

    Raises:
        HTTPException 422: If validation fails.

    Example:
        POST /api/subscriptions
        {
            "name": "Netflix",
            "amount": "15.99",
            "currency": "GBP",
            "frequency": "MONTHLY",
            "start_date": "2025-01-01"
        }
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    subscription = await service.create(data)
    return SubscriptionResponse.model_validate(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
@limiter.limit(rate_limit_write)
async def update_subscription(
    request: Request,
    subscription_id: str,
    data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionResponse:
    """Update an existing subscription.

    Updates a subscription with the provided data. Only fields that are
    explicitly set will be updated (partial update supported).

    Args:
        subscription_id: UUID of the subscription to update.
        data: Update data. Only include fields you want to change.
        db: Database session (injected by dependency).

    Returns:
        SubscriptionResponse with the updated subscription details.

    Raises:
        HTTPException 404: If subscription not found.
        HTTPException 422: If validation fails.

    Example:
        PUT /api/subscriptions/123e4567-e89b-12d3-a456-426614174000
        {
            "amount": "19.99"
        }
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    subscription = await service.update(subscription_id, data)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    return SubscriptionResponse.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_limit_write)
async def delete_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a subscription.

    Permanently removes a subscription from the database.

    Args:
        subscription_id: UUID of the subscription to delete.
        db: Database session (injected by dependency).

    Raises:
        HTTPException 404: If subscription not found.

    Example:
        DELETE /api/subscriptions/123e4567-e89b-12d3-a456-426614174000
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    deleted = await service.delete(subscription_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )


# ============================================================================
# Import/Export Endpoints
# ============================================================================


@router.get("/export/json", response_model=ExportData)
@limiter.limit(rate_limit_get)
async def export_subscriptions_json(
    request: Request,
    include_inactive: bool = Query(default=True, description="Include inactive payments"),
    payment_type: PaymentType | None = Query(default=None, description="Filter by payment type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExportData:
    """Export all subscriptions/payments as JSON.

    Exports payment data in a format suitable for backup or transfer.
    The export includes metadata (version 2.0, timestamp) and all payment fields
    including Money Flow fields (payment_type, debt, savings).

    Args:
        include_inactive: Whether to include inactive payments.
        payment_type: Optional filter for specific payment type.
        db: Database session (injected by dependency).

    Returns:
        ExportData with all payments.

    Example:
        GET /api/subscriptions/export/json
        GET /api/subscriptions/export/json?include_inactive=false
        GET /api/subscriptions/export/json?payment_type=debt
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    is_active = None if include_inactive else True
    subscriptions = await service.get_all(is_active=is_active, payment_type=payment_type)

    # Helper to format Decimal for JSON - distinguishes null from zero
    def format_decimal_json(value: Decimal | None) -> str | None:
        """Format Decimal for JSON export, preserving null vs zero distinction."""
        if value is None:
            return None
        return str(value)

    export_subs = []
    for sub in subscriptions:
        export_subs.append(
            SubscriptionExport(
                name=sub.name,
                amount=str(sub.amount),
                currency=sub.currency,
                frequency=sub.frequency.value,
                frequency_interval=sub.frequency_interval,
                start_date=sub.start_date.isoformat(),
                next_payment_date=sub.next_payment_date.isoformat(),
                payment_type=sub.payment_type.value,
                payment_mode=sub.payment_mode.value if sub.payment_mode else "recurring",
                category=sub.category,
                notes=sub.notes,
                is_active=sub.is_active,
                payment_method=sub.payment_method,
                reminder_days=sub.reminder_days,
                icon_url=sub.icon_url,
                color=sub.color,
                auto_renew=sub.auto_renew,
                is_installment=sub.is_installment,
                total_installments=sub.total_installments,
                completed_installments=sub.completed_installments,
                # Debt-specific fields - use format_decimal_json to preserve 0 vs null
                total_owed=format_decimal_json(sub.total_owed),
                remaining_balance=format_decimal_json(sub.remaining_balance),
                creditor=sub.creditor,
                # Savings-specific fields - use format_decimal_json to preserve 0 vs null
                target_amount=format_decimal_json(sub.target_amount),
                current_saved=format_decimal_json(sub.current_saved),
                recipient=sub.recipient,
            )
        )

    return ExportData(
        version="2.0",
        exported_at=datetime.utcnow(),
        subscription_count=len(export_subs),
        subscriptions=export_subs,
    )


@router.get("/export/csv")
@limiter.limit(rate_limit_get)
async def export_subscriptions_csv(
    request: Request,
    include_inactive: bool = Query(default=True, description="Include inactive payments"),
    payment_type: PaymentType | None = Query(default=None, description="Filter by payment type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Export all subscriptions/payments as CSV.

    Exports payment data in CSV format for spreadsheet applications.
    Headers are included in the first row. Includes Money Flow fields.

    Args:
        include_inactive: Whether to include inactive payments.
        payment_type: Optional filter for specific payment type.
        db: Database session (injected by dependency).

    Returns:
        CSV file download response.

    Example:
        GET /api/subscriptions/export/csv
        GET /api/subscriptions/export/csv?payment_type=debt
    """
    service = SubscriptionService(db, user_id=str(current_user.id))
    is_active = None if include_inactive else True
    subscriptions = await service.get_all(is_active=is_active, payment_type=payment_type)

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header (Money Flow v2.1 format with payment_mode)
    writer.writerow(
        [
            "name",
            "amount",
            "currency",
            "frequency",
            "frequency_interval",
            "start_date",
            "next_payment_date",
            "payment_type",
            "payment_mode",
            "category",
            "notes",
            "is_active",
            "payment_method",
            "reminder_days",
            "icon_url",
            "color",
            "auto_renew",
            "is_installment",
            "total_installments",
            "completed_installments",
            # Debt-specific fields
            "total_owed",
            "remaining_balance",
            "creditor",
            # Savings-specific fields
            "target_amount",
            "current_saved",
            "recipient",
        ]
    )

    # Helper to format Decimal for CSV - distinguishes null from zero
    def format_decimal(value: Decimal | None) -> str:
        """Format Decimal for CSV export, preserving null vs zero distinction."""
        if value is None:
            return ""
        return str(value)

    # Write data rows
    for sub in subscriptions:
        writer.writerow(
            [
                sub.name,
                str(sub.amount),
                sub.currency,
                sub.frequency.value,
                sub.frequency_interval,
                sub.start_date.isoformat(),
                sub.next_payment_date.isoformat(),
                sub.payment_type.value,
                sub.payment_mode.value if sub.payment_mode else "recurring",
                sub.category or "",
                sub.notes or "",
                str(sub.is_active).lower(),
                sub.payment_method or "",
                sub.reminder_days,
                sub.icon_url or "",
                sub.color,
                str(sub.auto_renew).lower(),
                str(sub.is_installment).lower(),
                sub.total_installments if sub.total_installments is not None else "",
                sub.completed_installments,
                # Debt-specific fields - use format_decimal to preserve 0 vs null
                format_decimal(sub.total_owed),
                format_decimal(sub.remaining_balance),
                sub.creditor or "",
                # Savings-specific fields - use format_decimal to preserve 0 vs null
                format_decimal(sub.target_amount),
                format_decimal(sub.current_saved),
                sub.recipient or "",
            ]
        )

    csv_content = output.getvalue()
    filename = f"payments_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/pdf")
@limiter.limit(rate_limit_get)
async def export_subscriptions_pdf(
    request: Request,
    include_inactive: bool = Query(default=False, description="Include inactive payments"),
    payment_type: PaymentType | None = Query(default=None, description="Filter by payment type"),
    page_size: str = Query(default="a4", description="Page size (a4 or letter)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Export all subscriptions/payments as a PDF report.

    Generates a professional PDF report with:
    - Summary statistics (monthly/yearly totals)
    - Spending breakdown by category
    - Upcoming payments (next 30 days)
    - Complete payments table

    Args:
        include_inactive: Whether to include inactive payments.
        payment_type: Optional filter for specific payment type.
        page_size: Page size for the PDF ('a4' or 'letter').
        db: Database session (injected by dependency).
        current_user: Authenticated user (injected by dependency).

    Returns:
        PDF file download response.

    Example:
        GET /api/subscriptions/export/pdf
        GET /api/subscriptions/export/pdf?include_inactive=true
        GET /api/subscriptions/export/pdf?page_size=letter
    """
    from src.services.pdf_report_service import PDFReportService

    service = SubscriptionService(db, user_id=str(current_user.id))
    is_active = None if include_inactive else True
    subscriptions = await service.get_all(is_active=is_active, payment_type=payment_type)

    # Generate PDF report
    pdf_service = PDFReportService(
        page_size=page_size,
        include_inactive=include_inactive,
        currency=settings.default_currency,
    )
    pdf_content = pdf_service.generate_report(
        subscriptions=subscriptions,
        user_email=current_user.email,
        report_title="Money Flow Report",
    )

    filename = f"money_flow_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import/json", response_model=ImportResult)
@limiter.limit(rate_limit_write)
async def import_subscriptions_json(
    request: Request,
    file: UploadFile = File(..., description="JSON file to import"),
    skip_duplicates: bool = Query(default=True, description="Skip subscriptions with same name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ImportResult:
    """Import subscriptions from JSON file.

    Imports subscriptions from an export JSON file. Can skip duplicates
    or fail on duplicate names.

    Args:
        file: Uploaded JSON file.
        skip_duplicates: Skip if subscription with same name exists.
        db: Database session (injected by dependency).

    Returns:
        ImportResult with counts and any errors.

    Raises:
        HTTPException 400: If file is invalid or parsing fails.

    Example:
        POST /api/subscriptions/import/json
        Content-Type: multipart/form-data
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file",
        )

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {e}",
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )

    # Validate structure
    if "subscriptions" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format: missing 'subscriptions' key",
        )

    return await _import_subscriptions(
        data["subscriptions"], skip_duplicates, db, str(current_user.id)
    )


@router.post("/import/csv", response_model=ImportResult)
@limiter.limit(rate_limit_write)
async def import_subscriptions_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV file to import"),
    skip_duplicates: bool = Query(default=True, description="Skip subscriptions with same name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ImportResult:
    """Import subscriptions from CSV file.

    Imports subscriptions from a CSV file. First row must be headers.
    Can skip duplicates or fail on duplicate names.

    Args:
        file: Uploaded CSV file.
        skip_duplicates: Skip if subscription with same name exists.
        db: Database session (injected by dependency).

    Returns:
        ImportResult with counts and any errors.

    Raises:
        HTTPException 400: If file is invalid or parsing fails.

    Example:
        POST /api/subscriptions/import/csv
        Content-Type: multipart/form-data
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )

    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )

    reader = csv.DictReader(io.StringIO(text))
    subscriptions = list(reader)

    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no data rows",
        )

    return await _import_subscriptions(subscriptions, skip_duplicates, db, str(current_user.id))


async def _import_subscriptions(
    subscriptions: list[dict],
    skip_duplicates: bool,
    db: AsyncSession,
    user_id: str,
) -> ImportResult:
    """Import subscriptions/payments from parsed data.

    Supports both v1.0 (subscriptions only) and v2.0 (Money Flow) formats.

    Args:
        subscriptions: List of payment dictionaries.
        skip_duplicates: Whether to skip duplicates.
        db: Database session.
        user_id: ID of the user to import subscriptions for.

    Returns:
        ImportResult with counts and errors.
    """
    service = SubscriptionService(db, user_id=user_id)
    existing = await service.get_all()
    existing_names = {s.name.lower() for s in existing}

    result = ImportResult(
        total=len(subscriptions),
        imported=0,
        skipped=0,
        failed=0,
        errors=[],
    )

    for i, sub_data in enumerate(subscriptions):
        try:
            name = sub_data.get("name", "").strip()
            if not name:
                result.failed += 1
                result.errors.append(f"Row {i + 1}: Missing name")
                continue

            # Check for duplicates
            if name.lower() in existing_names:
                if skip_duplicates:
                    result.skipped += 1
                    continue
                else:
                    result.failed += 1
                    result.errors.append(f"Row {i + 1}: Duplicate name '{name}'")
                    continue

            # Parse amount
            try:
                amount = Decimal(sub_data.get("amount", "0"))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except (InvalidOperation, ValueError) as e:
                result.failed += 1
                result.errors.append(f"Row {i + 1}: Invalid amount - {e}")
                continue

            # Parse frequency (accept both upper and lower case)
            freq_str = sub_data.get("frequency", "monthly").lower()
            try:
                frequency = Frequency(freq_str)
            except ValueError:
                result.failed += 1
                result.errors.append(f"Row {i + 1}: Invalid frequency '{freq_str}'")
                continue

            # Parse start_date
            start_date_str = sub_data.get("start_date", "")
            try:
                if start_date_str:
                    start_date_val = date.fromisoformat(start_date_str)
                else:
                    start_date_val = date.today()
            except ValueError:
                result.failed += 1
                result.errors.append(f"Row {i + 1}: Invalid start_date '{start_date_str}'")
                continue

            # Parse boolean fields
            def parse_bool(value: str | bool) -> bool:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes")

            # Parse optional Decimal fields
            def parse_decimal(value: str | None) -> Decimal | None:
                if not value or str(value).strip() == "":
                    return None
                try:
                    return Decimal(str(value))
                except InvalidOperation:
                    return None

            # Parse payment_type (Money Flow v2.0 field, deprecated)
            payment_type_str = sub_data.get("payment_type", "subscription").lower()
            try:
                payment_type_val = PaymentType(payment_type_str)
            except ValueError:
                # Default to subscription for unknown types
                payment_type_val = PaymentType.SUBSCRIPTION

            # Parse payment_mode (Money Flow v2.1 field)
            payment_mode_str = sub_data.get("payment_mode", "recurring").lower()
            try:
                payment_mode_val = PaymentMode(payment_mode_str)
            except ValueError:
                # Default to recurring for unknown modes
                payment_mode_val = PaymentMode.RECURRING

            # Create subscription/payment
            create_data = SubscriptionCreate(
                name=name,
                amount=amount,
                currency=sub_data.get("currency", "GBP"),
                frequency=frequency,
                frequency_interval=int(sub_data.get("frequency_interval", 1)),
                start_date=start_date_val,
                payment_type=payment_type_val,
                payment_mode=payment_mode_val,
                category=sub_data.get("category") or None,
                notes=sub_data.get("notes") or None,
                payment_method=sub_data.get("payment_method") or None,
                reminder_days=int(sub_data.get("reminder_days", 3)),
                icon_url=sub_data.get("icon_url") or None,
                color=sub_data.get("color", "#3B82F6"),
                auto_renew=parse_bool(sub_data.get("auto_renew", True)),
                is_installment=parse_bool(sub_data.get("is_installment", False)),
                total_installments=int(sub_data["total_installments"])
                if sub_data.get("total_installments")
                else None,
                # Debt-specific fields (Money Flow v2.0)
                total_owed=parse_decimal(sub_data.get("total_owed")),
                remaining_balance=parse_decimal(sub_data.get("remaining_balance")),
                creditor=sub_data.get("creditor") or None,
                # Savings-specific fields (Money Flow v2.0)
                target_amount=parse_decimal(sub_data.get("target_amount")),
                current_saved=parse_decimal(sub_data.get("current_saved")),
                recipient=sub_data.get("recipient") or None,
            )

            await service.create(create_data)
            existing_names.add(name.lower())
            result.imported += 1

        except Exception as e:
            result.failed += 1
            result.errors.append(f"Row {i + 1}: {e}")
            logger.exception(f"Failed to import payment row {i + 1}")

    return result
