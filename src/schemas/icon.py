"""Pydantic schemas for icon cache API.

This module provides request/response schemas for the icon cache endpoints.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class IconSourceEnum(str, Enum):
    """Icon source enum for API."""

    SIMPLE_ICONS = "simple_icons"
    CLEARBIT = "clearbit"
    LOGO_DEV = "logo_dev"
    BRANDFETCH = "brandfetch"
    AI_GENERATED = "ai_generated"
    USER_UPLOADED = "user_uploaded"
    FALLBACK = "fallback"


class IconResponse(BaseModel):
    """Icon response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    service_name: str
    display_name: str | None = None
    source: IconSourceEnum
    icon_url: str | None = None
    brand_color: str | None = None
    secondary_color: str | None = None
    category: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    is_verified: bool = False
    created_at: datetime
    expires_at: datetime | None = None


class IconSearchRequest(BaseModel):
    """Request to search for icons."""

    query: str = Field(..., min_length=1, max_length=100, description="Service name to search")
    include_ai: bool = Field(False, description="Include AI-generated icons")
    category: str | None = Field(None, description="Filter by category")


class IconSearchResponse(BaseModel):
    """Response with list of icons."""

    icons: list[IconResponse]
    total: int
    from_cache: bool = False


class IconFetchRequest(BaseModel):
    """Request to fetch icon from external source."""

    service_name: str = Field(..., min_length=1, max_length=100)
    sources: list[IconSourceEnum] = Field(
        default=[IconSourceEnum.SIMPLE_ICONS, IconSourceEnum.CLEARBIT],
        description="Sources to try in order",
    )
    force_refresh: bool = Field(False, description="Force refresh even if cached")


class IconGenerateRequest(BaseModel):
    """Request to generate icon with AI."""

    service_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500, description="Optional description")
    style: str = Field("branded", description="Icon style: minimal, branded, playful, corporate")
    size: int = Field(128, ge=32, le=512, description="Icon size in pixels")
    brand_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Brand color")


class IconUploadRequest(BaseModel):
    """Request to upload custom icon."""

    service_name: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = Field(None, max_length=200)
    icon_data: str = Field(..., description="Base64 encoded icon data")
    brand_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    format: str = Field("png", pattern=r"^(png|svg|webp)$")


class IconBulkFetchRequest(BaseModel):
    """Request to fetch icons for multiple services."""

    service_names: list[str] = Field(..., min_length=1, max_length=50)
    sources: list[IconSourceEnum] = Field(
        default=[IconSourceEnum.SIMPLE_ICONS, IconSourceEnum.CLEARBIT],
    )


class IconBulkResponse(BaseModel):
    """Response for bulk icon fetch."""

    icons: dict[str, IconResponse | None]
    found: int
    missing: list[str]


class IconStatsResponse(BaseModel):
    """Icon cache statistics."""

    total_icons: int
    by_source: dict[str, int]
    expired_count: int
    ai_generated_count: int
    user_uploaded_count: int
