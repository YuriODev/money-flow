"""Telegram bot service for payment notifications.

This module provides the TelegramService class for sending payment reminders
and handling Telegram bot interactions. Supports both webhook and long-polling modes.
"""

import asyncio
import hmac
import logging
from collections.abc import Callable, Coroutine
from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from src.core.config import settings
from src.models.subscription import Subscription

logger = logging.getLogger(__name__)

# Type alias for update handler
UpdateHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "UAH": "₴",
}


class TelegramService:
    """Service for sending Telegram notifications.

    Handles sending payment reminders, daily/weekly digests, and
    managing Telegram bot interactions.

    Attributes:
        bot_token: Telegram bot API token.
        bot_username: Telegram bot username (without @).
        api_url: Telegram Bot API base URL.

    Example:
        >>> service = TelegramService()
        >>> await service.send_message("123456789", "Hello!")
        True
    """

    def __init__(self, bot_token: str | None = None):
        """Initialize TelegramService.

        Args:
            bot_token: Optional bot token (defaults to config).
        """
        self.bot_token = bot_token or settings.telegram_bot_token
        self.bot_username = settings.telegram_bot_username
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    @property
    def is_configured(self) -> bool:
        """Check if Telegram bot is configured.

        Returns:
            True if bot token is set.
        """
        return bool(self.bot_token)

    @property
    def bot_link(self) -> str:
        """Get the bot link for users to start a conversation.

        Returns:
            Telegram bot deep link URL.
        """
        return f"https://t.me/{self.bot_username}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        """Send a text message to a Telegram chat.

        Args:
            chat_id: Telegram chat ID to send to.
            text: Message text (supports HTML formatting).
            parse_mode: Message parse mode (HTML or Markdown).
            disable_notification: Send silently without notification sound.

        Returns:
            True if message was sent successfully.

        Example:
            >>> await service.send_message("123456789", "<b>Hello!</b>")
            True
        """
        if not self.is_configured:
            logger.warning("Telegram bot not configured, skipping message")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_notification": disable_notification,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("ok", False)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_reminder(
        self,
        chat_id: str,
        subscription: Subscription,
        days_until: int,
    ) -> bool:
        """Send a payment reminder notification.

        Args:
            chat_id: Telegram chat ID.
            subscription: Subscription to remind about.
            days_until: Days until payment is due.

        Returns:
            True if reminder was sent successfully.
        """
        currency_symbol = CURRENCY_SYMBOLS.get(subscription.currency, subscription.currency)
        amount = f"{currency_symbol}{subscription.amount:.2f}"

        # Determine urgency and emoji
        if days_until <= 0:
            urgency = "🚨 <b>OVERDUE</b>"
            timeframe = "is overdue!"
        elif days_until == 1:
            urgency = "⚠️ <b>Due Tomorrow</b>"
            timeframe = "is due tomorrow"
        elif days_until <= 3:
            urgency = "📅 <b>Due Soon</b>"
            timeframe = f"is due in {days_until} days"
        else:
            urgency = "📆 <b>Upcoming</b>"
            timeframe = f"is due in {days_until} days"

        # Format due date
        due_date = (
            subscription.next_payment_date.strftime("%B %d, %Y")
            if subscription.next_payment_date
            else "Unknown"
        )

        # Build message
        message = f"""
{urgency}

