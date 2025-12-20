"""Bank profile API endpoints.

This module provides endpoints for:
- Listing and searching bank profiles
- CRUD operations (admin only for create/update/delete)
- Bank auto-detection from file content
- Seeding initial bank data
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.core.dependencies import get_db
from src.models.user import User
from src.schemas.bank import (
    BankDetectRequest,
    BankDetectResponse,
    BankProfileCreate,
    BankProfileListResponse,
    BankProfileResponse,
    BankProfileUpdate,
    BankSeedResponse,
    CountryBanksResponse,
)
from src.services.bank_service import BankService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banks", tags=["banks"])


async def get_bank_service(db: AsyncSession = Depends(get_db)) -> BankService:
    """Dependency for bank service."""
    return BankService(db)


@router.get("", response_model=BankProfileListResponse)
async def list_banks(
    country_code: Annotated[str | None, Query(max_length=2)] = None,
    verified_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankProfileListResponse:
    """List all bank profiles with optional filtering.

    Args:
        country_code: Filter by country code (e.g., "GB", "US")
        verified_only: Only return admin-verified banks
        limit: Maximum results (default 100)
        offset: Pagination offset

    Returns:
        Paginated list of bank profiles
    """
    banks = await bank_service.get_all(
        country_code=country_code,
        verified_only=verified_only,
        limit=limit,
        offset=offset,
    )

    total = await bank_service.count(country_code=country_code)

    return BankProfileListResponse(
        banks=[BankProfileResponse.model_validate(b) for b in banks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=list[BankProfileResponse])
async def search_banks(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> list[BankProfileResponse]:
    """Search banks by name or slug.

    Args:
        q: Search query
        limit: Maximum results

    Returns:
        Matching bank profiles
    """
    banks = await bank_service.search(q, limit=limit)
    return [BankProfileResponse.model_validate(b) for b in banks]


@router.get("/countries", response_model=list[CountryBanksResponse])
async def list_countries(
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> list[CountryBanksResponse]:
    """Get list of countries with bank counts.

    Returns:
        List of countries and their bank counts
    """
    countries = await bank_service.get_countries()
    return [CountryBanksResponse(**c) for c in countries]


@router.get("/country/{country_code}", response_model=list[BankProfileResponse])
async def get_banks_by_country(
    country_code: str,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> list[BankProfileResponse]:
    """Get all banks for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        List of bank profiles for that country
    """
    if len(country_code) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country code must be 2 characters",
        )

    banks = await bank_service.get_by_country(country_code.upper())
    return [BankProfileResponse.model_validate(b) for b in banks]


@router.get("/{slug}", response_model=BankProfileResponse)
async def get_bank(
    slug: str,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankProfileResponse:
    """Get a bank profile by slug.

    Args:
        slug: Bank slug (e.g., "monzo", "chase")

    Returns:
        Bank profile
    """
    bank = await bank_service.get_by_slug(slug)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank not found: {slug}",
        )

    return BankProfileResponse.model_validate(bank)


@router.post("", response_model=BankProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_bank(
    data: BankProfileCreate,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankProfileResponse:
    """Create a new bank profile.

    Note: In production, this should be admin-only.

    Args:
        data: Bank profile data

    Returns:
        Created bank profile
    """
    # Check for duplicate slug
    existing = await bank_service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bank with slug '{data.slug}' already exists",
        )

    bank = await bank_service.create(
        name=data.name,
        slug=data.slug,
        country_code=data.country_code,
        currency=data.currency,
        csv_mapping=data.csv_mapping,
        detection_patterns=data.detection_patterns,
        logo_url=data.logo_url,
        website=data.website,
    )

    return BankProfileResponse.model_validate(bank)


@router.patch("/{slug}", response_model=BankProfileResponse)
async def update_bank(
    slug: str,
    data: BankProfileUpdate,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankProfileResponse:
    """Update a bank profile.

    Note: In production, this should be admin-only.

    Args:
        slug: Bank slug
        data: Update data

    Returns:
        Updated bank profile
    """
    bank = await bank_service.get_by_slug(slug)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank not found: {slug}",
        )

    # Filter out None values
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    if update_data:
        bank = await bank_service.update(bank, **update_data)

    return BankProfileResponse.model_validate(bank)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(
    slug: str,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a bank profile.

    Note: In production, this should be admin-only.

    Args:
        slug: Bank slug
    """
    bank = await bank_service.get_by_slug(slug)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank not found: {slug}",
        )

    await bank_service.delete(bank)


@router.post("/detect", response_model=BankDetectResponse)
async def detect_bank(
    data: BankDetectRequest,
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankDetectResponse:
    """Auto-detect bank from file characteristics.

    Args:
        data: Detection request with filename, headers, and/or content

    Returns:
        Detection result with matched bank (if found)
    """
    if not data.filename and not data.headers and not data.content_sample:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of filename, headers, or content_sample is required",
        )

    bank = await bank_service.detect_bank(
        filename=data.filename,
        headers=data.headers,
        content=data.content_sample,
    )

    if bank:
        # Determine confidence based on what matched
        confidence = "high" if data.headers else ("medium" if data.filename else "low")

        return BankDetectResponse(
            detected=True,
            bank=BankProfileResponse.model_validate(bank),
            confidence=confidence,
        )

    return BankDetectResponse(detected=False)


@router.post("/seed", response_model=BankSeedResponse)
async def seed_banks(
    bank_service: BankService = Depends(get_bank_service),
    current_user: User = Depends(get_current_active_user),
) -> BankSeedResponse:
    """Seed bank profiles from JSON file.

    Loads initial bank data from data/bank_profiles.json.
    Skips banks that already exist.

    Note: In production, this should be admin-only or run at startup.

    Returns:
        Number of banks seeded
    """
    seeded = await bank_service.seed_from_json()

    if seeded > 0:
        message = f"Successfully seeded {seeded} bank profiles"
    else:
        message = "No new bank profiles to seed (all already exist)"

    return BankSeedResponse(seeded=seeded, message=message)
