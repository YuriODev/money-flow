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
    TriggerRemindersRequest,
    TriggerRemindersResponse,
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


@router.post("/trigger", response_model=TriggerRemindersResponse)
async def trigger_reminder_task(
    request: TriggerRemindersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TriggerRemindersResponse:
    """Manually trigger a reminder task for testing.

    This endpoint allows testing reminder delivery without waiting for
    scheduled cron jobs. Only triggers reminders for the current user.

    Args:
        request: Task type to trigger.

    Returns:
        TriggerRemindersResponse with task result.

    Raises:
        HTTPException: If Telegram is not linked or task fails.
    """
    from datetime import date, timedelta

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.models.subscription import Subscription

    prefs = await get_or_create_preferences(db, current_user.id)

    if not prefs.is_telegram_linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram is not linked. Please link your Telegram account first.",
        )

    telegram_service = get_telegram_service()
    task_type = request.task_type
    result: dict = {}

    try:
        if task_type == "reminders":
            # Send reminders for upcoming payments
            today = date.today()
            target_date = today + timedelta(days=prefs.reminder_days_before)

            stmt = (
                select(Subscription)
                .where(Subscription.user_id == current_user.id)
                .where(Subscription.is_active.is_(True))
                .where(Subscription.next_payment_date <= target_date)
                .where(Subscription.next_payment_date >= today)
                .options(selectinload(Subscription.payment_card))
            )
            subs_result = await db.execute(stmt)
            subscriptions = list(subs_result.scalars().all())

            reminders_sent = 0
            for sub in subscriptions:
                days_until = (sub.next_payment_date - today).days if sub.next_payment_date else 0
                success = await telegram_service.send_reminder(
                    chat_id=prefs.telegram_chat_id,
                    subscription=sub,
                    days_until=days_until,
                )
                if success:
                    reminders_sent += 1

            result = {
                "subscriptions_found": len(subscriptions),
                "reminders_sent": reminders_sent,
            }
            message = f"Sent {reminders_sent} payment reminder(s)"

        elif task_type == "daily_digest":
            # Send daily digest
            today = date.today()
            week_end = today + timedelta(days=7)

            stmt = (
                select(Subscription)
                .where(Subscription.user_id == current_user.id)
                .where(Subscription.is_active.is_(True))
                .where(Subscription.next_payment_date >= today)
                .where(Subscription.next_payment_date <= week_end)
                .order_by(Subscription.next_payment_date)
            )
            subs_result = await db.execute(stmt)
            subscriptions = list(subs_result.scalars().all())

            currency = (
                current_user.preferences.get("currency", "GBP")
                if current_user.preferences
                else "GBP"
            )
            success = await telegram_service.send_daily_digest(
                chat_id=prefs.telegram_chat_id,
                subscriptions=subscriptions,
                currency=currency,
            )

            result = {"subscriptions_included": len(subscriptions), "sent": success}
            message = "Daily digest sent" if success else "Failed to send daily digest"

        elif task_type == "weekly_digest":
            # Send weekly digest
            today = date.today()
            week_end = today + timedelta(days=7)

            stmt = (
                select(Subscription)
                .where(Subscription.user_id == current_user.id)
                .where(Subscription.is_active.is_(True))
                .where(Subscription.next_payment_date >= today)
                .where(Subscription.next_payment_date <= week_end)
                .order_by(Subscription.next_payment_date)
            )
            subs_result = await db.execute(stmt)
            subscriptions = list(subs_result.scalars().all())

            currency = (
                current_user.preferences.get("currency", "GBP")
                if current_user.preferences
                else "GBP"
            )
            success = await telegram_service.send_weekly_digest(
                chat_id=prefs.telegram_chat_id,
                subscriptions=subscriptions,
                currency=currency,
            )

            result = {"subscriptions_included": len(subscriptions), "sent": success}
            message = "Weekly digest sent" if success else "Failed to send weekly digest"

        elif task_type == "overdue":
            # Send overdue alerts
            today = date.today()

            stmt = (
                select(Subscription)
                .where(Subscription.user_id == current_user.id)
                .where(Subscription.is_active.is_(True))
                .where(Subscription.next_payment_date < today)
            )
            subs_result = await db.execute(stmt)
            overdue_subscriptions = list(subs_result.scalars().all())

            alerts_sent = 0
            for sub in overdue_subscriptions:
                days_overdue = (today - sub.next_payment_date).days if sub.next_payment_date else 0
                success = await telegram_service.send_reminder(
                    chat_id=prefs.telegram_chat_id,
                    subscription=sub,
                    days_until=-days_overdue,  # Negative = overdue
                )
                if success:
                    alerts_sent += 1

            result = {"overdue_found": len(overdue_subscriptions), "alerts_sent": alerts_sent}
            message = f"Sent {alerts_sent} overdue alert(s)"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown task type: {task_type}. Valid types: reminders, daily_digest, weekly_digest, overdue",
            )

        logger.info(f"Triggered {task_type} task for user {current_user.id}: {result}")

        return TriggerRemindersResponse(
            success=True,
            task_type=task_type,
            message=message,
            result=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger {task_type} task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger {task_type} task: {str(e)}",
        )
