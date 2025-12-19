"""Unit tests for icon cache model and service.

Tests cover:
- IconCache model creation and methods
- Icon source enum
- TTL expiration logic
- IconService cache operations
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.icon_cache import IconCache, IconSource, SOURCE_TTL_HOURS
from src.schemas.icon import (
    IconBulkFetchRequest,
    IconFetchRequest,
    IconResponse,
    IconSearchRequest,
    IconSourceEnum,
)


class TestIconSource:
    """Tests for IconSource enum."""

    def test_all_sources_defined(self) -> None:
        """Test all expected sources are defined."""
        assert IconSource.SIMPLE_ICONS.value == "simple_icons"
        assert IconSource.CLEARBIT.value == "clearbit"
        assert IconSource.LOGO_DEV.value == "logo_dev"
        assert IconSource.BRANDFETCH.value == "brandfetch"
        assert IconSource.AI_GENERATED.value == "ai_generated"
        assert IconSource.USER_UPLOADED.value == "user_uploaded"
        assert IconSource.FALLBACK.value == "fallback"

    def test_source_ttl_mapping(self) -> None:
        """Test TTL hours for each source."""
        assert SOURCE_TTL_HOURS[IconSource.SIMPLE_ICONS] == 24 * 7
        assert SOURCE_TTL_HOURS[IconSource.CLEARBIT] == 24 * 3
        assert SOURCE_TTL_HOURS[IconSource.AI_GENERATED] == 24 * 30
        assert SOURCE_TTL_HOURS[IconSource.USER_UPLOADED] == 24 * 365
        assert SOURCE_TTL_HOURS[IconSource.FALLBACK] == 24


class TestIconCache:
    """Tests for IconCache model."""

    def test_create_icon_cache(self) -> None:
        """Test creating an IconCache instance."""
        icon = IconCache(
            service_name="netflix",
            display_name="Netflix",
            source=IconSource.SIMPLE_ICONS,
            icon_url="https://cdn.simpleicons.org/netflix/E50914",
            brand_color="#E50914",
        )

        assert icon.service_name == "netflix"
        assert icon.display_name == "Netflix"
        assert icon.source == IconSource.SIMPLE_ICONS
        assert icon.icon_url == "https://cdn.simpleicons.org/netflix/E50914"
        assert icon.brand_color == "#E50914"

    def test_is_expired_no_expiry(self) -> None:
        """Test is_expired with no expiry set."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        icon.expires_at = None

        assert icon.is_expired is False

    def test_is_expired_future(self) -> None:
        """Test is_expired with future expiry."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        icon.expires_at = datetime.now(UTC) + timedelta(hours=24)

        assert icon.is_expired is False

    def test_is_expired_past(self) -> None:
        """Test is_expired with past expiry."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        icon.expires_at = datetime.now(UTC) - timedelta(hours=1)

        assert icon.is_expired is True

    def test_is_global_no_user(self) -> None:
        """Test is_global with no user_id."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
            user_id=None,
        )

        assert icon.is_global is True

    def test_is_global_with_user(self) -> None:
        """Test is_global with user_id."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
            user_id="user-123",
        )

        assert icon.is_global is False

    def test_set_expiry_from_source_simple_icons(self) -> None:
        """Test setting expiry for SimpleIcons source."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        icon.set_expiry_from_source()

        expected_hours = SOURCE_TTL_HOURS[IconSource.SIMPLE_ICONS]
        expected_expiry = datetime.now(UTC) + timedelta(hours=expected_hours)

        # Allow 1 second tolerance
        assert abs((icon.expires_at - expected_expiry).total_seconds()) < 1

    def test_set_expiry_from_source_ai_generated(self) -> None:
        """Test setting expiry for AI-generated source."""
        icon = IconCache(
            service_name="test",
            source=IconSource.AI_GENERATED,
        )
        icon.set_expiry_from_source()

        expected_hours = SOURCE_TTL_HOURS[IconSource.AI_GENERATED]
        expected_expiry = datetime.now(UTC) + timedelta(hours=expected_hours)

        assert abs((icon.expires_at - expected_expiry).total_seconds()) < 1

    def test_record_fetch(self) -> None:
        """Test recording fetch updates count and timestamp."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        icon.fetch_count = 0
        icon.last_fetched_at = None

        icon.record_fetch()

        assert icon.fetch_count == 1
        assert icon.last_fetched_at is not None

        icon.record_fetch()
        assert icon.fetch_count == 2

    def test_refresh_updates_data(self) -> None:
        """Test refresh updates icon data and expiry."""
        icon = IconCache(
            service_name="test",
            source=IconSource.SIMPLE_ICONS,
        )
        old_url = "https://old.url/icon.svg"
        new_url = "https://new.url/icon.svg"
        icon.icon_url = old_url

        icon.refresh(icon_url=new_url)

        assert icon.icon_url == new_url
        assert icon.expires_at is not None

    def test_repr(self) -> None:
        """Test string representation."""
        icon = IconCache(
            service_name="netflix",
            source=IconSource.SIMPLE_ICONS,
        )

        assert "netflix" in repr(icon)
        assert "simple_icons" in repr(icon)


