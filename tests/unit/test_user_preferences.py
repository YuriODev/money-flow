"""Unit tests for user preferences API and schemas.

Tests cover:
- UserPreferences schema validation
- UserPreferencesUpdate partial updates
- Preferences API endpoints (get, update)
- Default preferences handling
- Preference merging logic
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api.users import DEFAULT_PREFERENCES, _parse_preferences, router
from src.schemas.user import UserPreferencesResponse, UserPreferencesUpdate

# ============================================================================
# Schema Tests
# ============================================================================


class TestUserPreferencesResponseSchema:
    """Test UserPreferencesResponse schema."""

    def test_default_values(self):
        """Test schema has correct default values."""
        prefs = UserPreferencesResponse()
        assert prefs.currency == "GBP"
        assert prefs.date_format == "DD/MM/YYYY"
        assert prefs.number_format == "1,234.56"
        assert prefs.theme == "system"
        assert prefs.default_view == "list"
        assert prefs.compact_mode is False
        assert prefs.week_start == "monday"
        assert prefs.timezone == "UTC"
        assert prefs.language == "en"
        assert prefs.show_currency_symbol is True

    def test_custom_values(self):
        """Test schema accepts custom values."""
        prefs = UserPreferencesResponse(
            currency="USD",
            date_format="MM/DD/YYYY",
            number_format="1.234,56",
            theme="dark",
            default_view="calendar",
            compact_mode=True,
            week_start="sunday",
            timezone="America/New_York",
            language="es",
            show_currency_symbol=False,
        )
        assert prefs.currency == "USD"
        assert prefs.date_format == "MM/DD/YYYY"
        assert prefs.theme == "dark"
        assert prefs.compact_mode is True


class TestUserPreferencesUpdateSchema:
    """Test UserPreferencesUpdate schema validation."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        update = UserPreferencesUpdate(currency="EUR", theme="dark")
        assert update.currency == "EUR"
        assert update.theme == "dark"
        assert update.date_format is None
        assert update.default_view is None

    def test_empty_update(self):
        """Test empty update is valid."""
        update = UserPreferencesUpdate()
        data = update.model_dump(exclude_unset=True)
        assert data == {}

    def test_currency_validation_valid(self):
        """Test valid currency codes are accepted."""
        for code in ["GBP", "USD", "EUR", "UAH", "CAD", "AUD", "JPY", "CHF", "CNY", "INR"]:
            update = UserPreferencesUpdate(currency=code)
            assert update.currency == code.upper()

    def test_currency_validation_case_insensitive(self):
        """Test currency codes are normalized to uppercase."""
        update = UserPreferencesUpdate(currency="usd")
        assert update.currency == "USD"

    def test_currency_validation_invalid(self):
        """Test invalid currency code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(currency="XYZ")
        assert "Invalid currency" in str(exc_info.value)

    def test_theme_validation_valid(self):
        """Test valid theme values are accepted."""
        for theme in ["light", "dark", "system"]:
            update = UserPreferencesUpdate(theme=theme)
            assert update.theme == theme

    def test_theme_validation_case_insensitive(self):
        """Test theme values are normalized to lowercase."""
        update = UserPreferencesUpdate(theme="DARK")
        assert update.theme == "dark"

    def test_theme_validation_invalid(self):
        """Test invalid theme raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(theme="invalid")
        assert "Invalid theme" in str(exc_info.value)

    def test_default_view_validation_valid(self):
        """Test valid view values are accepted."""
        for view in ["list", "calendar", "cards", "agent"]:
            update = UserPreferencesUpdate(default_view=view)
            assert update.default_view == view

    def test_default_view_validation_invalid(self):
        """Test invalid view raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(default_view="invalid")
        assert "Invalid view" in str(exc_info.value)

    def test_date_format_validation_valid(self):
        """Test valid date formats are accepted."""
        for fmt in ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]:
            update = UserPreferencesUpdate(date_format=fmt)
            assert update.date_format == fmt

    def test_date_format_validation_invalid(self):
        """Test invalid date format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(date_format="YYYY/DD/MM")
        assert "Invalid date format" in str(exc_info.value)

    def test_week_start_validation_valid(self):
        """Test valid week start values are accepted."""
        for day in ["monday", "sunday"]:
            update = UserPreferencesUpdate(week_start=day)
            assert update.week_start == day

    def test_week_start_validation_invalid(self):
        """Test invalid week start raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferencesUpdate(week_start="tuesday")
        assert "Invalid week start" in str(exc_info.value)


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestParsePreferences:
    """Test _parse_preferences helper function."""

    def test_parse_none_returns_defaults(self):
        """Test None input returns default preferences."""
        result = _parse_preferences(None)
        assert result == DEFAULT_PREFERENCES

    def test_parse_empty_string_returns_defaults(self):
        """Test empty string returns default preferences."""
        result = _parse_preferences("")
        assert result == DEFAULT_PREFERENCES

    def test_parse_valid_json(self):
        """Test valid JSON is parsed correctly."""
        stored = json.dumps({"currency": "USD", "theme": "dark"})
        result = _parse_preferences(stored)
        assert result["currency"] == "USD"
        assert result["theme"] == "dark"
        # Defaults are preserved for unset values
        assert result["date_format"] == "DD/MM/YYYY"

    def test_parse_invalid_json_returns_defaults(self):
        """Test invalid JSON returns defaults."""
        result = _parse_preferences("not valid json")
        assert result == DEFAULT_PREFERENCES

    def test_parse_merges_with_defaults(self):
        """Test partial preferences are merged with defaults."""
        stored = json.dumps({"currency": "EUR"})
        result = _parse_preferences(stored)
        # Custom value
        assert result["currency"] == "EUR"
        # Default values
        assert result["theme"] == "system"
        assert result["default_view"] == "list"


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestPreferencesAPI:
    """Test preferences API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(router, prefix="/users")
        return app

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = "test-user-123"
        user.preferences = None
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    def test_get_preferences_returns_defaults_when_none(self, app, mock_user, mock_db):
        """Test GET preferences returns defaults when user has none."""
        # Override dependencies
        from src.auth.dependencies import get_current_active_user
        from src.core.dependencies import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/users/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "GBP"
        assert data["theme"] == "system"

    def test_get_preferences_returns_stored_values(self, app, mock_user, mock_db):
        """Test GET preferences returns stored values."""
        from src.auth.dependencies import get_current_active_user
        from src.core.dependencies import get_db

        mock_user.preferences = json.dumps({"currency": "USD", "theme": "dark"})
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/users/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "USD"
        assert data["theme"] == "dark"
        # Defaults for unset
        assert data["date_format"] == "DD/MM/YYYY"

    def test_update_preferences_partial_update(self, app, mock_user, mock_db):
        """Test PUT preferences performs partial update."""
        from src.auth.dependencies import get_current_active_user
        from src.core.dependencies import get_db

        mock_user.preferences = json.dumps({"currency": "GBP"})
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.put(
            "/users/preferences", json={"theme": "dark", "default_view": "calendar"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "GBP"  # Preserved
        assert data["theme"] == "dark"  # Updated
        assert data["default_view"] == "calendar"  # Updated

    def test_update_preferences_saves_to_db(self, app, mock_user, mock_db):
        """Test PUT preferences saves to database."""
        from src.auth.dependencies import get_current_active_user
        from src.core.dependencies import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.put("/users/preferences", json={"currency": "EUR"})

        assert response.status_code == 200
        # Verify DB operations called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        # Verify preferences saved
        saved_prefs = json.loads(mock_user.preferences)
        assert saved_prefs["currency"] == "EUR"

    def test_update_preferences_validation_error(self, app, mock_user, mock_db):
        """Test PUT preferences returns 422 for invalid data."""
        from src.auth.dependencies import get_current_active_user
        from src.core.dependencies import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.put("/users/preferences", json={"currency": "INVALID"})

        assert response.status_code == 422


# ============================================================================
# Default Preferences Tests
# ============================================================================


class TestDefaultPreferences:
    """Test default preferences constants."""

    def test_default_preferences_has_all_keys(self):
        """Test DEFAULT_PREFERENCES has all required keys."""
        required_keys = {
            "currency",
            "date_format",
            "number_format",
            "theme",
            "default_view",
            "compact_mode",
            "week_start",
            "timezone",
            "language",
            "show_currency_symbol",
            "default_card_id",
            "default_category_id",
        }
        assert set(DEFAULT_PREFERENCES.keys()) == required_keys

    def test_default_currency_is_gbp(self):
        """Test default currency is GBP."""
        assert DEFAULT_PREFERENCES["currency"] == "GBP"

    def test_default_theme_is_system(self):
        """Test default theme is system."""
        assert DEFAULT_PREFERENCES["theme"] == "system"

    def test_default_view_is_list(self):
        """Test default view is list."""
        assert DEFAULT_PREFERENCES["default_view"] == "list"

    def test_default_card_id_is_none(self):
        """Test default card ID is None."""
        assert DEFAULT_PREFERENCES["default_card_id"] is None

    def test_default_category_id_is_none(self):
        """Test default category ID is None."""
        assert DEFAULT_PREFERENCES["default_category_id"] is None
