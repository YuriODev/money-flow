"""AI settings and preferences API endpoints.

This module provides endpoints for managing AI preferences including:
- Get/update AI preferences
- Conversation history management
- AI model selection

Routes:
    GET /api/v1/ai/preferences - Get AI preferences
    PUT /api/v1/ai/preferences - Update AI preferences
    GET /api/v1/ai/history/stats - Get conversation history stats
    DELETE /api/v1/ai/history - Clear conversation history
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.dependencies import get_db
from src.models.ai_preferences import AIPreferences
from src.models.rag import Conversation
from src.models.user import User
from src.schemas.ai_preferences import (
    AIPreferencesResponse,
    AIPreferencesUpdate,
    ClearHistoryRequest,
    ConversationHistoryStats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/preferences", response_model=AIPreferencesResponse)
async def get_ai_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIPreferencesResponse:
    """Get AI preferences for the current user.

    Creates default preferences if none exist.

    Returns:
        AIPreferencesResponse with user's AI settings.
    """
    # Get existing preferences
    result = await db.execute(select(AIPreferences).where(AIPreferences.user_id == current_user.id))
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Create default preferences
        prefs = AIPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        logger.info(f"Created default AI preferences for user {current_user.id}")

    return AIPreferencesResponse.model_validate(prefs)


@router.put("/preferences", response_model=AIPreferencesResponse)
async def update_ai_preferences(
    data: AIPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIPreferencesResponse:
    """Update AI preferences for the current user.

    Args:
        data: Fields to update (partial update supported).

    Returns:
        Updated AIPreferencesResponse.
    """
    # Get or create preferences
    result = await db.execute(select(AIPreferences).where(AIPreferences.user_id == current_user.id))
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = AIPreferences(user_id=current_user.id)
        db.add(prefs)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(prefs, field):
            setattr(prefs, field, value)

    prefs.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(prefs)

    logger.info(f"Updated AI preferences for user {current_user.id}: {list(update_data.keys())}")

    return AIPreferencesResponse.model_validate(prefs)


@router.post("/preferences/reset", response_model=AIPreferencesResponse)
async def reset_ai_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIPreferencesResponse:
    """Reset AI preferences to defaults.

    Returns:
        Reset AIPreferencesResponse.
    """
    # Delete existing preferences
    await db.execute(delete(AIPreferences).where(AIPreferences.user_id == current_user.id))

    # Create fresh defaults
    prefs = AIPreferences(user_id=current_user.id)
    db.add(prefs)
    await db.commit()
    await db.refresh(prefs)

    logger.info(f"Reset AI preferences for user {current_user.id}")

    return AIPreferencesResponse.model_validate(prefs)


@router.get("/history/stats", response_model=ConversationHistoryStats)
async def get_conversation_history_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationHistoryStats:
    """Get statistics about conversation history.

    Returns:
        ConversationHistoryStats with conversation counts and dates.
    """
    # Count total conversations
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get message count (approximation - count turns)
    # Each conversation has multiple turns stored in messages JSON
    msg_count = total * 5  # Rough estimate

    # Get oldest and newest
    oldest_result = await db.execute(
        select(func.min(Conversation.created_at)).where(Conversation.user_id == current_user.id)
    )
    oldest = oldest_result.scalar()

    newest_result = await db.execute(
        select(func.max(Conversation.created_at)).where(Conversation.user_id == current_user.id)
    )
    newest = newest_result.scalar()

    return ConversationHistoryStats(
        total_conversations=total,
        total_messages=msg_count,
        oldest_conversation=oldest,
        newest_conversation=newest,
    )


@router.delete("/history")
async def clear_conversation_history(
    data: ClearHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Clear conversation history.

    Args:
        data: Clear options (older_than_days, confirm).

    Returns:
        Dict with deleted count.

    Raises:
        HTTPException: If confirmation not provided.
    """
    if not data.confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set confirm=true to delete.",
        )

    # Build delete query
    stmt = delete(Conversation).where(Conversation.user_id == current_user.id)

    if data.older_than_days:
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(days=data.older_than_days)
        stmt = stmt.where(Conversation.created_at < cutoff)

    result = await db.execute(stmt)
    await db.commit()

    deleted = result.rowcount
    logger.info(f"Cleared {deleted} conversations for user {current_user.id}")

    return {"deleted": deleted, "message": f"Deleted {deleted} conversations"}