class TestIconSchemas:
    """Tests for icon Pydantic schemas."""

    def test_icon_response_from_model(self) -> None:
        """Test IconResponse can be created from model attributes."""
        now = datetime.now(UTC)
        response = IconResponse(
            id="uuid-123",
            service_name="spotify",
            display_name="Spotify",
            source=IconSourceEnum.SIMPLE_ICONS,
            icon_url="https://cdn.simpleicons.org/spotify",
            brand_color="#1DB954",
            created_at=now,
        )

        assert response.service_name == "spotify"
        assert response.source == IconSourceEnum.SIMPLE_ICONS

    def test_icon_search_request_validation(self) -> None:
        """Test IconSearchRequest validation."""
        request = IconSearchRequest(query="netflix")
        assert request.query == "netflix"
        assert request.include_ai is False
        assert request.category is None

    def test_icon_fetch_request_default_sources(self) -> None:
        """Test IconFetchRequest has default sources."""
        request = IconFetchRequest(service_name="test")
        assert IconSourceEnum.SIMPLE_ICONS in request.sources
        assert IconSourceEnum.CLEARBIT in request.sources

    def test_icon_bulk_fetch_request(self) -> None:
        """Test IconBulkFetchRequest validation."""
        request = IconBulkFetchRequest(
            service_names=["netflix", "spotify", "hulu"]
        )
        assert len(request.service_names) == 3


class TestIconServiceNormalization:
    """Tests for IconService normalization methods."""

    def test_normalize_service_name(self) -> None:
        """Test service name normalization."""
        from src.services.icon_service import IconService

        # Create mock db session
        mock_db = MagicMock()
        service = IconService(mock_db)

        assert service._normalize_service_name("Netflix") == "netflix"
        assert service._normalize_service_name("Disney+") == "disney"
        assert service._normalize_service_name("HBO Max") == "hbomax"
        assert service._normalize_service_name("Apple Music") == "applemusic"

    def test_get_simple_icons_slug(self) -> None:
        """Test SimpleIcons slug mapping."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        assert service._get_simple_icons_slug("Netflix") == "netflix"
        assert service._get_simple_icons_slug("Disney+") == "disneyplus"
        assert service._get_simple_icons_slug("Disney Plus") == "disneyplus"
        assert service._get_simple_icons_slug("Amazon Prime") == "amazonprime"
        assert service._get_simple_icons_slug("ChatGPT") == "openai"
        assert service._get_simple_icons_slug("Claude") == "anthropic"

    def test_guess_domain(self) -> None:
        """Test domain guessing."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        assert service._guess_domain("netflix") == "netflix.com"
        assert service._guess_domain("spotify") == "spotify.com"
        assert service._guess_domain("zoom") == "zoom.us"
        assert service._guess_domain("notion") == "notion.so"
        assert service._guess_domain("twitch") == "twitch.tv"
        # Unknown defaults to .com
        assert service._guess_domain("unknownservice") == "unknownservice.com"


class TestIconServiceStyleInstructions:
    """Tests for IconService style instructions."""

    def test_get_style_instructions_minimal(self) -> None:
        """Test minimal style instructions."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        instructions = service._get_style_instructions("minimal")
        assert "Style: Minimal" in instructions
        assert "Flat design" in instructions
        assert "Single color" in instructions

    def test_get_style_instructions_branded(self) -> None:
        """Test branded style instructions."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        instructions = service._get_style_instructions("branded")
        assert "Style: Branded" in instructions
        assert "Modern and professional" in instructions

    def test_get_style_instructions_with_color(self) -> None:
        """Test style instructions include color when provided."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        instructions = service._get_style_instructions("minimal", "#FF0000")
        assert "#FF0000" in instructions

    def test_get_style_instructions_playful(self) -> None:
        """Test playful style instructions."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        instructions = service._get_style_instructions("playful")
        assert "Style: Playful" in instructions
        assert "Fun and friendly" in instructions

    def test_get_style_instructions_corporate(self) -> None:
        """Test corporate style instructions."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        instructions = service._get_style_instructions("corporate")
        assert "Style: Corporate" in instructions
        assert "Professional and serious" in instructions


class TestIconServiceColorExtraction:
    """Tests for SVG color extraction."""

    def test_extract_color_from_svg_fill(self) -> None:
        """Test extracting fill color from SVG."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        svg = '<svg><rect fill="#FF0000" /></svg>'
        color = service._extract_color_from_svg(svg)
        assert color == "#FF0000"

    def test_extract_color_from_svg_stroke(self) -> None:
        """Test extracting stroke color from SVG."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        svg = '<svg><rect stroke="#00FF00" /></svg>'
        color = service._extract_color_from_svg(svg)
        assert color == "#00FF00"

    def test_extract_color_from_svg_no_color(self) -> None:
        """Test extracting color when none present."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        svg = '<svg><rect /></svg>'
        color = service._extract_color_from_svg(svg)
        assert color is None

    def test_extract_color_from_svg_css_style(self) -> None:
        """Test extracting color from CSS style."""
        from src.services.icon_service import IconService

        mock_db = MagicMock()
        service = IconService(mock_db)

        svg = '<svg><rect style="fill: #0000FF" /></svg>'
        color = service._extract_color_from_svg(svg)
        assert color == "#0000FF"