📦 <b>{subscription.name}</b>
💰 {amount}
📅 {timeframe}
🗓️ Due: {due_date}
"""

        # Add payment type info
        if subscription.payment_type:
            type_name = subscription.payment_type.replace("_", " ").title()
            message += f"🏷️ Type: {type_name}\n"

        # Add card info if available
        if subscription.payment_card:
            message += f"💳 Card: {subscription.payment_card.name}\n"

        return await self.send_message(chat_id, message.strip())

    async def send_daily_digest(
        self,
        chat_id: str,
        subscriptions: list[Subscription],
        currency: str = "GBP",
    ) -> bool:
        """Send a daily payment digest.

        Args:
            chat_id: Telegram chat ID.
            subscriptions: List of upcoming subscriptions.
            currency: Display currency for totals.

        Returns:
            True if digest was sent successfully.
        """
        if not subscriptions:
            return True  # Nothing to send

        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)
        today = date.today()

        # Categorize payments
        due_today = []
        due_soon = []  # 1-7 days
        total_due_today = Decimal("0")
        total_due_soon = Decimal("0")

        for sub in subscriptions:
            if not sub.next_payment_date:
                continue

            days_until = (sub.next_payment_date - today).days

            if days_until <= 0:
                due_today.append(sub)
                total_due_today += sub.amount
            elif days_until <= 7:
                due_soon.append(sub)
                total_due_soon += sub.amount

        # Build message
        message = "📊 <b>Daily Payment Summary</b>\n"
        message += f"📅 {today.strftime('%B %d, %Y')}\n\n"

        if due_today:
            message += "🚨 <b>Due Today:</b>\n"
            for sub in due_today:
                sym = CURRENCY_SYMBOLS.get(sub.currency, sub.currency)
                message += f"  • {sub.name}: {sym}{sub.amount:.2f}\n"
            message += f"  <b>Total: {currency_symbol}{total_due_today:.2f}</b>\n\n"

        if due_soon:
            message += "📅 <b>Upcoming This Week:</b>\n"
            for sub in due_soon[:5]:  # Limit to 5
                days = (sub.next_payment_date - today).days
                sym = CURRENCY_SYMBOLS.get(sub.currency, sub.currency)
                message += f"  • {sub.name}: {sym}{sub.amount:.2f} ({days}d)\n"
            if len(due_soon) > 5:
                message += f"  ... and {len(due_soon) - 5} more\n"
            message += f"  <b>Total: {currency_symbol}{total_due_soon:.2f}</b>\n"

        if not due_today and not due_soon:
            message += "✅ No payments due in the next 7 days!"

        return await self.send_message(chat_id, message.strip())

    async def send_weekly_digest(
        self,
        chat_id: str,
        subscriptions: list[Subscription],
        currency: str = "GBP",
    ) -> bool:
        """Send a weekly payment summary.

        Args:
            chat_id: Telegram chat ID.
            subscriptions: List of subscriptions for the week.
            currency: Display currency for totals.

        Returns:
            True if digest was sent successfully.
        """
        if not subscriptions:
            message = "📅 <b>Weekly Payment Summary</b>\n\n✅ No payments scheduled for this week!"
            return await self.send_message(chat_id, message)

        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)
        today = date.today()

        # Calculate totals
        total = Decimal("0")
        by_day: dict[date, list[Subscription]] = {}

        for sub in subscriptions:
            if not sub.next_payment_date:
                continue
            total += sub.amount
            day = sub.next_payment_date
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(sub)

        # Build message
        message = "📅 <b>Weekly Payment Summary</b>\n\n"

        for day in sorted(by_day.keys()):
            day_name = day.strftime("%A, %B %d")
            if day == today:
                day_name += " (Today)"
            message += f"📆 <b>{day_name}</b>\n"
            for sub in by_day[day]:
                sym = CURRENCY_SYMBOLS.get(sub.currency, sub.currency)
                message += f"  • {sub.name}: {sym}{sub.amount:.2f}\n"
            message += "\n"

        message += f"💰 <b>Weekly Total: {currency_symbol}{total:.2f}</b>"

        return await self.send_message(chat_id, message.strip())

    async def send_verification_prompt(self, chat_id: str, username: str | None = None) -> bool:
        """Send verification code prompt to user.

        Args:
            chat_id: Telegram chat ID.
            username: User's Telegram username.

        Returns:
            True if message was sent successfully.
        """
        greeting = f"Hi {username}! " if username else "Hi! "
        message = f"""
{greeting}👋

Welcome to <b>Money Flow</b> 💰

To link your account and receive payment reminders, please enter the verification code shown in the Money Flow app.

Just send the 6-character code as a message.
"""
        return await self.send_message(chat_id, message.strip())

    async def send_verification_success(self, chat_id: str) -> bool:
        """Send verification success message.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            True if message was sent successfully.
        """
        message = """
✅ <b>Account Linked Successfully!</b>

You'll now receive payment reminders directly here on Telegram.

You can manage your notification preferences in the Money Flow app settings.

Commands:
/status - Check your notification settings
/pause - Temporarily pause notifications
/help - Get help
"""
        return await self.send_message(chat_id, message.strip())

    async def send_verification_failed(self, chat_id: str) -> bool:
        """Send verification failed message.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            True if message was sent successfully.
        """
        message = """
