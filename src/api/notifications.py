"""Notification preferences API endpoints.

This module provides endpoints for managing user notification preferences
and Telegram integration.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.notification import NotificationPreferences
from src.models.user import User
from src.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    TelegramLinkResponse,
    TelegramStatus,
    TelegramUnlinkResponse,
    TestNotificationRequest,
    TestNotificationResponse,
    preferences_to_response,
)
from src.services.telegram_service import get_telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def get_or_create_preferences(db: AsyncSession, user_id: str) -> NotificationPreferences:
    """Get or create notification preferences for a user.

    Args:
        db: Database session.
        user_id: User ID.

    Returns:
        NotificationPreferences instance.
    """
    result = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = NotificationPreferences(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return prefs


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's notification preferences.

    Returns notification settings including Telegram connection status.
    Creates default preferences if none exist.

    Returns:
        NotificationPreferencesResponse with all settings.
    """
    prefs = await get_or_create_preferences(db, current_user.id)
    return preferences_to_response(prefs)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update notification preferences.

    Allows partial updates - only provided fields are modified.

    Args:
        updates: Fields to update.

    Returns:
        Updated NotificationPreferencesResponse.
    """
    prefs = await get_or_create_preferences(db, current_user.id)

    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)

    logger.info(f"Updated notification preferences for user {current_user.id}")
    return preferences_to_response(prefs)


@router.post("/telegram/link", response_model=TelegramLinkResponse)
async def initiate_telegram_link(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramLinkResponse:
    """Initiate Telegram account linking.

    Generates a verification code that the user must send to the
    Telegram bot to complete linking.

    Returns:
        TelegramLinkResponse with verification code and instructions.

    Raises:
        HTTPException: If Telegram bot is not configured.
    """
    telegram_service = get_telegram_service()

    if not telegram_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot is not configured",
        )

    prefs = await get_or_create_preferences(db, current_user.id)

    # Generate new verification code
    code = prefs.generate_verification_code()
    await db.commit()

    logger.info(f"Generated Telegram verification code for user {current_user.id}")

    return TelegramLinkResponse(
        verification_code=code,
        bot_username=telegram_service.bot_username,
        bot_link=telegram_service.bot_link,
        expires_in_minutes=10,
        instructions=(
            f"1. Open Telegram and search for @{telegram_service.bot_username}\n"
            f"2. Start a conversation with the bot\n"
            f"3. Send this code: {code}\n"
            f"4. The bot will confirm when linking is complete"
        ),
    )


@router.get("/telegram/status", response_model=TelegramStatus)
async def get_telegram_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramStatus:
    """Get current Telegram connection status.

    Returns:
        TelegramStatus with connection details.
    """
    prefs = await get_or_create_preferences(db, current_user.id)

    return TelegramStatus(
        enabled=prefs.telegram_enabled,
        verified=prefs.telegram_verified,
        username=prefs.telegram_username,
        linked=prefs.is_telegram_linked,
    )


@router.delete("/telegram/unlink", response_model=TelegramUnlinkResponse)
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramUnlinkResponse:
    """Unlink Telegram account.

    Removes Telegram integration and disables Telegram notifications.

    Returns:
        TelegramUnlinkResponse confirming unlinking.
    """
    prefs = await get_or_create_preferences(db, current_user.id)

    # Clear Telegram settings
    prefs.telegram_enabled = False
    prefs.telegram_chat_id = None
    prefs.telegram_username = None
    prefs.telegram_verified = False
    prefs.clear_verification()

    await db.commit()

    logger.info(f"Unlinked Telegram for user {current_user.id}")

    return TelegramUnlinkResponse(
        success=True,
        message="Telegram account has been unlinked successfully",
    )


@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    _request: TestNotificationRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestNotificationResponse:
    """Send a test notification.

    Sends a test message to verify the notification channel is working.

    Returns:
        TestNotificationResponse indicating success or failure.

    Raises:
        HTTPException: If Telegram is not linked or sending fails.
    """
    prefs = await get_or_create_preferences(db, current_user.id)

    if not prefs.is_telegram_linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram is not linked. Please link your Telegram account first.",
        )

    telegram_service = get_telegram_service()
    success = await telegram_service.send_test_notification(prefs.telegram_chat_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification. Please try again.",
        )

    logger.info(f"Sent test notification to user {current_user.id}")

    return TestNotificationResponse(
        success=True,
        message="Test notification sent successfully! Check your Telegram.",
        channel="telegram",
    )
