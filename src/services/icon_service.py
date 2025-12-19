"""Icon service for fetching and caching icons from external sources.

This module provides the IconService for:
- Fetching icons from SimpleIcons, Clearbit, Logo.dev, Brandfetch
- Caching icons in database with TTL
- AI icon generation using Claude for SVG icons
- Icon search and retrieval

Example:
    >>> from src.services.icon_service import IconService
    >>> service = IconService(db_session)
    >>> icon = await service.get_icon("netflix")
"""

import base64
import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.icon_cache import IconCache, IconSource
from src.schemas.icon import (
    IconBulkResponse,
    IconResponse,
    IconSearchResponse,
    IconSourceEnum,
    IconStatsResponse,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Icon CDN URLs
SIMPLE_ICONS_CDN = "https://cdn.simpleicons.org"
CLEARBIT_LOGO_URL = "https://logo.clearbit.com"
LOGO_DEV_URL = "https://img.logo.dev"
BRANDFETCH_URL = "https://cdn.brandfetch.io"

# Popular service slugs for SimpleIcons
# Maps common names to SimpleIcons slugs
SERVICE_SLUG_MAP = {
    "netflix": "netflix",
    "spotify": "spotify",
    "disney+": "disneyplus",
    "disney plus": "disneyplus",
    "amazon prime": "amazonprime",
    "prime video": "amazonprimevideo",
    "hulu": "hulu",
    "hbo max": "hbo",
    "apple music": "applemusic",
    "youtube": "youtube",
    "youtube premium": "youtube",
    "github": "github",
    "microsoft 365": "microsoft365",
    "office 365": "microsoft365",
    "google": "google",
    "google one": "google",
    "dropbox": "dropbox",
    "icloud": "icloud",
    "adobe": "adobe",
    "figma": "figma",
    "slack": "slack",
    "zoom": "zoom",
    "notion": "notion",
    "linear": "linear",
    "vercel": "vercel",
    "aws": "amazonaws",
    "azure": "microsoftazure",
    "gcp": "googlecloud",
    "digitalocean": "digitalocean",
    "cloudflare": "cloudflare",
    "openai": "openai",
    "anthropic": "anthropic",
    "chatgpt": "openai",
    "claude": "anthropic",
    "midjourney": "midjourney",
    "revolut": "revolut",
    "monzo": "monzo",
    "paypal": "paypal",
    "stripe": "stripe",
    "twitch": "twitch",
    "discord": "discord",
    "steam": "steam",
    "playstation": "playstation",
    "xbox": "xbox",
    "nintendo": "nintendoswitch",
}

# Brand colors for popular services
BRAND_COLORS = {
    "netflix": "#E50914",
    "spotify": "#1DB954",
    "disneyplus": "#113CCF",
    "amazonprime": "#00A8E1",
    "hulu": "#1CE783",
    "hbo": "#5822B2",
    "applemusic": "#FA243C",
    "youtube": "#FF0000",
    "github": "#181717",
    "microsoft365": "#D83B01",
    "google": "#4285F4",
    "dropbox": "#0061FF",
    "icloud": "#3693F3",
    "adobe": "#FF0000",
    "figma": "#F24E1E",
    "slack": "#4A154B",
    "zoom": "#2D8CFF",
    "notion": "#000000",
    "linear": "#5E6AD2",
    "vercel": "#000000",
    "amazonaws": "#232F3E",
    "microsoftazure": "#0078D4",
    "googlecloud": "#4285F4",
    "openai": "#412991",
    "anthropic": "#D4A574",
    "revolut": "#0075EB",
    "monzo": "#FF5C5C",
    "paypal": "#003087",
    "stripe": "#635BFF",
    "discord": "#5865F2",
    "steam": "#000000",
    "twitch": "#9146FF",
}


class IconService:
    """Service for managing icon cache and fetching icons.

    Provides methods to:
    - Get icons from cache or fetch from external sources
    - Search icons by service name
    - Bulk fetch icons for multiple services
    - Generate cache statistics

    Attributes:
        db: Async database session.
        http_client: HTTP client for external requests.

    Example:
        >>> service = IconService(db_session)
        >>> icon = await service.get_icon("netflix")
        >>> print(icon.icon_url)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize IconService.

        Args:
            db: Async database session.
        """
        self.db = db
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={"User-Agent": "MoneyFlow/1.0"},
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _normalize_service_name(self, name: str) -> str:
        """Normalize service name for lookup.

        Args:
            name: Service name to normalize.

        Returns:
            Normalized lowercase name.
        """
        # Lowercase and remove special characters
        normalized = re.sub(r"[^a-z0-9]", "", name.lower())
        return normalized

    def _get_simple_icons_slug(self, service_name: str) -> str:
        """Get SimpleIcons slug for a service.

        Args:
            service_name: Service name.

        Returns:
            SimpleIcons slug or normalized name.
        """
        lower_name = service_name.lower().strip()

        # Check direct mapping
        if lower_name in SERVICE_SLUG_MAP:
            return SERVICE_SLUG_MAP[lower_name]

        # Check normalized name
        normalized = self._normalize_service_name(service_name)
        if normalized in SERVICE_SLUG_MAP.values():
            return normalized

        # Default to normalized name
        return normalized

    async def get_icon(
        self,
        service_name: str,
        user_id: str | None = None,
        force_refresh: bool = False,
    ) -> IconResponse | None:
        """Get icon for a service.

        First checks cache, then fetches from external sources if needed.

        Args:
            service_name: Service name to get icon for.
            user_id: Optional user ID for user-specific icons.
            force_refresh: Force refresh from external source.

        Returns:
            IconResponse or None if not found.
        """
        normalized = self._normalize_service_name(service_name)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = await self._get_from_cache(normalized, user_id)
            if cached and not cached.is_expired:
                cached.record_fetch()
                await self.db.commit()
                return self._to_response(cached)

        # Try to fetch from external sources
        icon = await self._fetch_from_sources(service_name)
        if icon:
            return self._to_response(icon)

        # Return cached even if expired
        if not force_refresh:
            cached = await self._get_from_cache(normalized, user_id)
            if cached:
                return self._to_response(cached)

        return None

    async def _get_from_cache(
        self,
        service_name: str,
        user_id: str | None = None,
    ) -> IconCache | None:
        """Get icon from cache.

        Args:
            service_name: Normalized service name.
            user_id: Optional user ID.

        Returns:
            Cached icon or None.
        """
        # Check user-specific cache first
        if user_id:
            query = select(IconCache).where(
                IconCache.service_name == service_name,
                IconCache.user_id == user_id,
            )
            result = await self.db.execute(query)
            cached = result.scalar_one_or_none()
            if cached:
                return cached

        # Check global cache
        query = select(IconCache).where(
            IconCache.service_name == service_name,
            IconCache.user_id.is_(None),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _fetch_from_sources(
        self,
        service_name: str,
        sources: list[IconSourceEnum] | None = None,
    ) -> IconCache | None:
        """Fetch icon from external sources.

        Tries sources in order until one succeeds.

        Args:
            service_name: Service name.
            sources: Sources to try (default: SimpleIcons, Clearbit).

        Returns:
            Cached icon or None.
        """
        if sources is None:
            sources = [IconSourceEnum.SIMPLE_ICONS, IconSourceEnum.CLEARBIT]

        normalized = self._normalize_service_name(service_name)
        slug = self._get_simple_icons_slug(service_name)
        brand_color = BRAND_COLORS.get(slug)

        for source in sources:
            icon_url = await self._try_fetch_source(service_name, source)
            if icon_url:
                # Create or update cache entry
                icon = await self._create_cache_entry(
                    service_name=normalized,
                    display_name=service_name,
                    source=IconSource(source.value),
                    icon_url=icon_url,
                    brand_color=brand_color,
                )
                return icon

        return None

    async def _try_fetch_source(
        self,
        service_name: str,
        source: IconSourceEnum,
    ) -> str | None:
        """Try to fetch icon from a specific source.

        Args:
            service_name: Service name.
            source: Source to try.

        Returns:
            Icon URL or None.
        """
        try:
            client = await self._get_http_client()
            slug = self._get_simple_icons_slug(service_name)
            color = BRAND_COLORS.get(slug, "000000").lstrip("#")

            if source == IconSourceEnum.SIMPLE_ICONS:
                # Try SimpleIcons CDN
                url = f"{SIMPLE_ICONS_CDN}/{slug}/{color}"
                response = await client.head(url)
                if response.status_code == 200:
                    return url

            elif source == IconSourceEnum.CLEARBIT:
                # Try Clearbit with domain guess
                domain = self._guess_domain(service_name)
                if domain:
                    url = f"{CLEARBIT_LOGO_URL}/{domain}"
                    response = await client.head(url)
                    if response.status_code == 200:
                        return url

            elif source == IconSourceEnum.LOGO_DEV:
                # Try Logo.dev
                domain = self._guess_domain(service_name)
                if domain:
                    url = f"{LOGO_DEV_URL}/{domain}?token=pk_placeholder"
                    response = await client.head(url)
                    if response.status_code == 200:
                        return url

        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch icon from {source}: {e}")

        return None

    def _guess_domain(self, service_name: str) -> str | None:
        """Guess domain for a service name.

        Args:
            service_name: Service name.

        Returns:
            Guessed domain or None.
        """
        normalized = self._normalize_service_name(service_name)

        # Common domain patterns
        domain_map = {
            "netflix": "netflix.com",
            "spotify": "spotify.com",
            "disney": "disneyplus.com",
            "amazon": "amazon.com",
            "hulu": "hulu.com",
            "hbo": "hbomax.com",
            "apple": "apple.com",
            "youtube": "youtube.com",
            "github": "github.com",
            "microsoft": "microsoft.com",
            "google": "google.com",
            "dropbox": "dropbox.com",
            "adobe": "adobe.com",
            "figma": "figma.com",
            "slack": "slack.com",
            "zoom": "zoom.us",
            "notion": "notion.so",
            "linear": "linear.app",
            "vercel": "vercel.com",
            "openai": "openai.com",
            "anthropic": "anthropic.com",
            "revolut": "revolut.com",
            "monzo": "monzo.com",
            "paypal": "paypal.com",
            "stripe": "stripe.com",
            "discord": "discord.com",
            "steam": "steampowered.com",
            "twitch": "twitch.tv",
        }

        return domain_map.get(normalized, f"{normalized}.com")

    async def _create_cache_entry(
        self,
        service_name: str,
        display_name: str,
        source: IconSource,
        icon_url: str | None = None,
        icon_data: str | None = None,
        brand_color: str | None = None,
        user_id: str | None = None,
    ) -> IconCache:
        """Create or update cache entry.

        Args:
            service_name: Normalized service name.
            display_name: Human-readable name.
            source: Icon source.
            icon_url: Icon URL.
            icon_data: Base64 icon data.
            brand_color: Brand color.
            user_id: Optional user ID.

        Returns:
            Created or updated cache entry.
        """
        # Check for existing entry
        query = select(IconCache).where(
            IconCache.service_name == service_name,
            IconCache.user_id == user_id if user_id else IconCache.user_id.is_(None),
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.icon_url = icon_url
            existing.icon_data = icon_data
            existing.source = source
            existing.brand_color = brand_color
            existing.set_expiry_from_source()
            existing.updated_at = datetime.now(UTC)
            await self.db.commit()
            return existing

        # Create new entry
        icon = IconCache(
            service_name=service_name,
            display_name=display_name,
            source=source,
            icon_url=icon_url,
            icon_data=icon_data,
            brand_color=brand_color,
            user_id=user_id,
        )
        icon.set_expiry_from_source()
        self.db.add(icon)
        await self.db.commit()
        await self.db.refresh(icon)
        return icon

    async def search_icons(
        self,
        query: str,
        category: str | None = None,
        include_ai: bool = False,
        limit: int = 20,
    ) -> IconSearchResponse:
        """Search for icons.

        Args:
            query: Search query.
            category: Optional category filter.
            include_ai: Include AI-generated icons.
            limit: Maximum results.

        Returns:
            Search results.
        """
        normalized = self._normalize_service_name(query)

        # Build query
        stmt = select(IconCache).where(
            IconCache.service_name.ilike(f"%{normalized}%"),
        )

        if category:
            stmt = stmt.where(IconCache.category == category)

        if not include_ai:
            stmt = stmt.where(IconCache.source != IconSource.AI_GENERATED)

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        icons = result.scalars().all()

        return IconSearchResponse(
            icons=[self._to_response(i) for i in icons],
            total=len(icons),
            from_cache=True,
        )

    async def bulk_fetch(
        self,
        service_names: list[str],
        sources: list[IconSourceEnum] | None = None,
    ) -> IconBulkResponse:
        """Fetch icons for multiple services.

        Args:
            service_names: List of service names.
            sources: Sources to try.

        Returns:
            Bulk fetch response.
        """
        icons: dict[str, IconResponse | None] = {}
        missing: list[str] = []

        for name in service_names:
            icon = await self.get_icon(name)
            if icon:
                icons[name] = icon
            else:
                missing.append(name)

        return IconBulkResponse(
            icons=icons,
            found=len(service_names) - len(missing),
            missing=missing,
        )

    async def get_stats(self) -> IconStatsResponse:
        """Get icon cache statistics.

        Returns:
            Cache statistics.
        """
        result = await self.db.execute(select(IconCache))
        all_icons = result.scalars().all()

        by_source: dict[str, int] = {}
        expired_count = 0
        ai_count = 0
        user_count = 0

        for icon in all_icons:
            source_name = icon.source.value
            by_source[source_name] = by_source.get(source_name, 0) + 1

            if icon.is_expired:
                expired_count += 1

            if icon.source == IconSource.AI_GENERATED:
                ai_count += 1

            if icon.source == IconSource.USER_UPLOADED:
                user_count += 1

        return IconStatsResponse(
            total_icons=len(all_icons),
            by_source=by_source,
            expired_count=expired_count,
            ai_generated_count=ai_count,
            user_uploaded_count=user_count,
        )

    def _to_response(self, icon: IconCache) -> IconResponse:
        """Convert cache entry to response.

        Args:
            icon: Cache entry.

        Returns:
            Icon response.
        """
        return IconResponse(
            id=icon.id,
            service_name=icon.service_name,
            display_name=icon.display_name,
            source=IconSourceEnum(icon.source.value),
            icon_url=icon.icon_url,
            brand_color=icon.brand_color,
            secondary_color=icon.secondary_color,
            category=icon.category,
            width=icon.width,
            height=icon.height,
            format=icon.format,
            is_verified=icon.is_verified,
            created_at=icon.created_at,
            expires_at=icon.expires_at,
        )

    async def generate_ai_icon(
        self,
        service_name: str,
        style: str = "minimal",
        primary_color: str | None = None,
        user_id: str | None = None,
    ) -> IconResponse | None:
        """Generate an icon using AI.

        Uses Claude to generate an SVG icon for a service when no
        external icon source is available.

        Args:
            service_name: Name of the service to generate icon for.
            style: Icon style (minimal, branded, playful, corporate).
            primary_color: Preferred primary color (hex).
            user_id: Optional user ID for user-specific icons.

        Returns:
            Generated icon response or None if generation fails.

        Example:
            >>> icon = await service.generate_ai_icon("CustomApp", style="minimal")
            >>> print(icon.icon_url)  # data:image/svg+xml;base64,...
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            # Build style instructions
            style_instructions = self._get_style_instructions(style, primary_color)

            prompt = f"""Generate a simple, clean SVG icon for a service called "{service_name}".

{style_instructions}

Requirements:
- SVG format only
- Size: 48x48 viewBox
- Single color or gradient
- Simple, recognizable shape
- No text in the icon
- Professional and clean design

Return ONLY the SVG code, nothing else. Start with <svg and end with </svg>."""

            message = client.messages.create(
                model="claude-haiku-4-5-20250929",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract SVG from response
            svg_content = message.content[0].text.strip()

            # Validate SVG
            if not svg_content.startswith("<svg") or not svg_content.endswith("</svg>"):
                logger.warning(f"Invalid SVG response for {service_name}")
                return None

            # Convert to base64 data URL
            svg_bytes = svg_content.encode("utf-8")
            svg_base64 = base64.b64encode(svg_bytes).decode("utf-8")
            data_url = f"data:image/svg+xml;base64,{svg_base64}"

            # Extract color from SVG if possible
            brand_color = primary_color or self._extract_color_from_svg(svg_content)

            # Create cache entry
            icon = await self._create_cache_entry(
                service_name=self._normalize_service_name(service_name),
                display_name=service_name,
                source=IconSource.AI_GENERATED,
                icon_url=data_url,
                icon_data=svg_base64,
                brand_color=brand_color,
                user_id=user_id,
            )

            logger.info(f"Generated AI icon for {service_name}")
            return self._to_response(icon)

        except ImportError:
            logger.error("anthropic package not installed")
            return None
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error generating icon: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating AI icon for {service_name}: {e}")
            return None

    def _get_style_instructions(
        self,
        style: str,
        primary_color: str | None = None,
    ) -> str:
        """Get style-specific instructions for AI generation.

        Args:
            style: Icon style.
            primary_color: Primary color preference.

        Returns:
            Style instructions for the prompt.
        """
        color_instruction = ""
        if primary_color:
            color_instruction = f"Use {primary_color} as the primary color."

        styles = {
            "minimal": f"""Style: Minimal
- Flat design with clean lines
- Single color fill
- Simple geometric shapes
- High contrast
{color_instruction}""",
            "branded": f"""Style: Branded
- Modern and professional
- Can use gradients
- Bold, distinctive shape
- Memorable design
{color_instruction}""",
            "playful": f"""Style: Playful
- Fun and friendly
- Rounded corners
- Vibrant colors allowed
- Approachable design
{color_instruction}""",
            "corporate": f"""Style: Corporate
- Professional and serious
- Clean, structured design
- Muted or business colors
- Trustworthy appearance
{color_instruction}""",
        }

        return styles.get(style, styles["minimal"])

    def _extract_color_from_svg(self, svg: str) -> str | None:
        """Extract primary color from SVG content.

        Args:
            svg: SVG content string.

        Returns:
            Hex color or None.
        """
        # Look for fill or stroke colors
        color_patterns = [
            r'fill="(#[0-9A-Fa-f]{6})"',
            r'fill="(#[0-9A-Fa-f]{3})"',
            r'stroke="(#[0-9A-Fa-f]{6})"',
            r"fill:\s*(#[0-9A-Fa-f]{6})",
        ]

        for pattern in color_patterns:
            match = re.search(pattern, svg)
            if match:
                color = match.group(1)
                # Expand 3-char hex to 6-char
                if len(color) == 4:
                    color = f"#{color[1] * 2}{color[2] * 2}{color[3] * 2}"
                return color

        return None

    async def get_or_generate_icon(
        self,
        service_name: str,
        user_id: str | None = None,
        allow_ai_generation: bool = True,
        style: str = "minimal",
    ) -> IconResponse | None:
        """Get icon from cache/external sources or generate with AI.

        This is the main method for getting icons with AI fallback.

        Args:
            service_name: Service name.
            user_id: Optional user ID.
            allow_ai_generation: Whether to use AI generation as fallback.
            style: Style for AI-generated icons.

        Returns:
            Icon response or None.

        Example:
            >>> icon = await service.get_or_generate_icon("MyCustomApp")
        """
        # First try to get from cache or external sources
        icon = await self.get_icon(service_name, user_id=user_id)
        if icon:
            return icon

        # If not found and AI generation is allowed, generate one
        if allow_ai_generation:
            return await self.generate_ai_icon(
                service_name=service_name,
                style=style,
                user_id=user_id,
            )

        return None
