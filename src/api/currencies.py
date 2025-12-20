"""Currency API endpoints for fetching currency information.

This module provides endpoints for:
- Getting all currencies with regional grouping
- Searching currencies by name/code/symbol
- Getting popular currencies
- Getting currencies by region

Routes:
    GET /api/v1/currencies - Get all currencies grouped by region
    GET /api/v1/currencies/search - Search currencies
    GET /api/v1/currencies/popular - Get popular currencies
    GET /api/v1/currencies/regions/{region} - Get currencies by region
    GET /api/v1/currencies/{code} - Get single currency info
"""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.data.currencies import (
    CURRENCIES,
    POPULAR_CURRENCIES,
    CurrencyData,
    CurrencyRegion,
    get_all_regions,
    get_currencies_by_region,
    get_currency,
    search_currencies,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CurrencyResponse(BaseModel):
    """Response model for a single currency."""

    code: str
    symbol: str
    name: str
    flag: str
    region: str
    decimal_places: int
    is_popular: bool

    @classmethod
    def from_currency_data(cls, data: CurrencyData) -> "CurrencyResponse":
        """Create from CurrencyData."""
        return cls(
            code=data.code,
            symbol=data.symbol,
            name=data.name,
            flag=data.flag,
            region=data.region.value,
            decimal_places=data.decimal_places,
            is_popular=data.is_popular,
        )


class RegionInfo(BaseModel):
    """Region information for grouping."""

    id: str
    name: str
    count: int


class CurrenciesGroupedResponse(BaseModel):
    """Response with currencies grouped by region."""

    total: int
    regions: list[RegionInfo]
    currencies: dict[str, list[CurrencyResponse]]


class CurrencySearchResponse(BaseModel):
    """Response for currency search."""

    query: str
    total: int
    currencies: list[CurrencyResponse]


@router.get("", response_model=CurrenciesGroupedResponse)
async def get_all_currencies() -> CurrenciesGroupedResponse:
    """Get all currencies grouped by region.

    Returns all 161+ ISO 4217 currencies organized by geographic region
    for easy browsing and selection.

    Returns:
        CurrenciesGroupedResponse with regions and currencies.
    """
    regions_info: list[RegionInfo] = []
    currencies_by_region: dict[str, list[CurrencyResponse]] = {}

    for region, display_name in get_all_regions():
        region_currencies = get_currencies_by_region(region)
        region_id = region.value

        regions_info.append(
            RegionInfo(
                id=region_id,
                name=display_name,
                count=len(region_currencies),
            )
        )

        currencies_by_region[region_id] = [
            CurrencyResponse.from_currency_data(c) for c in region_currencies
        ]

    return CurrenciesGroupedResponse(
        total=len(CURRENCIES),
        regions=regions_info,
        currencies=currencies_by_region,
    )


@router.get("/search", response_model=CurrencySearchResponse)
async def search_currencies_endpoint(
    q: str = Query(..., min_length=1, max_length=50, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
) -> CurrencySearchResponse:
    """Search currencies by code, name, or symbol.

    Args:
        q: Search string (case-insensitive).
        limit: Maximum number of results (default 20, max 50).

    Returns:
        CurrencySearchResponse with matching currencies.
    """
    results = search_currencies(q, limit)
    return CurrencySearchResponse(
        query=q,
        total=len(results),
        currencies=[CurrencyResponse.from_currency_data(c) for c in results],
    )


@router.get("/popular", response_model=list[CurrencyResponse])
async def get_popular_currencies_endpoint() -> list[CurrencyResponse]:
    """Get popular/commonly used currencies.

    Returns the 24 most commonly used currencies worldwide,
    sorted by usage frequency.

    Returns:
        List of popular CurrencyResponse objects.
    """
    return [CurrencyResponse.from_currency_data(c) for c in POPULAR_CURRENCIES]


@router.get("/regions", response_model=list[RegionInfo])
async def get_regions() -> list[RegionInfo]:
    """Get all available currency regions.

    Returns:
        List of RegionInfo with region IDs, names, and currency counts.
    """
    regions: list[RegionInfo] = []
    for region, display_name in get_all_regions():
        region_currencies = get_currencies_by_region(region)
        regions.append(
            RegionInfo(
                id=region.value,
                name=display_name,
                count=len(region_currencies),
            )
        )
    return regions


@router.get("/regions/{region_id}", response_model=list[CurrencyResponse])
async def get_currencies_by_region_endpoint(
    region_id: str,
) -> list[CurrencyResponse]:
    """Get all currencies in a specific region.

    Args:
        region_id: Region identifier (popular, europe, americas,
                  asia_pacific, middle_east, africa, caribbean).

    Returns:
        List of CurrencyResponse objects in that region.
    """
    try:
        region = CurrencyRegion(region_id.lower())
        currencies = get_currencies_by_region(region)
        return [CurrencyResponse.from_currency_data(c) for c in currencies]
    except ValueError:
        return []


@router.get("/{code}", response_model=CurrencyResponse | None)
async def get_currency_endpoint(code: str) -> CurrencyResponse | None:
    """Get a single currency by ISO 4217 code.

    Args:
        code: Three-letter currency code (e.g., 'USD', 'EUR', 'GBP').

    Returns:
        CurrencyResponse if found, None otherwise.
    """
    currency = get_currency(code)
    if currency:
        return CurrencyResponse.from_currency_data(currency)
    return None
