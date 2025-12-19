"""Pydantic schemas for AI preferences API.

This module provides request/response schemas for AI preferences endpoints.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SuggestionFrequencyEnum(str, Enum):
    """How often AI offers suggestions."""

    OFF = "off"
    MINIMAL = "minimal"
    NORMAL = "normal"
    PROACTIVE = "proactive"


class AIModelEnum(str, Enum):
    """Available AI models."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class IconGenerationStyleEnum(str, Enum):
    """Style for AI-generated icons."""

    MINIMAL = "minimal"
    BRANDED = "branded"
    PLAYFUL = "playful"
    CORPORATE = "corporate"


class AIPreferencesResponse(BaseModel):
    """AI preferences response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    # AI Assistant Settings
    ai_enabled: bool = True
    preferred_model: AIModelEnum = AIModelEnum.HAIKU

    # Auto-categorization Settings
    auto_categorization: bool = True
    auto_icon_assignment: bool = True

    # Suggestion Settings
    smart_suggestions: bool = True
    suggestion_frequency: SuggestionFrequencyEnum = SuggestionFrequencyEnum.NORMAL
    confidence_threshold: float = 0.7

    # Icon Generation Settings
    icon_generation_enabled: bool = False
    icon_style: IconGenerationStyleEnum = IconGenerationStyleEnum.BRANDED
    icon_size: int = 128

    # Conversation History Settings
    conversation_history_enabled: bool = True
    conversation_history_days: int = 30

    # Natural Language Settings
    natural_language_parsing: bool = True
    learn_from_corrections: bool = True

    # Privacy Settings
    privacy_mode: bool = False

    # Custom Instructions
    custom_instructions: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime


class AIPreferencesUpdate(BaseModel):
    """AI preferences update request."""

    # AI Assistant Settings
    ai_enabled: bool | None = None
    preferred_model: AIModelEnum | None = None

    # Auto-categorization Settings
    auto_categorization: bool | None = None
    auto_icon_assignment: bool | None = None

    # Suggestion Settings
    smart_suggestions: bool | None = None
    suggestion_frequency: SuggestionFrequencyEnum | None = None
    confidence_threshold: float | None = Field(None, ge=0.0, le=1.0)

    # Icon Generation Settings
    icon_generation_enabled: bool | None = None
    icon_style: IconGenerationStyleEnum | None = None
    icon_size: int | None = Field(None, ge=32, le=512)

    # Conversation History Settings
    conversation_history_enabled: bool | None = None
    conversation_history_days: int | None = Field(None, ge=1, le=365)

    # Natural Language Settings
    natural_language_parsing: bool | None = None
    learn_from_corrections: bool | None = None

    # Privacy Settings
    privacy_mode: bool | None = None

    # Custom Instructions
    custom_instructions: str | None = Field(None, max_length=2000)


class AIPreferencesCreate(BaseModel):
    """AI preferences create request (for initialization)."""

    # All fields optional with defaults
    ai_enabled: bool = True
    preferred_model: AIModelEnum = AIModelEnum.HAIKU
    auto_categorization: bool = True
    auto_icon_assignment: bool = True
    smart_suggestions: bool = True
    suggestion_frequency: SuggestionFrequencyEnum = SuggestionFrequencyEnum.NORMAL
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    icon_generation_enabled: bool = False
    icon_style: IconGenerationStyleEnum = IconGenerationStyleEnum.BRANDED
    icon_size: int = Field(128, ge=32, le=512)
    conversation_history_enabled: bool = True
    conversation_history_days: int = Field(30, ge=1, le=365)
    natural_language_parsing: bool = True
    learn_from_corrections: bool = True
    privacy_mode: bool = False
    custom_instructions: str | None = Field(None, max_length=2000)


class ConversationHistoryStats(BaseModel):
    """Stats about conversation history."""

    total_conversations: int
    total_messages: int
    oldest_conversation: datetime | None
    newest_conversation: datetime | None


class ClearHistoryRequest(BaseModel):
    """Request to clear conversation history."""

    older_than_days: int | None = Field(None, ge=1, description="Clear only older than N days")
    confirm: bool = Field(False, description="Confirm deletion")
