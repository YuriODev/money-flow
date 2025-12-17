"""Pydantic schemas for notification preferences.

This module defines request/response schemas for notification settings
and Telegram integration endpoints.
"""

from datetime import time
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


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Schema for notification preferences response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    telegram: TelegramStatus


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
    }
