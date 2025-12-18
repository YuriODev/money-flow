"""Telegram bot update handler.

This module processes incoming Telegram messages and handles
user verification and bot commands.
"""

import logging
import re
from typing import Any

from sqlalchemy import select

from src.db.database import async_session_maker
from src.models.notification import NotificationPreferences
from src.services.telegram_service import TelegramService, get_telegram_service

logger = logging.getLogger(__name__)

# Verification code pattern (6 hex characters)
VERIFICATION_CODE_PATTERN = re.compile(r"^[A-Fa-f0-9]{6}$")


async def handle_telegram_update(update: dict[str, Any]) -> None:
    """Process an incoming Telegram update.

    Handles:
    - /start command: Send welcome message
    - Verification codes: Link Telegram account
    - /status command: Check notification status
    - /help command: Show help message

    Args:
        update: Telegram update object.
    """
    message = update.get("message")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = message.get("text", "").strip()
    username = message.get("from", {}).get("username")

    if not chat_id or not text:
        return

    telegram_service = get_telegram_service()

    # Handle commands
    if text.startswith("/"):
        await handle_command(telegram_service, chat_id, text, username)
        return

    # Check if it looks like a verification code
    if VERIFICATION_CODE_PATTERN.match(text):
        await handle_verification_code(telegram_service, chat_id, text, username)
        return

    # Unknown message - prompt for code
    await telegram_service.send_message(
        chat_id,
        "I didn't understand that. Please send your 6-character verification code "
        "from the Money Flow app, or use /help for assistance.",
    )


async def handle_command(
    service: TelegramService,
    chat_id: str,
    text: str,
    username: str | None,
) -> None:
    """Handle a bot command.

    Args:
        service: TelegramService instance.
        chat_id: Telegram chat ID.
        text: Command text.
        username: User's Telegram username.
    """
    command = text.split()[0].lower()

    if command == "/start":
        await service.send_verification_prompt(chat_id, username)

    elif command == "/help":
        await service.send_message(
            chat_id,
            """
<b>Money Flow Bot Help</b>

To link your account:
1. Go to Settings in the Money Flow app
2. Click "Connect Telegram"
3. Copy the 6-character code
4. Send the code here

<b>Commands:</b>
/start - Start linking your account
/status - Check your notification status
/help - Show this help message
""",
        )

    elif command == "/status":
        await handle_status_command(service, chat_id)

    else:
        await service.send_message(
            chat_id,
            "Unknown command. Use /help to see available commands.",
        )


async def handle_status_command(service: TelegramService, chat_id: str) -> None:
    """Handle /status command.

    Args:
        service: TelegramService instance.
        chat_id: Telegram chat ID.
    """
    async with async_session_maker() as db:
        # Find user by chat_id
        result = await db.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.telegram_chat_id == chat_id
            )
        )
        prefs = result.scalar_one_or_none()

        if prefs and prefs.is_telegram_linked:
            status = "✅ <b>Connected</b>\n\n"
            status += f"Reminders: {'Enabled' if prefs.reminder_enabled else 'Disabled'}\n"
            status += f"Days before: {prefs.reminder_days_before}\n"
            status += f"Daily digest: {'Enabled' if prefs.daily_digest else 'Disabled'}\n"
            status += f"Weekly digest: {'Enabled' if prefs.weekly_digest else 'Disabled'}\n"
            await service.send_message(chat_id, status)
        else:
            await service.send_message(
                chat_id,
                "❌ <b>Not Connected</b>\n\n"
                "Your Telegram is not linked to a Money Flow account.\n"
                "Go to Settings in the app to connect.",
            )


async def handle_verification_code(
    service: TelegramService,
    chat_id: str,
    code: str,
    username: str | None,
) -> None:
    """Handle a verification code message.

    Args:
        service: TelegramService instance.
        chat_id: Telegram chat ID.
        code: Verification code from user.
        username: User's Telegram username.
    """
    async with async_session_maker() as db:
        # Find user with this verification code
        result = await db.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.telegram_verification_code == code.upper()
            )
        )
        prefs = result.scalar_one_or_none()

        if prefs and prefs.verify_code(code):
            # Link the account
            prefs.telegram_chat_id = chat_id
            prefs.telegram_username = username
            prefs.telegram_verified = True
            prefs.telegram_enabled = True
            prefs.clear_verification()

            await db.commit()

            logger.info(f"Telegram account linked for user {prefs.user_id}")
            await service.send_verification_success(chat_id)
        else:
            logger.warning(f"Invalid verification code attempt: {code}")
            await service.send_verification_failed(chat_id)