❌ <b>Verification Failed</b>

The code you entered is invalid or has expired.

Please generate a new code in the Money Flow app settings and try again.
"""
        return await self.send_message(chat_id, message.strip())

    async def send_test_notification(self, chat_id: str) -> bool:
        """Send a test notification.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            True if message was sent successfully.
        """
        message = """
🔔 <b>Test Notification</b>

This is a test notification from Money Flow.

If you received this message, your Telegram notifications are working correctly! ✅
"""
        return await self.send_message(chat_id, message.strip())

    def verify_webhook_signature(self, data: bytes, signature: str) -> bool:
        """Verify Telegram webhook update signature.

        Args:
            data: Raw request body.
            signature: X-Telegram-Bot-Api-Secret-Token header value.

        Returns:
            True if signature is valid.
        """
        if not settings.telegram_webhook_secret:
            return True  # No secret configured, skip verification

        return hmac.compare_digest(signature, settings.telegram_webhook_secret)

    async def get_me(self) -> dict[str, Any] | None:
        """Get bot information.

        Returns:
            Bot info dict or None if failed.
        """
        if not self.is_configured:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/getMe", timeout=10.0)
                response.raise_for_status()
                result = response.json()
                if result.get("ok"):
                    return result.get("result")
        except httpx.HTTPError as e:
            logger.error(f"Failed to get bot info: {e}")

        return None

    async def get_updates(
        self,
        offset: int | None = None,
        timeout: int = 30,
    ) -> list[dict[str, Any]]:
        """Get updates from Telegram using long polling.

        Args:
            offset: Identifier of the first update to be returned.
            timeout: Long polling timeout in seconds.

        Returns:
            List of update objects.
        """
        if not self.is_configured:
            return []

        params: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            params["offset"] = offset

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/getUpdates",
                    params=params,
                    timeout=timeout + 10,  # HTTP timeout > long poll timeout
                )
                response.raise_for_status()
                result = response.json()
                if result.get("ok"):
                    return result.get("result", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to get updates: {e}")

        return []

    async def delete_webhook(self) -> bool:
        """Delete webhook to enable long polling mode.

        Returns:
            True if webhook was deleted successfully.
        """
        if not self.is_configured:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/deleteWebhook",
                    json={"drop_pending_updates": False},
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("ok", False)
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False


class TelegramPoller:
    """Long polling handler for Telegram bot updates.

    Runs a background task that polls for updates and processes them.

    Attributes:
        service: TelegramService instance.
        handler: Async function to handle updates.
        running: Whether the poller is currently running.
        task: The background polling task.
    """

    def __init__(
        self,
        service: TelegramService,
        handler: UpdateHandler,
    ):
        """Initialize TelegramPoller.

        Args:
            service: TelegramService instance.
            handler: Async function to call for each update.
        """
        self.service = service
        self.handler = handler
        self.running = False
        self.task: asyncio.Task | None = None
        self._offset: int | None = None

    async def start(self) -> None:
        """Start the polling loop.

        Deletes any existing webhook and starts polling for updates.
        """
        if self.running:
            logger.warning("Telegram poller already running")
            return

        if not self.service.is_configured:
            logger.warning("Telegram bot not configured, skipping poller start")
            return

        # Delete webhook to enable long polling
        deleted = await self.service.delete_webhook()
        if deleted:
            logger.info("Deleted Telegram webhook, switching to long polling mode")

        # Verify bot is working
        bot_info = await self.service.get_me()
        if bot_info:
            logger.info(f"Telegram bot connected: @{bot_info.get('username')}")
        else:
            logger.error("Failed to connect to Telegram bot")
            return

        self.running = True
        self.task = asyncio.create_task(self._poll_loop())
        logger.info("Telegram long polling started")

    async def stop(self) -> None:
        """Stop the polling loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Telegram long polling stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self.running:
            try:
                updates = await self.service.get_updates(
                    offset=self._offset,
                    timeout=30,
                )

                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        self._offset = update_id + 1

                    try:
                        await self.handler(update)
                    except Exception as e:
                        logger.error(f"Error handling update: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)  # Wait before retry


# Singleton instance
_telegram_service: TelegramService | None = None


def get_telegram_service() -> TelegramService:
    """Get or create TelegramService singleton.

    Returns:
        TelegramService instance.
    """
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service
