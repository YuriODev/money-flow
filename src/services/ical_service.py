"""iCal Feed Generation Service.

This module provides functionality to generate iCal calendar feeds
for subscription payments, allowing users to subscribe to their
payment schedule in any calendar application.

Sprint 5.6 - Calendar Integration
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from icalendar import Calendar, Event
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription
from src.models.user import User

if TYPE_CHECKING:
    pass


# Map payment frequencies to iCal RRULE frequencies
FREQUENCY_MAP = {
    "daily": {"FREQ": "DAILY", "INTERVAL": 1},
    "weekly": {"FREQ": "WEEKLY", "INTERVAL": 1},
    "biweekly": {"FREQ": "WEEKLY", "INTERVAL": 2},
    "monthly": {"FREQ": "MONTHLY", "INTERVAL": 1},
    "quarterly": {"FREQ": "MONTHLY", "INTERVAL": 3},
    "yearly": {"FREQ": "YEARLY", "INTERVAL": 1},
    "annually": {"FREQ": "YEARLY", "INTERVAL": 1},
    "one_time": None,  # No recurrence for one-time payments
}


class ICalService:
    """Service for generating iCal calendar feeds.

    This service generates iCal (.ics) feeds containing payment events
    for a user's subscriptions and recurring payments.

    Attributes:
        db: AsyncSession for database access.
        user_id: UUID of the user whose calendar to generate.

    Example:
        >>> service = ICalService(db, user_id)
        >>> calendar_bytes = await service.generate_feed()
        >>> # Returns bytes of the .ics file
    """

    def __init__(self, db: AsyncSession, user_id: UUID) -> None:
        """Initialize the iCal service.

        Args:
            db: AsyncSession for database access.
            user_id: UUID of the user whose calendar to generate.
        """
        self.db = db
        self.user_id = user_id

    async def generate_feed(
        self,
        include_inactive: bool = False,
        days_ahead: int = 365,
        payment_types: list[str] | None = None,
    ) -> bytes:
        """Generate an iCal feed for user's subscriptions.

        Creates a calendar with events for all upcoming payments.
        Recurring payments are represented with RRULE for proper
        calendar repeat handling.

        Args:
            include_inactive: Include inactive subscriptions.
            days_ahead: Number of days to include future events.
            payment_types: Filter by payment types (e.g., ['subscription', 'debt']).

        Returns:
            bytes: The iCal file content as bytes.

        Example:
            >>> ical_bytes = await service.generate_feed(days_ahead=90)
            >>> with open("payments.ics", "wb") as f:
            ...     f.write(ical_bytes)
        """
        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Money Flow//Subscription Tracker//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", "Money Flow - Payments")
        cal.add("x-wr-timezone", "UTC")

        # Fetch subscriptions - convert UUID to string for comparison with String(36) column
        user_id_str = str(self.user_id)
        query = select(Subscription).where(Subscription.user_id == user_id_str)

        if not include_inactive:
            query = query.where(Subscription.is_active == True)  # noqa: E712

        if payment_types:
            query = query.where(Subscription.payment_type.in_(payment_types))

        result = await self.db.execute(query)
        subscriptions = result.scalars().all()

        # Generate events for each subscription
        for sub in subscriptions:
            event = self._create_event(sub, days_ahead)
            if event:
                cal.add_component(event)

        return cal.to_ical()

    def _create_event(self, sub: Subscription, days_ahead: int) -> Event | None:
        """Create an iCal event for a subscription.

        Args:
            sub: The subscription to create an event for.
            days_ahead: Number of days to limit future events.

        Returns:
            Event: The iCal event, or None if no event should be created.
        """
        # Skip if no next payment date
        if not sub.next_payment_date:
            return None

        # Skip if payment is too far in the future
        if sub.next_payment_date > datetime.now().date() + timedelta(days=days_ahead):
            return None

        event = Event()

        # Generate a stable UID based on subscription ID
        uid = f"{sub.id}@moneyflow.app"
        event.add("uid", uid)

        # Event summary (title)
        currency_symbol = self._get_currency_symbol(sub.currency)
        amount_str = f"{currency_symbol}{sub.amount:.2f}"
        event.add("summary", f"💰 {sub.name} - {amount_str}")

        # Event description
        # Handle frequency - could be Enum or string
        freq_str = sub.frequency.value if hasattr(sub.frequency, "value") else str(sub.frequency)
        description_parts = [
            f"Payment: {sub.name}",
            f"Amount: {amount_str}",
            f"Frequency: {freq_str.replace('_', ' ').title()}",
        ]

        # Handle payment_type - could be Enum or string
        if sub.payment_type:
            pt_str = (
                sub.payment_type.value
                if hasattr(sub.payment_type, "value")
                else str(sub.payment_type)
            )
            description_parts.append(f"Type: {pt_str.replace('_', ' ').title()}")

        if sub.notes:
            description_parts.append(f"Notes: {sub.notes}")

        if sub.card_id:
            description_parts.append("Card: Linked")

        event.add("description", "\n".join(description_parts))

        # Set the date (all-day event)
        event.add("dtstart", sub.next_payment_date)
        event.add("dtend", sub.next_payment_date + timedelta(days=1))

        # Add categories
        categories = ["Payment"]
        if sub.payment_type:
            pt_str = (
                sub.payment_type.value
                if hasattr(sub.payment_type, "value")
                else str(sub.payment_type)
            )
            categories.append(pt_str.replace("_", " ").title())
        event.add("categories", categories)

        # Set priority based on amount
        if sub.amount >= 500:
            event.add("priority", 1)  # High
        elif sub.amount >= 100:
            event.add("priority", 5)  # Medium
        else:
            event.add("priority", 9)  # Low

        # Add recurrence rule for recurring payments
        rrule = self._get_rrule(freq_str)
        if rrule:
            event.add("rrule", rrule)

        # Add alarm (reminder) 1 day before
        from icalendar import Alarm

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Payment due tomorrow: {sub.name} - {amount_str}")
        alarm.add("trigger", timedelta(days=-1))
        event.add_component(alarm)

        # Add creation timestamp
        event.add("dtstamp", datetime.utcnow())
        event.add("created", sub.created_at if sub.created_at else datetime.utcnow())

        return event

    def _get_rrule(self, frequency: str) -> dict | None:
        """Get iCal RRULE parameters for a frequency.

        Args:
            frequency: The payment frequency string.

        Returns:
            dict: RRULE parameters, or None for one-time payments.
        """
        freq_lower = frequency.lower().replace(" ", "_")
        return FREQUENCY_MAP.get(freq_lower)

    def _get_currency_symbol(self, currency: str) -> str:
        """Get currency symbol for a currency code.

        Args:
            currency: ISO 4217 currency code.

        Returns:
            str: Currency symbol.
        """
        symbols = {
            "GBP": "£",
            "USD": "$",
            "EUR": "€",
            "UAH": "₴",
            "CAD": "C$",
            "AUD": "A$",
            "JPY": "¥",
            "CHF": "CHF ",
            "CNY": "¥",
            "INR": "₹",
            "BRL": "R$",
        }
        return symbols.get(currency.upper(), f"{currency} ")


async def generate_ical_token(db: AsyncSession, user_id: UUID) -> str:
    """Generate or retrieve an iCal feed token for a user.

    This token is used to authenticate iCal feed requests without
    requiring full OAuth. The token is stored in the user's record.

    Args:
        db: AsyncSession for database access.
        user_id: UUID of the user.

    Returns:
        str: The iCal feed token.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Check if user already has a token
    if hasattr(user, "ical_token") and user.ical_token:
        return user.ical_token

    # Generate new token
    token = secrets.token_urlsafe(32)

    # Store token (requires ical_token column on User model)
    # For now, we generate a deterministic token based on user_id
    # This can be upgraded to stored tokens in a future migration
    token = hashlib.sha256(f"{user_id}-ical-feed".encode()).hexdigest()[:32]

    return token


async def validate_ical_token(db: AsyncSession, token: str) -> UUID | None:
    """Validate an iCal feed token and return the user ID.

    Args:
        db: AsyncSession for database access.
        token: The iCal feed token to validate.

    Returns:
        UUID: The user ID if valid, None otherwise.
    """
    # For the deterministic token approach, we need to look up by token
    # This requires either a stored token or iterating users (not ideal)
    # A proper implementation would store tokens in the database

    # For now, return None and implement proper token storage later
    # when we add the ical_token column to the User model
    return None


def generate_feed_url(base_url: str, user_id: UUID, token: str) -> str:
    """Generate the full iCal feed URL for a user.

    Args:
        base_url: The base URL of the API (e.g., https://api.moneyflow.app).
        user_id: UUID of the user.
        token: The iCal feed token.

    Returns:
        str: The full iCal feed URL.
    """
    return f"{base_url}/api/v1/calendar/feed/{user_id}/{token}/payments.ics"
