"""Calendar and payment history API endpoints.

This module provides API endpoints for calendar view, payment history,
and payment recording functionality.

All endpoints use async/await for non-blocking I/O operations.
"""

import logging
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.dependencies import get_db
from src.models.subscription import PaymentStatus
from src.schemas.subscription import CalendarEvent, MonthlyPaymentsSummary, PaymentHistoryResponse
from src.services.currency_service import CurrencyService
from src.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter()


class RecordPaymentRequest(BaseModel):
    """Request body for recording a payment.

    Attributes:
        payment_date: Date of the payment.
        amount: Payment amount.
        status: Payment status (default: completed).
        payment_method: Optional payment method used.
        notes: Optional notes about the payment.
    """

    payment_date: date = Field(..., description="Date of the payment")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    status: PaymentStatus = Field(default=PaymentStatus.COMPLETED, description="Payment status")
    payment_method: str | None = Field(default=None, description="Payment method")
    notes: str | None = Field(default=None, description="Payment notes")


class MonthlySummaryResponse(BaseModel):
    """Response for monthly payment summary.

    Attributes:
        year: Year of the summary.
        month: Month of the summary.
        total_paid: Total amount paid.
        total_pending: Total pending amount.
        total_failed: Total failed amount.
        payment_count: Total number of payments.
        completed_count: Number of completed payments.
        pending_count: Number of pending payments.
        failed_count: Number of failed payments.
    """

    year: int
    month: int
    total_paid: Decimal
    total_pending: Decimal
    total_failed: Decimal
    payment_count: int
    completed_count: int
    pending_count: int
    failed_count: int


@router.get("/events", response_model=list[CalendarEvent])
async def get_calendar_events(
    start_date: date = Query(..., description="Start date for calendar range"),
    end_date: date = Query(..., description="End date for calendar range"),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarEvent]:
    """Get payment events for calendar view.

    Retrieves all scheduled payment events for active subscriptions
    within the specified date range.

    Args:
        start_date: Start of the date range.
        end_date: End of the date range.
        db: Database session (injected).

    Returns:
        List of CalendarEvent objects for the date range.

    Example:
        GET /api/calendar/events?start_date=2025-01-01&end_date=2025-01-31
    """
    logger.info(f"[API] GET /calendar/events?start_date={start_date}&end_date={end_date}")

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date",
        )

    service = PaymentService(db)
    events = await service.get_calendar_events(start_date, end_date)
    logger.info(
        f"[API] Returning {len(events)} events, is_paid counts: "
        f"paid={sum(1 for e in events if e.is_paid)}, "
        f"unpaid={sum(1 for e in events if not e.is_paid)}"
    )
    return events


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    year: int = Query(..., ge=2020, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db),
) -> MonthlySummaryResponse:
    """Get payment summary for a specific month.

    Aggregates payment data for the specified month including
    totals, counts, and status breakdown.

    Args:
        year: Year to query.
        month: Month to query (1-12).
        db: Database session (injected).

    Returns:
        Monthly payment summary.

    Example:
        GET /api/calendar/monthly-summary?year=2025&month=1
    """
    service = PaymentService(db)
    summary = await service.get_monthly_summary(year, month)
    return MonthlySummaryResponse(**summary)


@router.get("/payments/{subscription_id}", response_model=list[PaymentHistoryResponse])
async def get_payment_history(
    subscription_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum records"),
    offset: int = Query(default=0, ge=0, description="Records to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[PaymentHistoryResponse]:
    """Get payment history for a subscription.

    Retrieves payment records for the specified subscription,
    ordered by payment date descending.

    Args:
        subscription_id: UUID of the subscription.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
        db: Database session (injected).

    Returns:
        List of PaymentHistoryResponse records.

    Example:
        GET /api/calendar/payments/uuid-string?limit=10
    """
    service = PaymentService(db)
    history = await service.get_payment_history(subscription_id, limit, offset)
    return [PaymentHistoryResponse.model_validate(p) for p in history]


@router.post("/payments/{subscription_id}", response_model=PaymentHistoryResponse)
async def record_payment(
    subscription_id: str,
    request: RecordPaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentHistoryResponse:
    """Record a payment for a subscription.

    Creates a payment history record and updates the subscription.
    For installment payments, automatically tracks progress.

    Args:
        subscription_id: UUID of the subscription.
        request: Payment details.
        db: Database session (injected).

    Returns:
        The created PaymentHistoryResponse record.

    Raises:
        HTTPException 404: If subscription not found.

    Example:
        POST /api/calendar/payments/uuid-string
        {
            "payment_date": "2025-01-15",
            "amount": "15.99",
            "status": "completed"
        }
    """
    logger.info(
        f"[API] POST /calendar/payments/{subscription_id} - "
        f"date={request.payment_date}, amount={request.amount}, status={request.status}"
    )

    service = PaymentService(db)

    try:
        payment = await service.record_payment(
            subscription_id=subscription_id,
            payment_date=request.payment_date,
            amount=request.amount,
            status=request.status,
            payment_method=request.payment_method,
            notes=request.notes,
        )
        await db.commit()
        logger.info(f"[API] Payment recorded successfully: id={payment.id}")
        return PaymentHistoryResponse.model_validate(payment)
    except ValueError as e:
        logger.error(f"[API] Payment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete("/payments/{subscription_id}/{payment_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    subscription_id: str,
    payment_date: date,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a payment record (unmark as paid).

    Removes the payment history record for a specific subscription and date.
    This allows users to undo an accidental payment marking.

    Args:
        subscription_id: UUID of the subscription.
        payment_date: Date of the payment to delete.
        db: Database session (injected).

    Raises:
        HTTPException 404: If payment not found.

    Example:
        DELETE /api/calendar/payments/uuid-string/2025-01-15
    """
    logger.info(f"[API] DELETE /calendar/payments/{subscription_id}/{payment_date}")

    service = PaymentService(db)

    try:
        await service.delete_payment(subscription_id, payment_date)
        await db.commit()
        logger.info("[API] Payment deleted successfully")
    except ValueError as e:
        logger.error(f"[API] Delete payment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/payments-summary", response_model=MonthlyPaymentsSummary)
async def get_monthly_payments_summary(
    currency: str = Query(default="GBP", description="Target currency for totals"),
    db: AsyncSession = Depends(get_db),
) -> MonthlyPaymentsSummary:
    """Get unified monthly payments summary for current and next month.

    This is the single source of truth for monthly payment totals used by both
    the Calendar and Cards dashboard components. Returns totals for current month
    (total, paid, remaining) and next month total, all converted to the
    requested display currency.

    Args:
        currency: Target currency code for totals (default: GBP).
        db: Database session (injected).

    Returns:
        MonthlyPaymentsSummary with current and next month totals.

    Example:
        GET /api/calendar/payments-summary
        GET /api/calendar/payments-summary?currency=USD
    """
    logger.info(f"[API] GET /calendar/payments-summary?currency={currency}")

    service = PaymentService(db)
    currency_service = CurrencyService(api_key=settings.exchange_rate_api_key or None)

    summary = await service.get_monthly_payments_summary(
        currency=currency,
        currency_service=currency_service,
    )

    return MonthlyPaymentsSummary(**summary)
