"""Pydantic schemas for notification preferences and history.

This module defines request/response schemas for notification settings,
Telegram integration, push notifications, and notification history endpoints.
"""

from datetime import datetime, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferencesBase(BaseModel):
    """Base schema for notification preferences."""

    # Reminder settings
    reminder_enabled: bool = True
    reminder_days_before: Annotated[int, Field(ge=1, le=30)] = 3
    reminder_time: time = time(9, 0)  # 09:00
    overdue_alerts: bool = True

    # Digest settings
    daily_digest: bool = False
    weekly_digest: bool = True
    weekly_digest_day: Annotated[int, Field(ge=0, le=6)] = 0  # 0=Monday

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class NotificationPreferencesCreate(NotificationPreferencesBase):
    """Schema for creating notification preferences."""

    pass


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences.

    All fields are optional to allow partial updates.
    """

    # Reminder settings
    reminder_enabled: bool | None = None
    reminder_days_before: Annotated[int, Field(ge=1, le=30)] | None = None
    reminder_time: time | None = None
    overdue_alerts: bool | None = None

    # Digest settings
    daily_digest: bool | None = None
    weekly_digest: bool | None = None
    weekly_digest_day: Annotated[int, Field(ge=0, le=6)] | None = None

    # Quiet hours
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class TelegramStatus(BaseModel):
    """Schema for Telegram connection status."""

    enabled: bool = False
    verified: bool = False
    username: str | None = None
    linked: bool = False  # True if enabled, verified, and has chat_id


class PushStatus(BaseModel):
    """Schema for Web Push connection status."""

    enabled: bool = False
    verified: bool = False
    linked: bool = False  # True if enabled, verified, and has subscription


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Schema for notification preferences response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    telegram: TelegramStatus
    push: PushStatus
    email_enabled: bool = True


class TelegramLinkRequest(BaseModel):
    """Schema for initiating Telegram link."""

    pass  # No fields needed, user_id from auth


class TelegramLinkResponse(BaseModel):
    """Schema for Telegram link initiation response."""

    verification_code: str
    bot_username: str
    bot_link: str
    expires_in_minutes: int = 10
    instructions: str


class TelegramVerifyRequest(BaseModel):
    """Schema for verifying Telegram link (from webhook)."""

    code: str


class TelegramVerifyResponse(BaseModel):
    """Schema for Telegram verification response."""

    success: bool
    message: str
    telegram: TelegramStatus | None = None


class TelegramUnlinkResponse(BaseModel):
    """Schema for Telegram unlink response."""

    success: bool
    message: str


class TestNotificationRequest(BaseModel):
    """Schema for test notification request."""

    pass  # No fields needed


class TestNotificationResponse(BaseModel):
    """Schema for test notification response."""

    success: bool
    message: str
    channel: str = "telegram"


class PushSubscriptionKeys(BaseModel):
    """Schema for Web Push subscription keys."""

    p256dh: str
    auth: str


class PushSubscriptionRequest(BaseModel):
    """Schema for Web Push subscription.

    This is the subscription object returned by the browser's
    PushManager.subscribe() method.
    """

    endpoint: str
    keys: PushSubscriptionKeys
    expiration_time: int | None = None


class PushSubscribeResponse(BaseModel):
    """Schema for push subscription response."""

    success: bool
    message: str
    push: PushStatus | None = None


class PushUnsubscribeResponse(BaseModel):
    """Schema for push unsubscribe response."""

    success: bool
    message: str


class PushVapidKeyResponse(BaseModel):
    """Schema for VAPID public key response."""

    public_key: str
    is_configured: bool


class TriggerRemindersRequest(BaseModel):
    """Schema for manually triggering reminder tasks."""

    task_type: str = "reminders"  # reminders, daily_digest, weekly_digest, overdue


class TriggerRemindersResponse(BaseModel):
    """Schema for trigger reminders response."""

    success: bool
    task_type: str
    message: str
    result: dict | None = None


# Helper function to build response from model
def preferences_to_response(prefs) -> dict:
    """Convert NotificationPreferences model to response dict.

    Args:
        prefs: NotificationPreferences model instance.

    Returns:
        Dict suitable for NotificationPreferencesResponse.
    """
    return {
        "id": prefs.id,
        "user_id": prefs.user_id,
        "reminder_enabled": prefs.reminder_enabled,
        "reminder_days_before": prefs.reminder_days_before,
        "reminder_time": prefs.reminder_time,
        "overdue_alerts": prefs.overdue_alerts,
        "daily_digest": prefs.daily_digest,
        "weekly_digest": prefs.weekly_digest,
        "weekly_digest_day": prefs.weekly_digest_day,
        "quiet_hours_enabled": prefs.quiet_hours_enabled,
        "quiet_hours_start": prefs.quiet_hours_start,
        "quiet_hours_end": prefs.quiet_hours_end,
        "telegram": TelegramStatus(
            enabled=prefs.telegram_enabled,
            verified=prefs.telegram_verified,
            username=prefs.telegram_username,
            linked=prefs.is_telegram_linked,
        ),
        "push": PushStatus(
            enabled=prefs.push_enabled,
            verified=prefs.push_verified,
            linked=prefs.is_push_linked,
        ),
        "email_enabled": prefs.email_enabled,
    }


# ============== Notification History Schemas ==============


class NotificationHistoryResponse(BaseModel):
    """Schema for notification history response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    subscription_id: str | None = None
    channel: str
    notification_type: str
    title: str
    body: str
    status: str
    error_message: str | None = None
    sent_at: datetime
    delivered_at: datetime | None = None
    extra_data: dict | None = None


class NotificationHistoryListResponse(BaseModel):
    """Schema for paginated notification history list."""

    items: list[NotificationHistoryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationHistoryFilters(BaseModel):
    """Schema for filtering notification history."""

    channel: str | None = None  # telegram, email, push
    notification_type: str | None = None  # payment_reminder, daily_digest, etc.
    status: str | None = None  # sent, delivered, failed
    start_date: datetime | None = None
    end_date: datetime | None = None


def history_to_response(history) -> dict:
    """Convert NotificationHistory model to response dict.

    Args:
        history: NotificationHistory model instance.

    Returns:
        Dict suitable for NotificationHistoryResponse.
    """
    return {
        "id": history.id,
        "user_id": history.user_id,
        "subscription_id": history.subscription_id,
        "channel": history.channel,
        "notification_type": history.notification_type,
        "title": history.title,
        "body": history.body,
        "status": history.status,
        "error_message": history.error_message,
        "sent_at": history.sent_at,
        "delivered_at": history.delivered_at,
        "extra_data": history.get_extra_data_dict(),
    }
