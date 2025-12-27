"""Google Calendar OAuth and sync service.

This module provides functionality for Google Calendar OAuth authentication
and two-way synchronization of payment events.

Sprint 5.6 - Calendar Integration

References:
- https://developers.google.com/calendar/api/quickstart/python
- https://googleapis.github.io/google-api-python-client/docs/oauth.html
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.google_calendar import GoogleCalendarConnection, GoogleCalendarSyncStatus
from src.models.subscription import Subscription

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]

# Money Flow event prefix for identification
EVENT_PREFIX = "[Money Flow]"


class GoogleCalendarService:
    """Service for Google Calendar OAuth and event synchronization.

    Handles OAuth flow, token management, and event CRUD operations
    for syncing Money Flow subscriptions to Google Calendar.

    Attributes:
        db: AsyncSession for database access.
        user_id: UUID of the current user.

    Example:
        >>> service = GoogleCalendarService(db, user_id)
        >>> auth_url = service.get_authorization_url()
        >>> # User visits auth_url and authorizes
        >>> await service.handle_oauth_callback(code)
        >>> await service.sync_subscriptions_to_calendar()
    """

    def __init__(self, db: AsyncSession, user_id: UUID) -> None:
        """Initialize the Google Calendar service.

        Args:
            db: AsyncSession for database access.
            user_id: UUID of the current user.
        """
        self.db = db
        self.user_id = user_id

    def _get_oauth_flow(self, state: str | None = None) -> Flow:
        """Create an OAuth flow instance.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            Flow: Configured OAuth flow instance.

        Raises:
            ValueError: If Google OAuth credentials are not configured.
        """
        if not settings.google_client_id or not settings.google_client_secret:
            raise ValueError("Google OAuth credentials are not configured")

        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.google_redirect_uri

        return flow

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Generate the Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            tuple: (authorization_url, state) - The URL to redirect user to
                   and the state for verification.

        Example:
            >>> auth_url, state = service.get_authorization_url()
            >>> # Store state in session, redirect user to auth_url
        """
        flow = self._get_oauth_flow(state)
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
        )
        return authorization_url, state

    async def handle_oauth_callback(
        self,
        code: str,
        state: str | None = None,
    ) -> GoogleCalendarConnection:
        """Handle the OAuth callback and store tokens.

        Args:
            code: Authorization code from Google.
            state: State parameter for verification.

        Returns:
            GoogleCalendarConnection: The created or updated connection.

        Raises:
            ValueError: If token exchange fails.
        """
        flow = self._get_oauth_flow(state)

        try:
            flow.fetch_token(code=code)
        except Exception as e:
            logger.error(f"Failed to fetch token: {e}")
            raise ValueError(f"Failed to exchange authorization code: {e}") from e

        credentials = flow.credentials

        # Check for existing connection
        result = await self.db.execute(
            select(GoogleCalendarConnection).where(
                GoogleCalendarConnection.user_id == str(self.user_id)
            )
        )
        connection = result.scalar_one_or_none()

        if connection:
            # Update existing connection
            connection.access_token = credentials.token
            connection.refresh_token = credentials.refresh_token or connection.refresh_token
            connection.token_expiry = credentials.expiry
            connection.sync_status = GoogleCalendarSyncStatus.CONNECTED
            connection.last_error = None
            connection.updated_at = datetime.utcnow()
        else:
            # Create new connection
            connection = GoogleCalendarConnection(
                user_id=str(self.user_id),
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=credentials.expiry,
                sync_status=GoogleCalendarSyncStatus.CONNECTED,
            )
            self.db.add(connection)

        await self.db.commit()
        await self.db.refresh(connection)

        logger.info(f"Google Calendar connected for user {self.user_id}")
        return connection

    async def get_connection(self) -> GoogleCalendarConnection | None:
        """Get the user's Google Calendar connection.

        Returns:
            GoogleCalendarConnection or None if not connected.
        """
        result = await self.db.execute(
            select(GoogleCalendarConnection).where(
                GoogleCalendarConnection.user_id == str(self.user_id)
            )
        )
        return result.scalar_one_or_none()

    async def disconnect(self) -> bool:
        """Disconnect Google Calendar integration.

        Returns:
            bool: True if disconnected successfully.
        """
        connection = await self.get_connection()
        if connection:
            connection.sync_status = GoogleCalendarSyncStatus.DISCONNECTED
            connection.access_token = ""
            connection.refresh_token = None
            await self.db.commit()
            logger.info(f"Google Calendar disconnected for user {self.user_id}")
            return True
        return False

    async def _get_credentials(self) -> Credentials | None:
        """Get valid OAuth credentials, refreshing if needed.

        Returns:
            Credentials or None if no valid connection exists.
        """
        connection = await self.get_connection()
        if not connection or connection.sync_status == GoogleCalendarSyncStatus.DISCONNECTED:
            return None

        credentials = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            expiry=connection.token_expiry,
        )

        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request

                credentials.refresh(Request())

                # Update stored tokens
                connection.access_token = credentials.token
                connection.token_expiry = credentials.expiry
                connection.updated_at = datetime.utcnow()
                await self.db.commit()

                logger.info(f"Refreshed Google Calendar token for user {self.user_id}")
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                connection.sync_status = GoogleCalendarSyncStatus.TOKEN_EXPIRED
                connection.last_error = str(e)
                await self.db.commit()
                return None

        return credentials

    def _get_calendar_service(self, credentials: Credentials) -> Any:
        """Build the Google Calendar API service.

        Args:
            credentials: Valid OAuth credentials.

        Returns:
            Google Calendar API service instance.
        """
        return build("calendar", "v3", credentials=credentials)

    async def list_calendars(self) -> list[dict]:
        """List user's calendars.

        Returns:
            List of calendar dictionaries with id, summary, primary status.
        """
        credentials = await self._get_credentials()
        if not credentials:
            return []

        try:
            service = self._get_calendar_service(credentials)
            calendar_list = service.calendarList().list().execute()
            return [
                {
                    "id": cal["id"],
                    "summary": cal.get("summary", "Untitled"),
                    "primary": cal.get("primary", False),
                }
                for cal in calendar_list.get("items", [])
            ]
        except HttpError as e:
            logger.error(f"Failed to list calendars: {e}")
            return []

    async def create_event(
        self,
        subscription: Subscription,
        calendar_id: str = "primary",
    ) -> dict | None:
        """Create a calendar event for a subscription.

        Args:
            subscription: The subscription to create an event for.
            calendar_id: Google Calendar ID (default: 'primary').

        Returns:
            dict: The created event or None if failed.
        """
        credentials = await self._get_credentials()
        if not credentials or not subscription.next_payment_date:
            return None

        event = self._build_event_body(subscription)

        try:
            service = self._get_calendar_service(credentials)
            created_event = (
                service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event,
                )
                .execute()
            )

            logger.info(f"Created Google Calendar event: {created_event.get('id')}")
            return created_event
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            return None

    def _build_event_body(self, subscription: Subscription) -> dict:
        """Build Google Calendar event body from subscription.

        Args:
            subscription: The subscription to convert.

        Returns:
            dict: Google Calendar event body.
        """
        # Get currency symbol
        currency_symbols = {
            "GBP": "£",
            "USD": "$",
            "EUR": "€",
            "UAH": "₴",
            "CAD": "C$",
            "AUD": "A$",
            "JPY": "¥",
        }
        symbol = currency_symbols.get(subscription.currency, subscription.currency + " ")
        amount_str = f"{symbol}{subscription.amount:.2f}"

        # Build description
        freq_str = subscription.frequency
        if hasattr(subscription.frequency, "value"):
            freq_str = subscription.frequency.value

        description_parts = [
            f"Payment: {subscription.service_name}",
            f"Amount: {amount_str}",
            f"Frequency: {freq_str.replace('_', ' ').title()}",
        ]

        if subscription.payment_type:
            pt_str = subscription.payment_type
            if hasattr(subscription.payment_type, "value"):
                pt_str = subscription.payment_type.value
            description_parts.append(f"Type: {pt_str.replace('_', ' ').title()}")

        if subscription.notes:
            description_parts.append(f"Notes: {subscription.notes}")

        description_parts.append("\n---\nManaged by Money Flow")

        # Format date
        payment_date = subscription.next_payment_date

        event = {
            "summary": f"{EVENT_PREFIX} {subscription.service_name} - {amount_str}",
            "description": "\n".join(description_parts),
            "start": {
                "date": payment_date.isoformat(),
            },
            "end": {
                "date": (payment_date + timedelta(days=1)).isoformat(),
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 24 * 60},  # 1 day before
                ],
            },
            "extendedProperties": {
                "private": {
                    "moneyflow_subscription_id": str(subscription.id),
                    "moneyflow_managed": "true",
                },
            },
        }

        # Add recurrence rule for recurring payments
        rrule = self._get_recurrence_rule(freq_str)
        if rrule:
            event["recurrence"] = [rrule]

        return event

    def _get_recurrence_rule(self, frequency: str) -> str | None:
        """Get Google Calendar recurrence rule for a frequency.

        Args:
            frequency: Payment frequency string.

        Returns:
            str: RRULE string or None for one-time payments.
        """
        freq_lower = frequency.lower().replace(" ", "_")

        rules = {
            "daily": "RRULE:FREQ=DAILY;INTERVAL=1",
            "weekly": "RRULE:FREQ=WEEKLY;INTERVAL=1",
            "biweekly": "RRULE:FREQ=WEEKLY;INTERVAL=2",
            "monthly": "RRULE:FREQ=MONTHLY;INTERVAL=1",
            "quarterly": "RRULE:FREQ=MONTHLY;INTERVAL=3",
            "yearly": "RRULE:FREQ=YEARLY;INTERVAL=1",
            "annually": "RRULE:FREQ=YEARLY;INTERVAL=1",
        }

        return rules.get(freq_lower)

    async def sync_subscriptions_to_calendar(
        self,
        calendar_id: str = "primary",
    ) -> dict:
        """Sync all active subscriptions to Google Calendar.

        Creates or updates calendar events for all active subscriptions.

        Args:
            calendar_id: Google Calendar ID to sync to.

        Returns:
            dict: Sync result with counts of created/updated/failed events.
        """
        connection = await self.get_connection()
        if not connection or connection.sync_status != GoogleCalendarSyncStatus.CONNECTED:
            return {"error": "Not connected to Google Calendar"}

        # Get active subscriptions
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == str(self.user_id))
            .where(Subscription.is_active == True)  # noqa: E712
            .where(Subscription.next_payment_date != None)  # noqa: E711
        )
        subscriptions = result.scalars().all()

        created = 0
        failed = 0

        for sub in subscriptions:
            event = await self.create_event(sub, calendar_id)
            if event:
                created += 1
            else:
                failed += 1

        # Update last sync time
        connection.last_sync_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"Synced {created} events to Google Calendar for user {self.user_id}")

        return {
            "created": created,
            "failed": failed,
            "total": len(subscriptions),
        }

    async def get_sync_status(self) -> dict:
        """Get the current sync status.

        Returns:
            dict: Status information including connection state and last sync.
        """
        connection = await self.get_connection()

        if not connection:
            return {
                "connected": False,
                "status": "not_connected",
            }

        return {
            "connected": connection.sync_status == GoogleCalendarSyncStatus.CONNECTED,
            "status": connection.sync_status.value,
            "calendar_id": connection.calendar_id,
            "sync_enabled": connection.sync_enabled,
            "last_sync_at": connection.last_sync_at.isoformat()
            if connection.last_sync_at
            else None,
            "last_error": connection.last_error,
        }
