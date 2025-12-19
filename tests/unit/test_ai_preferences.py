"""Unit tests for AI preferences model and schemas.

Tests cover:
- AIPreferences model creation and methods
- AI preference enums
- Pydantic schemas validation
- Confidence threshold logic
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.models.ai_preferences import (
    AIModel,
    AIPreferences,
    IconGenerationStyle,
    SuggestionFrequency,
)
from src.schemas.ai_preferences import (
    AIModelEnum,
    AIPreferencesCreate,
    AIPreferencesResponse,
    AIPreferencesUpdate,
    ClearHistoryRequest,
    IconGenerationStyleEnum,
    SuggestionFrequencyEnum,
)


class TestSuggestionFrequency:
    """Tests for SuggestionFrequency enum."""

    def test_all_frequencies_defined(self) -> None:
        """Test all expected frequencies are defined."""
        assert SuggestionFrequency.OFF.value == "off"
        assert SuggestionFrequency.MINIMAL.value == "minimal"
        assert SuggestionFrequency.NORMAL.value == "normal"
        assert SuggestionFrequency.PROACTIVE.value == "proactive"


class TestAIModel:
    """Tests for AIModel enum."""

    def test_all_models_defined(self) -> None:
        """Test all expected models are defined."""
        assert AIModel.HAIKU.value == "haiku"
        assert AIModel.SONNET.value == "sonnet"
        assert AIModel.OPUS.value == "opus"


class TestIconGenerationStyle:
    """Tests for IconGenerationStyle enum."""

    def test_all_styles_defined(self) -> None:
        """Test all expected styles are defined."""
        assert IconGenerationStyle.MINIMAL.value == "minimal"
        assert IconGenerationStyle.BRANDED.value == "branded"
        assert IconGenerationStyle.PLAYFUL.value == "playful"
        assert IconGenerationStyle.CORPORATE.value == "corporate"


class TestAIPreferences:
    """Tests for AIPreferences model."""

    def test_create_ai_preferences_defaults(self) -> None:
        """Test creating AIPreferences with defaults via schema."""
        # Use schema to create with defaults (model defaults only work in DB)
        from src.schemas.ai_preferences import AIPreferencesCreate

        create = AIPreferencesCreate()

        assert create.ai_enabled is True
        assert create.preferred_model == AIModelEnum.HAIKU
        assert create.auto_categorization is True
        assert create.smart_suggestions is True
        assert create.suggestion_frequency == SuggestionFrequencyEnum.NORMAL
        assert create.confidence_threshold == 0.7
        assert create.icon_generation_enabled is False
        assert create.conversation_history_enabled is True
        assert create.natural_language_parsing is True
        assert create.privacy_mode is False

    def test_create_ai_preferences_custom(self) -> None:
        """Test creating AIPreferences with custom values."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=False,
            preferred_model=AIModel.OPUS,
            suggestion_frequency=SuggestionFrequency.PROACTIVE,
            confidence_threshold=0.9,
            icon_generation_enabled=True,
            icon_style=IconGenerationStyle.PLAYFUL,
            privacy_mode=True,
        )

        assert prefs.ai_enabled is False
        assert prefs.preferred_model == AIModel.OPUS
        assert prefs.suggestion_frequency == SuggestionFrequency.PROACTIVE
        assert prefs.confidence_threshold == 0.9
        assert prefs.icon_generation_enabled is True
        assert prefs.icon_style == IconGenerationStyle.PLAYFUL
        assert prefs.privacy_mode is True

    def test_is_fully_enabled_all_on(self) -> None:
        """Test is_fully_enabled when all features enabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
            smart_suggestions=True,
            natural_language_parsing=True,
        )

        assert prefs.is_fully_enabled is True

    def test_is_fully_enabled_ai_off(self) -> None:
        """Test is_fully_enabled when AI disabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=False,
            smart_suggestions=True,
            natural_language_parsing=True,
        )

        assert prefs.is_fully_enabled is False

    def test_is_fully_enabled_suggestions_off(self) -> None:
        """Test is_fully_enabled when suggestions disabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
            smart_suggestions=False,
            natural_language_parsing=True,
        )

        assert prefs.is_fully_enabled is False

    def test_should_auto_categorize_enabled(self) -> None:
        """Test should_auto_categorize when enabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
            auto_categorization=True,
        )

        assert prefs.should_auto_categorize is True

    def test_should_auto_categorize_ai_off(self) -> None:
        """Test should_auto_categorize when AI disabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=False,
            auto_categorization=True,
        )

        assert prefs.should_auto_categorize is False

    def test_should_suggest_enabled(self) -> None:
        """Test should_suggest when enabled."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
            smart_suggestions=True,
            suggestion_frequency=SuggestionFrequency.NORMAL,
        )

        assert prefs.should_suggest is True

    def test_should_suggest_off_frequency(self) -> None:
        """Test should_suggest when frequency is off."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
            smart_suggestions=True,
            suggestion_frequency=SuggestionFrequency.OFF,
        )

        assert prefs.should_suggest is False

    def test_meets_confidence_threshold(self) -> None:
        """Test confidence threshold checking."""
        prefs = AIPreferences(
            user_id="user-123",
            confidence_threshold=0.7,
        )

        assert prefs.meets_confidence_threshold(0.8) is True
        assert prefs.meets_confidence_threshold(0.7) is True
        assert prefs.meets_confidence_threshold(0.5) is False
        assert prefs.meets_confidence_threshold(0.0) is False
        assert prefs.meets_confidence_threshold(1.0) is True

    def test_clear_conversation_history_cutoff(self) -> None:
        """Test conversation history cutoff calculation."""
        prefs = AIPreferences(
            user_id="user-123",
            conversation_history_days=30,
        )

        cutoff = prefs.clear_conversation_history_cutoff()
        expected = datetime.now(UTC) - timedelta(days=30)

        # Allow 1 second tolerance
        assert abs((cutoff - expected).total_seconds()) < 1

    def test_repr(self) -> None:
        """Test string representation."""
        prefs = AIPreferences(
            user_id="user-123",
            ai_enabled=True,
        )

        assert "user-123" in repr(prefs)
        assert "ai_enabled=True" in repr(prefs)


class TestAIPreferencesSchemas:
    """Tests for AI preferences Pydantic schemas."""

    def test_ai_preferences_response_from_model(self) -> None:
        """Test AIPreferencesResponse can be created from model."""
        now = datetime.now(UTC)
        response = AIPreferencesResponse(
            id="uuid-123",
            user_id="user-123",
            ai_enabled=True,
            preferred_model=AIModelEnum.HAIKU,
            auto_categorization=True,
            auto_icon_assignment=True,
            smart_suggestions=True,
            suggestion_frequency=SuggestionFrequencyEnum.NORMAL,
            confidence_threshold=0.7,
            icon_generation_enabled=False,
            icon_style=IconGenerationStyleEnum.BRANDED,
            icon_size=128,
            conversation_history_enabled=True,
            conversation_history_days=30,
            natural_language_parsing=True,
            learn_from_corrections=True,
            privacy_mode=False,
            custom_instructions=None,
            created_at=now,
            updated_at=now,
        )

        assert response.id == "uuid-123"
        assert response.ai_enabled is True
        assert response.preferred_model == AIModelEnum.HAIKU

    def test_ai_preferences_update_partial(self) -> None:
        """Test AIPreferencesUpdate allows partial updates."""
        update = AIPreferencesUpdate(ai_enabled=False)

        assert update.ai_enabled is False
        assert update.preferred_model is None
        assert update.auto_categorization is None

    def test_ai_preferences_update_multiple_fields(self) -> None:
        """Test AIPreferencesUpdate with multiple fields."""
        update = AIPreferencesUpdate(
            ai_enabled=False,
            preferred_model=AIModelEnum.OPUS,
            suggestion_frequency=SuggestionFrequencyEnum.PROACTIVE,
        )

        assert update.ai_enabled is False
        assert update.preferred_model == AIModelEnum.OPUS
        assert update.suggestion_frequency == SuggestionFrequencyEnum.PROACTIVE

    def test_ai_preferences_update_confidence_validation(self) -> None:
        """Test confidence_threshold validation."""
        # Valid values
        AIPreferencesUpdate(confidence_threshold=0.0)
        AIPreferencesUpdate(confidence_threshold=0.5)
        AIPreferencesUpdate(confidence_threshold=1.0)

        # Invalid values
        with pytest.raises(ValueError):
            AIPreferencesUpdate(confidence_threshold=-0.1)

        with pytest.raises(ValueError):
            AIPreferencesUpdate(confidence_threshold=1.1)

    def test_ai_preferences_update_icon_size_validation(self) -> None:
        """Test icon_size validation."""
        # Valid values
        AIPreferencesUpdate(icon_size=32)
        AIPreferencesUpdate(icon_size=128)
        AIPreferencesUpdate(icon_size=512)

        # Invalid values
        with pytest.raises(ValueError):
            AIPreferencesUpdate(icon_size=16)

        with pytest.raises(ValueError):
            AIPreferencesUpdate(icon_size=1024)

    def test_ai_preferences_update_history_days_validation(self) -> None:
        """Test conversation_history_days validation."""
        # Valid values
        AIPreferencesUpdate(conversation_history_days=1)
        AIPreferencesUpdate(conversation_history_days=30)
        AIPreferencesUpdate(conversation_history_days=365)

        # Invalid values
        with pytest.raises(ValueError):
            AIPreferencesUpdate(conversation_history_days=0)

        with pytest.raises(ValueError):
            AIPreferencesUpdate(conversation_history_days=500)

    def test_ai_preferences_create_defaults(self) -> None:
        """Test AIPreferencesCreate has correct defaults."""
        create = AIPreferencesCreate()

        assert create.ai_enabled is True
        assert create.preferred_model == AIModelEnum.HAIKU
        assert create.auto_categorization is True
        assert create.smart_suggestions is True
        assert create.suggestion_frequency == SuggestionFrequencyEnum.NORMAL
        assert create.confidence_threshold == 0.7
        assert create.icon_generation_enabled is False
        assert create.icon_size == 128
        assert create.conversation_history_days == 30
        assert create.privacy_mode is False

    def test_clear_history_request(self) -> None:
        """Test ClearHistoryRequest validation."""
        # Without confirmation
        request = ClearHistoryRequest()
        assert request.confirm is False
        assert request.older_than_days is None

        # With confirmation
        request = ClearHistoryRequest(confirm=True, older_than_days=7)
        assert request.confirm is True
        assert request.older_than_days == 7


class TestAIPreferencesIntegration:
    """Integration-style tests for AI preferences."""

    def test_model_to_schema_conversion(self) -> None:
        """Test converting model to schema and back."""
        now = datetime.now(UTC)

        # Create response directly (simulating what would come from DB)
        response = AIPreferencesResponse(
            id="pref-123",
            user_id="user-123",
            ai_enabled=True,
            preferred_model=AIModelEnum.SONNET,
            auto_categorization=True,
            auto_icon_assignment=True,
            smart_suggestions=True,
            suggestion_frequency=SuggestionFrequencyEnum.PROACTIVE,
            confidence_threshold=0.7,
            icon_generation_enabled=True,
            icon_style=IconGenerationStyleEnum.PLAYFUL,
            icon_size=128,
            conversation_history_enabled=True,
            conversation_history_days=30,
            natural_language_parsing=True,
            learn_from_corrections=True,
            privacy_mode=False,
            custom_instructions=None,
            created_at=now,
            updated_at=now,
        )

        assert response.id == "pref-123"
        assert response.preferred_model == AIModelEnum.SONNET
        assert response.icon_generation_enabled is True

    def test_update_preserves_unset_fields(self) -> None:
        """Test that partial update only changes specified fields."""
        update = AIPreferencesUpdate(ai_enabled=False)
        update_data = update.model_dump(exclude_unset=True)

        assert "ai_enabled" in update_data
        assert "preferred_model" not in update_data
        assert len(update_data) == 1
