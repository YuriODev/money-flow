"""User API endpoints.

This module provides endpoints for user-related operations that are not
authentication-specific, such as user preferences management.

Endpoints:
    GET /users/preferences - Get current user preferences
    PUT /users/preferences - Update user preferences

Security:
    All endpoints require authentication via JWT bearer token.
"""

import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.core.dependencies import get_db
from src.models.user import User
from src.schemas.user import UserPreferencesResponse, UserPreferencesUpdate
from src.security.rate_limit import limiter

router = APIRouter()

# Rate limit constants
rate_limit_read = "30/minute"
rate_limit_write = "10/minute"

# Default preferences
DEFAULT_PREFERENCES = {
    "currency": "GBP",
    "date_format": "DD/MM/YYYY",
    "number_format": "1,234.56",
    "theme": "system",
    "default_view": "list",
    "compact_mode": False,
    "week_start": "monday",
    "timezone": "UTC",
    "language": "en",
    "show_currency_symbol": True,
    "default_card_id": None,
    "default_category_id": None,
}


def _parse_preferences(preferences_str: str | None) -> dict:
    """Parse preferences JSON string to dict.

    Args:
        preferences_str: JSON string or None.

    Returns:
        Parsed dict with defaults applied.
    """
    if not preferences_str:
        return DEFAULT_PREFERENCES.copy()

    try:
        stored = json.loads(preferences_str)
        # Merge with defaults to ensure all keys exist
        result = DEFAULT_PREFERENCES.copy()
        result.update(stored)
        return result
    except (json.JSONDecodeError, TypeError):
        return DEFAULT_PREFERENCES.copy()


@router.get(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Get the current user's preferences.",
)
@limiter.limit(rate_limit_read)
async def get_preferences(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> UserPreferencesResponse:
    """Get current user's preferences.

    Returns the user's preferences merged with defaults for any
    unset values.

    Args:
        current_user: Authenticated user from dependency.

    Returns:
        UserPreferencesResponse with all preference values.

    Example:
        GET /users/preferences
        Authorization: Bearer eyJ...

        Response:
        {
            "currency": "GBP",
            "date_format": "DD/MM/YYYY",
            "theme": "dark",
            ...
        }
    """
    prefs = _parse_preferences(current_user.preferences)
    return UserPreferencesResponse(**prefs)


@router.put(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Update user preferences",
    description="Update the current user's preferences (partial update).",
)
@limiter.limit(rate_limit_write)
async def update_preferences(
    request: Request,
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """Update current user's preferences.

    Performs a partial update - only provided fields are updated.
    Missing fields retain their current values.

    Args:
        preferences: Preference updates (only non-null fields applied).
        current_user: Authenticated user from dependency.
        db: Database session.

    Returns:
        UserPreferencesResponse with updated preference values.

    Example:
        PUT /users/preferences
        Authorization: Bearer eyJ...
        {
            "currency": "USD",
            "theme": "dark"
        }

        Response:
        {
            "currency": "USD",
            "date_format": "DD/MM/YYYY",
            "theme": "dark",
            ...
        }
    """
    # Parse existing preferences
    current_prefs = _parse_preferences(current_user.preferences)

    # Apply updates (only non-null values)
    update_data = preferences.model_dump(exclude_unset=True, exclude_none=True)
    current_prefs.update(update_data)

    # Save to database
    current_user.preferences = json.dumps(current_prefs)
    await db.commit()
    await db.refresh(current_user)

    return UserPreferencesResponse(**current_prefs)
