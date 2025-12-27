"""Calendar and payment history API endpoints.

This module provides API endpoints for calendar view, payment history,
payment recording functionality, iCal feed generation, and Google Calendar
OAuth integration.

All endpoints use async/await for non-blocking I/O operations.

Sprint 5.6 - Added iCal feed generation and Google Calendar OAuth endpoints.
"""

import hashlib
import logging
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.config import settings
from src.core.dependencies import get_db
from src.models.subscription import PaymentStatus, Subscription
from src.models.user import User
from src.schemas.subscription import CalendarEvent, MonthlyPaymentsSummary, PaymentHistoryResponse
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.currency_service import CurrencyService
from src.services.google_calendar_service import GoogleCalendarService
from src.services.ical_service import ICalService
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
@limiter.limit(rate_limit_get)
async def get_calendar_events(
    request: Request,
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
@limiter.limit(rate_limit_get)
async def get_monthly_summary(
    request: Request,
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
@limiter.limit(rate_limit_get)
async def get_payment_history(
    request: Request,
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
@limiter.limit(rate_limit_write)
async def record_payment(
    request: Request,
    subscription_id: str,
    payment_request: RecordPaymentRequest,
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
        f"date={payment_request.payment_date}, amount={payment_request.amount}, status={payment_request.status}"
    )

    service = PaymentService(db)

    try:
        payment = await service.record_payment(
            subscription_id=subscription_id,
            payment_date=payment_request.payment_date,
            amount=payment_request.amount,
            status=payment_request.status,
            payment_method=payment_request.payment_method,
            notes=payment_request.notes,
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
@limiter.limit(rate_limit_write)
async def delete_payment(
    request: Request,
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
@limiter.limit(rate_limit_get)
async def get_monthly_payments_summary(
    request: Request,
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


# =============================================================================
# iCal Feed Endpoints (Sprint 5.6)
# =============================================================================


class CalendarFeedResponse(BaseModel):
    """Response containing calendar feed information."""

    feed_url: str = Field(description="The iCal feed URL (use your server's base URL)")
    webcal_url: str = Field(description="The webcal:// URL for one-click subscribe")
    token: str = Field(description="The feed authentication token")
    feed_path: str = Field(description="The path portion of the feed URL")
    instructions: dict[str, str] = Field(description="Setup instructions for various apps")


class CalendarPreviewEvent(BaseModel):
    """A single event in the calendar preview."""

    id: str
    title: str
    date: str | None
    amount: float
    currency: str
    frequency: str
    payment_type: str | None


class CalendarPreviewResponse(BaseModel):
    """Response for calendar preview."""

    events: list[CalendarPreviewEvent]
    total: int
    days_ahead: int
    generated_at: str


def _generate_user_token(user_id: UUID) -> str:
    """Generate a deterministic token for a user.

    This creates a stable token based on user_id that can be used
    to authenticate calendar feed requests.

    Args:
        user_id: The user's UUID.

    Returns:
        str: A 32-character token.
    """
    return hashlib.sha256(f"{user_id}-ical-feed-v1".encode()).hexdigest()[:32]


@router.get("/ical/feed-url", response_model=CalendarFeedResponse)
@limiter.limit(rate_limit_get)
async def get_ical_feed_url(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CalendarFeedResponse:
    """Get the iCal feed URL for the current user.

    Returns the feed URL along with setup instructions for various
    calendar applications.

    Returns:
        CalendarFeedResponse: Feed URL and setup instructions.
    """
    token = _generate_user_token(current_user.id)

    # Build the feed path
    feed_path = f"/api/v1/calendar/ical/feed/{current_user.id}/{token}/payments.ics"

    # Try to determine base URL from request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    base_url = f"{scheme}://{host}"

    feed_url = f"{base_url}{feed_path}"
    webcal_host = host.replace("https://", "").replace("http://", "")
    webcal_url = f"webcal://{webcal_host}{feed_path}"

    instructions = {
        "google_calendar": (
            "1. Open Google Calendar\n"
            "2. Click '+' next to 'Other calendars'\n"
            "3. Select 'From URL'\n"
            "4. Paste the feed URL"
        ),
        "apple_calendar": (
            "1. Open Calendar app\n"
            "2. File > New Calendar Subscription\n"
            "3. Paste the feed URL\n"
            "4. Click Subscribe"
        ),
        "outlook": (
            "1. Open Outlook Calendar\n"
            "2. Add Calendar > From Internet\n"
            "3. Paste the feed URL\n"
            "4. Click Import"
        ),
        "one_click": (
            "Click the webcal:// URL to automatically open your default calendar app and subscribe."
        ),
    }

    return CalendarFeedResponse(
        feed_url=feed_url,
        webcal_url=webcal_url,
        token=token,
        feed_path=feed_path,
        instructions=instructions,
    )


@router.get("/ical/feed/{user_id}/{token}/payments.ics")
async def get_ical_feed(
    user_id: UUID,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: Annotated[bool, Query()] = False,
    days_ahead: Annotated[int, Query(ge=30, le=730)] = 365,
    payment_types: Annotated[str | None, Query()] = None,
) -> Response:
    """Get the iCal feed for a user's subscriptions.

    This endpoint is publicly accessible but requires a valid token.
    The token is generated per-user and provides read-only access
    to the calendar feed.

    Args:
        user_id: The user's UUID.
        token: The authentication token.
        include_inactive: Include inactive subscriptions.
        days_ahead: Number of days of future events to include.
        payment_types: Comma-separated list of payment types to include.

    Returns:
        Response: The iCal file content with appropriate headers.

    Raises:
        HTTPException: 403 if token is invalid.
    """
    # Validate token
    expected_token = _generate_user_token(user_id)
    if token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid feed token")

    # Parse payment types
    types_list = None
    if payment_types:
        types_list = [t.strip() for t in payment_types.split(",")]

    # Generate feed
    service = ICalService(db, user_id)
    ical_content = await service.generate_feed(
        include_inactive=include_inactive,
        days_ahead=days_ahead,
        payment_types=types_list,
    )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=moneyflow-payments.ics",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/ical/preview", response_model=CalendarPreviewResponse)
@limiter.limit(rate_limit_get)
async def preview_ical_events(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days_ahead: Annotated[int, Query(ge=7, le=90)] = 30,
    payment_types: Annotated[str | None, Query()] = None,
) -> CalendarPreviewResponse:
    """Preview upcoming calendar events without generating a full feed.

    Returns a JSON preview of what events would appear in the calendar.

    Args:
        days_ahead: Number of days to preview (max 90).
        payment_types: Comma-separated list of payment types.

    Returns:
        CalendarPreviewResponse: Preview of upcoming events.
    """
    # Parse payment types
    types_list = None
    if payment_types:
        types_list = [t.strip() for t in payment_types.split(",")]

    # Build query - convert UUID to string for comparison with String(36) column
    user_id_str = str(current_user.id)
    query = (
        select(Subscription)
        .where(Subscription.user_id == user_id_str)
        .where(Subscription.is_active == True)  # noqa: E712
        .where(Subscription.next_payment_date != None)  # noqa: E711
        .where(Subscription.next_payment_date <= datetime.now().date() + timedelta(days=days_ahead))
        .order_by(Subscription.next_payment_date)
    )

    if types_list:
        query = query.where(Subscription.payment_type.in_(types_list))

    result = await db.execute(query)
    subscriptions = result.scalars().all()

    events = []
    for sub in subscriptions:
        events.append(
            CalendarPreviewEvent(
                id=str(sub.id),
                title=f"💰 {sub.service_name}",
                date=sub.next_payment_date.isoformat() if sub.next_payment_date else None,
                amount=float(sub.amount),
                currency=sub.currency,
                frequency=sub.frequency,
                payment_type=sub.payment_type,
            )
        )

    return CalendarPreviewResponse(
        events=events,
        total=len(events),
        days_ahead=days_ahead,
        generated_at=datetime.utcnow().isoformat(),
    )


# =============================================================================
# Google Calendar OAuth Endpoints (Sprint 5.6)
# =============================================================================

# In-memory state storage for OAuth CSRF protection
# In production, use Redis or database for state management
_oauth_states: dict[str, str] = {}


class GoogleCalendarStatusResponse(BaseModel):
    """Response for Google Calendar connection status."""

    connected: bool = Field(description="Whether Google Calendar is connected")
    status: str = Field(description="Connection status")
    calendar_id: str | None = Field(default=None, description="Selected calendar ID")
    sync_enabled: bool | None = Field(default=None, description="Whether sync is enabled")
    last_sync_at: str | None = Field(default=None, description="Last sync timestamp")
    last_error: str | None = Field(default=None, description="Last error message")


class GoogleCalendarConnectResponse(BaseModel):
    """Response for initiating Google Calendar connection."""

    authorization_url: str = Field(description="URL to redirect user for OAuth")
    state: str = Field(description="State parameter for CSRF protection")


class GoogleCalendarSyncResponse(BaseModel):
    """Response for sync operation."""

    created: int = Field(description="Number of events created")
    failed: int = Field(description="Number of events that failed")
    total: int = Field(description="Total subscriptions processed")


class GoogleCalendarListResponse(BaseModel):
    """Response for listing calendars."""

    calendars: list[dict] = Field(description="List of calendars")


@router.get("/google/status", response_model=GoogleCalendarStatusResponse)
@limiter.limit(rate_limit_get)
async def get_google_calendar_status(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoogleCalendarStatusResponse:
    """Get Google Calendar connection status.

    Returns the current connection status, last sync time, and any errors.

    Returns:
        GoogleCalendarStatusResponse: Connection status details.
    """
    service = GoogleCalendarService(db, current_user.id)
    status_info = await service.get_sync_status()
    return GoogleCalendarStatusResponse(**status_info)


@router.get("/google/connect", response_model=GoogleCalendarConnectResponse)
@limiter.limit(rate_limit_write)
async def initiate_google_calendar_connect(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoogleCalendarConnectResponse:
    """Initiate Google Calendar OAuth flow.

    Generates an authorization URL for the user to authorize access
    to their Google Calendar.

    Returns:
        GoogleCalendarConnectResponse: Authorization URL and state.

    Raises:
        HTTPException 503: If Google OAuth is not configured.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration is not configured",
        )

    service = GoogleCalendarService(db, current_user.id)

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = str(current_user.id)

    try:
        auth_url, _ = service.get_authorization_url(state)
        return GoogleCalendarConnectResponse(
            authorization_url=auth_url,
            state=state,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e


@router.get("/google/callback")
async def google_calendar_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State for CSRF verification"),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback.

    Exchanges the authorization code for tokens and stores them.
    Redirects to the frontend with success/error status.

    Args:
        code: Authorization code from Google.
        state: State parameter for CSRF verification.

    Returns:
        RedirectResponse: Redirect to frontend with result.
    """
    # Verify state
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        logger.warning(f"Invalid OAuth state: {state}")
        return RedirectResponse(
            url="http://localhost:3001/settings?google_calendar=error&reason=invalid_state"
        )

    service = GoogleCalendarService(db, UUID(user_id))

    try:
        await service.handle_oauth_callback(code, state)
        logger.info(f"Google Calendar connected for user {user_id}")
        return RedirectResponse(url="http://localhost:3001/settings?google_calendar=success")
    except ValueError as e:
        logger.error(f"OAuth callback failed: {e}")
        return RedirectResponse(
            url=f"http://localhost:3001/settings?google_calendar=error&reason={str(e)[:50]}"
        )


@router.delete("/google/disconnect", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_limit_write)
async def disconnect_google_calendar(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Disconnect Google Calendar integration.

    Removes the OAuth connection and stops syncing.
    """
    service = GoogleCalendarService(db, current_user.id)
    await service.disconnect()
    logger.info(f"Google Calendar disconnected for user {current_user.id}")


@router.post("/google/sync", response_model=GoogleCalendarSyncResponse)
@limiter.limit(rate_limit_write)
async def sync_to_google_calendar(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    calendar_id: str = Query(default="primary", description="Calendar ID to sync to"),
) -> GoogleCalendarSyncResponse:
    """Sync subscriptions to Google Calendar.

    Creates calendar events for all active subscriptions.

    Args:
        calendar_id: Google Calendar ID to sync to (default: 'primary').

    Returns:
        GoogleCalendarSyncResponse: Sync operation results.

    Raises:
        HTTPException 400: If not connected to Google Calendar.
    """
    service = GoogleCalendarService(db, current_user.id)
    status_info = await service.get_sync_status()

    if not status_info.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not connected to Google Calendar",
        )

    result = await service.sync_subscriptions_to_calendar(calendar_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return GoogleCalendarSyncResponse(**result)


@router.get("/google/calendars", response_model=GoogleCalendarListResponse)
@limiter.limit(rate_limit_get)
async def list_google_calendars(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoogleCalendarListResponse:
    """List user's Google Calendars.

    Returns a list of calendars the user has access to.

    Returns:
        GoogleCalendarListResponse: List of calendars.

    Raises:
        HTTPException 400: If not connected to Google Calendar.
    """
    service = GoogleCalendarService(db, current_user.id)
    status_info = await service.get_sync_status()

    if not status_info.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not connected to Google Calendar",
        )

    calendars = await service.list_calendars()
    return GoogleCalendarListResponse(calendars=calendars)
