"""Web Push notification service.

This module provides the PushService class for sending push notifications
to web browsers using the Web Push API (VAPID).

Features:
- VAPID key generation and management
- Push subscription storage
- Payment reminder push notifications
- Daily/weekly digest notifications
"""

import json
import logging
from typing import TYPE_CHECKING, Any

from pywebpush import WebPushException, webpush

from src.core.config import settings

if TYPE_CHECKING:
    from src.models.subscription import Subscription

logger = logging.getLogger(__name__)

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "UAH": "₴",
}


class PushService:
    """Service for sending Web Push notifications.

    Uses VAPID (Voluntary Application Server Identification) for authentication
    with push services.

    Attributes:
        vapid_private_key: VAPID private key for signing push messages.
        vapid_public_key: VAPID public key shared with clients.
        vapid_claims: VAPID claims including contact email.

    Example:
        >>> service = PushService()
        >>> await service.send_notification(
        ...     subscription_info={"endpoint": "...", "keys": {...}},
        ...     title="Payment Due",
        ...     body="Netflix £15.99 due tomorrow",
        ... )
        True
    """

    def __init__(
        self,
        vapid_private_key: str | None = None,
        vapid_public_key: str | None = None,
        vapid_email: str | None = None,
    ):
        """Initialize PushService.

        Args:
            vapid_private_key: VAPID private key (defaults to config).
            vapid_public_key: VAPID public key (defaults to config).
            vapid_email: Contact email for VAPID claims (defaults to config).
        """
        self.vapid_private_key = vapid_private_key or getattr(settings, "vapid_private_key", "")
        self.vapid_public_key = vapid_public_key or getattr(settings, "vapid_public_key", "")
        self.vapid_email = vapid_email or getattr(settings, "vapid_email", "")

        self.vapid_claims = {"sub": f"mailto:{self.vapid_email}"} if self.vapid_email else {}

    @property
    def is_configured(self) -> bool:
        """Check if push service is configured.

        Returns:
            True if VAPID keys and email are configured.
        """
        return bool(self.vapid_private_key and self.vapid_public_key and self.vapid_email)

    def send_notification(
        self,
        subscription_info: dict[str, Any],
        title: str,
        body: str,
        icon: str = "/icons/icon-192x192.png",
        badge: str = "/icons/badge-72x72.png",
        tag: str | None = None,
        data: dict[str, Any] | None = None,
        actions: list[dict[str, str]] | None = None,
    ) -> bool:
        """Send a push notification.

        Args:
            subscription_info: Push subscription object from browser.
            title: Notification title.
            body: Notification body text.
            icon: URL to notification icon.
            badge: URL to notification badge.
            tag: Tag for notification grouping/replacement.
            data: Additional data to include with notification.
            actions: List of notification actions (buttons).

        Returns:
            True if notification sent successfully, False otherwise.
        """
        if not self.is_configured:
            logger.warning("Push service not configured, skipping notification")
            return False

        try:
            payload = {
                "title": title,
                "body": body,
                "icon": icon,
                "badge": badge,
            }

            if tag:
                payload["tag"] = tag
            if data:
                payload["data"] = data
            if actions:
                payload["actions"] = actions

            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
            )

            logger.info(f"Push notification sent: {title}")
            return True

        except WebPushException as e:
            logger.error(f"Push notification failed: {e}")
            # Handle specific error codes
            if e.response and e.response.status_code == 410:
                # Subscription expired or unsubscribed
                logger.warning("Push subscription is no longer valid (410 Gone)")
            return False
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return False

    def send_reminder(
        self,
        subscription_info: dict[str, Any],
        subscription: "Subscription",
        days_until: int,
    ) -> bool:
        """Send a payment reminder push notification.

        Args:
            subscription_info: Push subscription object from browser.
            subscription: Subscription object for the reminder.
            days_until: Number of days until payment is due.

        Returns:
            True if notification sent successfully.
        """
        # Get currency symbol
        currency_symbol = CURRENCY_SYMBOLS.get(subscription.currency, "£")
        amount = f"{currency_symbol}{subscription.amount:.2f}"

        # Determine urgency and text
        if days_until < 0:
            title = f"⚠️ Overdue: {subscription.name}"
            body = f"Payment of {amount} is {abs(days_until)} days overdue"
            tag = f"overdue-{subscription.id}"
        elif days_until == 0:
            title = f"💳 Due Today: {subscription.name}"
            body = f"Payment of {amount} is due today"
            tag = f"today-{subscription.id}"
        elif days_until == 1:
            title = f"📅 Due Tomorrow: {subscription.name}"
            body = f"Payment of {amount} is due tomorrow"
            tag = f"tomorrow-{subscription.id}"
        else:
            title = f"📅 Upcoming: {subscription.name}"
            body = f"Payment of {amount} due in {days_until} days"
            tag = f"upcoming-{subscription.id}"

        return self.send_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            tag=tag,
            data={
                "type": "reminder",
                "subscription_id": str(subscription.id),
                "days_until": days_until,
            },
            actions=[
                {"action": "view", "title": "View Details"},
                {"action": "dismiss", "title": "Dismiss"},
            ],
        )

    def send_daily_digest(
        self,
        subscription_info: dict[str, Any],
        payment_count: int,
        total_amount: float,
        currency: str = "GBP",
    ) -> bool:
        """Send a daily digest push notification.

        Args:
            subscription_info: Push subscription object from browser.
            payment_count: Number of upcoming payments.
            total_amount: Total amount due.
            currency: Currency code.

        Returns:
            True if notification sent successfully.
        """
        currency_symbol = CURRENCY_SYMBOLS.get(currency, "£")

        if payment_count == 0:
            title = "📊 Daily Digest"
            body = "No payments due this week"
        elif payment_count == 1:
            title = "📊 Daily Digest: 1 Payment"
            body = f"You have 1 payment ({currency_symbol}{total_amount:.2f}) coming up"
        else:
            title = f"📊 Daily Digest: {payment_count} Payments"
            body = (
                f"You have {payment_count} payments ({currency_symbol}{total_amount:.2f}) coming up"
            )

        return self.send_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            tag="daily-digest",
            data={
                "type": "daily_digest",
                "payment_count": payment_count,
                "total_amount": total_amount,
            },
            actions=[
                {"action": "view", "title": "View All"},
            ],
        )

    def send_weekly_digest(
        self,
        subscription_info: dict[str, Any],
        payment_count: int,
        total_amount: float,
        currency: str = "GBP",
    ) -> bool:
        """Send a weekly digest push notification.

        Args:
            subscription_info: Push subscription object from browser.
            payment_count: Number of upcoming payments.
            total_amount: Total amount due this week.
            currency: Currency code.

        Returns:
            True if notification sent successfully.
        """
        currency_symbol = CURRENCY_SYMBOLS.get(currency, "£")

        if payment_count == 0:
            title = "📅 Weekly Summary"
            body = "No payments scheduled this week"
        elif payment_count == 1:
            title = "📅 Weekly Summary: 1 Payment"
            body = f"You have 1 payment ({currency_symbol}{total_amount:.2f}) this week"
        else:
            title = f"📅 Weekly Summary: {payment_count} Payments"
            body = f"You have {payment_count} payments totaling {currency_symbol}{total_amount:.2f} this week"

        return self.send_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            tag="weekly-digest",
            data={
                "type": "weekly_digest",
                "payment_count": payment_count,
                "total_amount": total_amount,
            },
            actions=[
                {"action": "view", "title": "View All"},
            ],
        )

    def send_test_notification(self, subscription_info: dict[str, Any]) -> bool:
        """Send a test push notification.

        Args:
            subscription_info: Push subscription object from browser.

        Returns:
            True if notification sent successfully.
        """
        return self.send_notification(
            subscription_info=subscription_info,
            title="✅ Push Notifications Enabled",
            body="You'll now receive payment reminders and updates",
            tag="test-notification",
            data={"type": "test"},
        )
