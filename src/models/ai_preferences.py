"""AI preferences model for user AI assistant settings.

This module provides the AIPreferences model for storing user preferences
related to the AI assistant, icon generation, and automation features.

Example:
    >>> from src.models.ai_preferences import AIPreferences
    >>> prefs = AIPreferences(
    ...     user_id="user-uuid",
    ...     ai_enabled=True,
    ...     auto_categorization=True,
    ...     suggestion_frequency="normal",
    ... )
"""

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class SuggestionFrequency(str, Enum):
    """How often AI offers suggestions.

    Attributes:
        OFF: No suggestions.
        MINIMAL: Only critical suggestions.
        NORMAL: Balanced suggestions.
        PROACTIVE: Frequent proactive suggestions.
    """

    OFF = "off"
    MINIMAL = "minimal"
    NORMAL = "normal"
    PROACTIVE = "proactive"


class AIModel(str, Enum):
    """Available AI models.

    Attributes:
        HAIKU: Claude Haiku (fast, cost-effective).
        SONNET: Claude Sonnet (balanced).
        OPUS: Claude Opus (most capable).
    """

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class IconGenerationStyle(str, Enum):
    """Style for AI-generated icons.

    Attributes:
        MINIMAL: Simple, flat icons.
        BRANDED: Branded-style icons.
        PLAYFUL: Fun, colorful icons.
        CORPORATE: Professional, corporate style.
    """

    MINIMAL = "minimal"
    BRANDED = "branded"
    PLAYFUL = "playful"
    CORPORATE = "corporate"


class AIPreferences(Base):
    """User AI preferences and settings.

    Stores all AI-related preferences including:
    - AI assistant toggle and model selection
    - Auto-categorization settings
    - Icon generation preferences
    - Suggestion frequency
    - Conversation history settings
    - Confidence thresholds

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner user ID (one-to-one).
        ai_enabled: Whether AI assistant is enabled.
        preferred_model: Preferred AI model.
        auto_categorization: Auto-categorize subscriptions.
        smart_suggestions: Enable smart suggestions.
        suggestion_frequency: How often to suggest.
        confidence_threshold: Minimum confidence for auto-actions.
        icon_generation_enabled: Allow AI icon generation.
        icon_style: Style for generated icons.
        icon_size: Preferred icon size.
        conversation_history_enabled: Save conversation history.
        conversation_history_days: Days to keep history.
        natural_language_parsing: Enable NL command parsing.
        learn_from_corrections: Learn from user corrections.
        privacy_mode: Minimize data sent to AI.
        custom_instructions: Custom instructions for AI.
        created_at: When preferences were created.
        updated_at: When preferences were last updated.

    Example:
        >>> prefs = AIPreferences(user_id="user-uuid")
        >>> prefs.ai_enabled = True
        >>> prefs.preferred_model = AIModel.SONNET
    """

    __tablename__ = "ai_preferences"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # User relationship (one-to-one)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # AI Assistant Settings
    ai_enabled: Mapped[bool] = mapped_column(
        default=True,
        comment="Whether AI assistant is enabled",
    )
    preferred_model: Mapped[AIModel] = mapped_column(
        SQLEnum(AIModel, name="aimodel"),
        default=AIModel.HAIKU,
        comment="Preferred AI model",
    )

    # Auto-categorization Settings
    auto_categorization: Mapped[bool] = mapped_column(
        default=True,
        comment="Auto-categorize new subscriptions",
    )
    auto_icon_assignment: Mapped[bool] = mapped_column(
        default=True,
        comment="Auto-assign icons to subscriptions",
    )

    # Suggestion Settings
    smart_suggestions: Mapped[bool] = mapped_column(
        default=True,
        comment="Enable smart suggestions",
    )
    suggestion_frequency: Mapped[SuggestionFrequency] = mapped_column(
        SQLEnum(SuggestionFrequency, name="suggestionfrequency"),
        default=SuggestionFrequency.NORMAL,
        comment="How often to show suggestions",
    )
    confidence_threshold: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        comment="Minimum confidence for auto-actions (0.0-1.0)",
    )

    # Icon Generation Settings
    icon_generation_enabled: Mapped[bool] = mapped_column(
        default=False,
        comment="Allow AI to generate icons",
    )
    icon_style: Mapped[IconGenerationStyle] = mapped_column(
        SQLEnum(IconGenerationStyle, name="icongenerationstyle"),
        default=IconGenerationStyle.BRANDED,
        comment="Style for AI-generated icons",
    )
    icon_size: Mapped[int] = mapped_column(
        Integer,
        default=128,
        comment="Preferred icon size in pixels",
    )

    # Conversation History Settings
    conversation_history_enabled: Mapped[bool] = mapped_column(
        default=True,
        comment="Save conversation history",
    )
    conversation_history_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        comment="Days to keep conversation history",
    )

    # Natural Language Settings
    natural_language_parsing: Mapped[bool] = mapped_column(
        default=True,
        comment="Enable natural language command parsing",
    )
    learn_from_corrections: Mapped[bool] = mapped_column(
        default=True,
        comment="Learn from user corrections",
    )

    # Privacy Settings
    privacy_mode: Mapped[bool] = mapped_column(
        default=False,
        comment="Minimize data sent to AI",
    )

    # Custom Instructions
    custom_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Custom instructions for AI assistant",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="ai_preferences",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<AIPreferences(user_id={self.user_id}, ai_enabled={self.ai_enabled})>"

    @property
    def is_fully_enabled(self) -> bool:
        """Check if AI features are fully enabled.

        Returns:
            True if AI, suggestions, and NL parsing are all enabled.
        """
        return self.ai_enabled and self.smart_suggestions and self.natural_language_parsing

    @property
    def should_auto_categorize(self) -> bool:
        """Check if auto-categorization should run.

        Returns:
            True if AI and auto-categorization are enabled.
        """
        return self.ai_enabled and self.auto_categorization

    @property
    def should_suggest(self) -> bool:
        """Check if suggestions should be shown.

        Returns:
            True if suggestions are enabled and frequency is not off.
        """
        return (
            self.ai_enabled
            and self.smart_suggestions
            and self.suggestion_frequency != SuggestionFrequency.OFF
        )

    def meets_confidence_threshold(self, confidence: float) -> bool:
        """Check if a confidence score meets the threshold.

        Args:
            confidence: The confidence score to check (0.0-1.0).

        Returns:
            True if confidence meets or exceeds threshold.
        """
        return confidence >= self.confidence_threshold

    def clear_conversation_history_cutoff(self) -> datetime:
        """Get the cutoff date for clearing conversation history.

        Returns:
            Datetime before which history should be cleared.
        """
        from datetime import timedelta

        return datetime.now(UTC) - timedelta(days=self.conversation_history_days)
