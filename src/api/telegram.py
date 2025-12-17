"""Telegram webhook handler.

This module provides the webhook endpoint for receiving Telegram bot updates
and handling user interactions.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.dependencies import get_db
from src.models.notification import NotificationPreferences
from src.services.telegram_service import get_telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


async def process_message(
    db: AsyncSession,
    chat_id: str,
    text: str,
    username: str | None = None,
    first_name: str | None = None,
) -> None:
    """Process an incoming Telegram message.

    Args:
        db: Database session.
        chat_id: Telegram chat ID.
        text: Message text.
        username: Sender's Telegram username.
        first_name: Sender's first name.
    """
    telegram_service = get_telegram_service()
    text = text.strip()

    # Handle commands
    if text.startswith("/"):
        command = text.split()[0].lower()

        if command == "/start":
            # Check if there's a verification code in the command
            parts = text.split()
            if len(parts) > 1:
                code = parts[1]
                await verify_code(db, chat_id, code, username)
            else:
                await telegram_service.send_verification_prompt(chat_id, first_name)

        elif command == "/status":
            await send_status(db, chat_id)

        elif command == "/pause":
            await toggle_notifications(db, chat_id, enabled=False)

        elif command == "/resume":
            await toggle_notifications(db, chat_id, enabled=True)

        elif command == "/help":
            await send_help(chat_id)

        elif command == "/stop":
            await unlink_account(db, chat_id)

        else:
            await telegram_service.send_message(
                chat_id,
                "Unknown command. Send /help to see available commands.",
            )

    else:
        # Treat plain text as potential verification code
        if len(text) == 6 and text.isalnum():
            await verify_code(db, chat_id, text, username)
        else:
            await telegram_service.send_message(
                chat_id,
                "To link your account, please enter the 6-character verification code from the Money Flow app.\n\n"
                "Send /help to see available commands.",
            )


async def verify_code(
    db: AsyncSession,
    chat_id: str,
    code: str,
    username: str | None = None,
) -> None:
    """Verify a linking code and complete account linking.

    Args:
        db: Database session.
        chat_id: Telegram chat ID.
        code: Verification code.
        username: Sender's Telegram username.
    """
    telegram_service = get_telegram_service()

    # Find preferences with matching verification code
    result = await db.execute(
        select(NotificationPreferences).where(
            NotificationPreferences.telegram_verification_code == code.upper()
        )
    )
    prefs = result.scalar_one_or_none()

    if prefs and prefs.verify_code(code):
        # Complete linking
        prefs.telegram_chat_id = chat_id
        prefs.telegram_username = username
        prefs.telegram_verified = True
        prefs.telegram_enabled = True
        prefs.clear_verification()

        await db.commit()

        logger.info(f"Telegram linked for user {prefs.user_id} with chat_id {chat_id}")
        await telegram_service.send_verification_success(chat_id)
    else:
        await telegram_service.send_verification_failed(chat_id)


async def send_status(db: AsyncSession, chat_id: str) -> None:
    """Send notification status to user.

    Args:
        db: Database session.
        chat_id: Telegram chat ID.
    """
    telegram_service = get_telegram_service()

    # Find preferences by chat_id
    result = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.telegram_chat_id == chat_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        await telegram_service.send_message(
            chat_id,
            "Your Telegram account is not linked to any Money Flow account.\n\n"
            "Please generate a verification code in the Money Flow app settings.",
        )
        return

    status_emoji = "✅" if prefs.reminder_enabled else "⏸️"
    telegram_emoji = "🟢" if prefs.telegram_enabled else "🔴"

    message = f"""
📊 <b>Notification Status</b>

{telegram_emoji} Telegram: {"Enabled" if prefs.telegram_enabled else "Disabled"}
{status_emoji} Reminders: {"Enabled" if prefs.reminder_enabled else "Paused"}
📅 Reminder days before: {prefs.reminder_days_before}
⏰ Reminder time: {prefs.reminder_time.strftime("%H:%M")}