class TestIconServiceAsync:
    """Async tests for IconService."""

    @pytest.mark.asyncio
    async def test_get_icon_from_cache(self) -> None:
        """Test getting icon from cache."""
        from src.services.icon_service import IconService

        mock_db = AsyncMock()
        mock_result = MagicMock()

        # Create a cached icon with all required fields
        cached_icon = IconCache(
            id="icon-123",
            service_name="netflix",
            display_name="Netflix",
            source=IconSource.SIMPLE_ICONS,
            icon_url="https://cdn.simpleicons.org/netflix",
            brand_color="#E50914",
            created_at=datetime.now(UTC),
            fetch_count=0,
            is_verified=False,
        )
        cached_icon.expires_at = datetime.now(UTC) + timedelta(hours=24)

        mock_result.scalar_one_or_none.return_value = cached_icon
        mock_db.execute.return_value = mock_result

        service = IconService(mock_db)

        # Patch _fetch_from_sources to not make real HTTP calls
        with patch.object(service, '_fetch_from_sources', return_value=None):
            result = await service.get_icon("netflix")

        assert result is not None
        assert result.service_name == "netflix"
        assert result.source == IconSourceEnum.SIMPLE_ICONS

    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        """Test getting icon cache statistics."""
        from src.services.icon_service import IconService

        mock_db = AsyncMock()
        mock_result = MagicMock()

        # Create sample icons
        icons = [
            IconCache(
                service_name="netflix",
                source=IconSource.SIMPLE_ICONS,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            ),
            IconCache(
                service_name="spotify",
                source=IconSource.CLEARBIT,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            ),
            IconCache(
                service_name="custom",
                source=IconSource.AI_GENERATED,
                expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
            ),
        ]

        mock_result.scalars.return_value.all.return_value = icons
        mock_db.execute.return_value = mock_result

        service = IconService(mock_db)
        stats = await service.get_stats()

        assert stats.total_icons == 3
        assert stats.by_source["simple_icons"] == 1
        assert stats.by_source["clearbit"] == 1
        assert stats.by_source["ai_generated"] == 1
        assert stats.expired_count == 1
        assert stats.ai_generated_count == 1

    @pytest.mark.asyncio
    async def test_search_icons(self) -> None:
        """Test searching for icons."""
        from src.services.icon_service import IconService

        mock_db = AsyncMock()
        mock_result = MagicMock()

        icons = [
            IconCache(
                id="icon-1",
                service_name="netflix",
                display_name="Netflix",
                source=IconSource.SIMPLE_ICONS,
                created_at=datetime.now(UTC),
                is_verified=False,
            ),
        ]

        mock_result.scalars.return_value.all.return_value = icons
        mock_db.execute.return_value = mock_result

        service = IconService(mock_db)
        response = await service.search_icons("net")

        assert response.total == 1
        assert response.from_cache is True
        assert len(response.icons) == 1

    @pytest.mark.asyncio
    async def test_bulk_fetch(self) -> None:
        """Test bulk fetching icons."""
        from src.services.icon_service import IconService

        mock_db = AsyncMock()
        mock_result = MagicMock()

        # Return None for all - simulating empty cache
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = IconService(mock_db)

        # Patch get_icon to return some results
        async def mock_get_icon(name, **kwargs):
            if name == "netflix":
                return IconResponse(
                    id="icon-1",
                    service_name="netflix",
                    source=IconSourceEnum.SIMPLE_ICONS,
                    created_at=datetime.now(UTC),
                )
            return None

        with patch.object(service, 'get_icon', side_effect=mock_get_icon):
            response = await service.bulk_fetch(["netflix", "unknown"])

        assert response.found == 1
        assert "netflix" in response.icons
        assert "unknown" in response.missing