📬 Daily digest: {"Yes" if prefs.daily_digest else "No"}
📆 Weekly digest: {"Yes" if prefs.weekly_digest else "No"}

Commands:
/pause - Pause notifications
/resume - Resume notifications
/stop - Unlink account
"""
    await telegram_service.send_message(chat_id, message.strip())


async def toggle_notifications(db: AsyncSession, chat_id: str, enabled: bool) -> None:
    """Toggle notifications on/off.

    Args:
        db: Database session.
        chat_id: Telegram chat ID.
        enabled: Whether to enable or disable.
    """
    telegram_service = get_telegram_service()

    result = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.telegram_chat_id == chat_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        await telegram_service.send_message(
            chat_id,
            "Your Telegram account is not linked to any Money Flow account.",
        )
        return

    prefs.reminder_enabled = enabled
    await db.commit()

    if enabled:
        await telegram_service.send_message(
            chat_id,
            "✅ Notifications have been resumed. You'll receive payment reminders again.",
        )
    else:
        await telegram_service.send_message(
            chat_id,
            "⏸️ Notifications have been paused. You won't receive reminders until you /resume.",
        )


async def unlink_account(db: AsyncSession, chat_id: str) -> None:
    """Unlink Telegram account.

    Args:
        db: Database session.
        chat_id: Telegram chat ID.
    """
    telegram_service = get_telegram_service()

    result = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.telegram_chat_id == chat_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        await telegram_service.send_message(
            chat_id,
            "Your Telegram account is not linked to any Money Flow account.",
        )
        return

    # Clear Telegram settings
    prefs.telegram_chat_id = None
    prefs.telegram_username = None
    prefs.telegram_verified = False
    prefs.telegram_enabled = False

    await db.commit()

    await telegram_service.send_message(
        chat_id,
        "👋 Your Telegram account has been unlinked from Money Flow.\n\n"
        "You will no longer receive notifications here. "
        "To reconnect, generate a new verification code in the app settings.",
    )


async def send_help(chat_id: str) -> None:
    """Send help message.

    Args:
        chat_id: Telegram chat ID.
    """
    telegram_service = get_telegram_service()

    message = """
💡 <b>Money Flow Bot Help</b>

<b>Available Commands:</b>
/start - Start the bot / link your account
/status - Check your notification settings
/pause - Temporarily pause notifications
/resume - Resume paused notifications
/stop - Unlink your account
/help - Show this help message

<b>Linking Your Account:</b>
1. Go to Settings in the Money Flow app
2. Click "Connect Telegram"
3. Copy the verification code
4. Send the code here

<b>Payment Reminders:</b>
You'll receive reminders before upcoming payments based on your settings in the app.

Need help? Contact support at support@moneyflow.app
"""
    await telegram_service.send_message(chat_id, message.strip())


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """Handle Telegram webhook updates.

    Receives and processes updates from the Telegram Bot API.
    Updates include messages, commands, and other events.

    Args:
        request: FastAPI request object.
        x_telegram_bot_api_secret_token: Webhook secret for verification.

    Returns:
        Simple OK response.

    Raises:
        HTTPException: If webhook verification fails.
    """
    # Verify webhook secret if configured
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            logger.warning("Invalid Telegram webhook secret")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook secret",
            )

    try:
        update: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    # Get database session
    async for db in get_db():
        try:
            # Handle message updates
            message = update.get("message")
            if message:
                chat = message.get("chat", {})
                chat_id = str(chat.get("id"))
                text = message.get("text", "")
                user = message.get("from", {})
                username = user.get("username")
                first_name = user.get("first_name")

                if text:
                    await process_message(db, chat_id, text, username, first_name)

            # Handle callback queries (button clicks) - future enhancement
            callback_query = update.get("callback_query")
            if callback_query:
                # For future button-based interactions
                pass

        except Exception as e:
            logger.exception(f"Error processing Telegram update: {e}")
            # Don't raise - we want to return 200 to Telegram

    return {"status": "ok"}
