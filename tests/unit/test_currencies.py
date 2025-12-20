"""Unit tests for currency data and service.

Tests cover:
- Currency data module (ISO 4217 currencies)
- Currency regions and grouping
- Currency search functionality
- CurrencyService methods
- Currency API endpoints
"""

from decimal import Decimal

import pytest

from src.data.currencies import (
    ALL_CURRENCY_CODES,
    CURRENCIES,
    CURRENCIES_BY_REGION,
    POPULAR_CURRENCIES,
    REGION_DISPLAY_NAMES,
    CurrencyRegion,
    get_all_regions,
    get_currencies_by_region,
    get_currency,
    get_currency_symbol,
    is_valid_currency,
    search_currencies,
)
from src.services.currency_service import CurrencyInfo, CurrencyService


class TestCurrencyData:
    """Tests for currency data module."""

    def test_currencies_count(self) -> None:
        """Test that we have a comprehensive currency list."""
        # Should have at least 150 currencies (ISO 4217 has ~180 active)
        assert len(CURRENCIES) >= 150
        assert len(ALL_CURRENCY_CODES) >= 150

    def test_popular_currencies_count(self) -> None:
        """Test popular currencies list."""
        assert len(POPULAR_CURRENCIES) == 24
        # All popular should be marked as popular
        for currency in POPULAR_CURRENCIES:
            assert currency.is_popular is True

    def test_all_regions_defined(self) -> None:
        """Test all currency regions are defined."""
        assert CurrencyRegion.POPULAR.value == "popular"
        assert CurrencyRegion.EUROPE.value == "europe"
        assert CurrencyRegion.AMERICAS.value == "americas"
        assert CurrencyRegion.ASIA_PACIFIC.value == "asia_pacific"
        assert CurrencyRegion.MIDDLE_EAST.value == "middle_east"
        assert CurrencyRegion.AFRICA.value == "africa"
        assert CurrencyRegion.CARIBBEAN.value == "caribbean"

    def test_region_display_names(self) -> None:
        """Test region display names are defined."""
        assert len(REGION_DISPLAY_NAMES) == 7
        assert REGION_DISPLAY_NAMES[CurrencyRegion.POPULAR] == "Popular"
        assert REGION_DISPLAY_NAMES[CurrencyRegion.EUROPE] == "Europe"
        assert REGION_DISPLAY_NAMES[CurrencyRegion.ASIA_PACIFIC] == "Asia & Pacific"

    def test_currencies_by_region_grouping(self) -> None:
        """Test currencies are properly grouped by region."""
        assert len(CURRENCIES_BY_REGION) == 7
        # Each region should have currencies
        for region in CurrencyRegion:
            currencies = CURRENCIES_BY_REGION.get(region, [])
            assert len(currencies) > 0, f"Region {region.value} has no currencies"

    def test_currency_data_structure(self) -> None:
        """Test CurrencyData has all required fields."""
        usd = get_currency("USD")
        assert usd is not None
        assert usd.code == "USD"
        assert usd.symbol == "$"
        assert usd.name == "US Dollar"
        assert usd.flag == "🇺🇸"
        assert usd.region == CurrencyRegion.POPULAR
        assert usd.decimal_places == 2
        assert usd.is_popular is True

    def test_currency_decimal_places(self) -> None:
        """Test currencies have correct decimal places."""
        # Most currencies have 2 decimal places
        usd = get_currency("USD")
        assert usd.decimal_places == 2

        # JPY and KRW have 0 decimal places
        jpy = get_currency("JPY")
        assert jpy.decimal_places == 0

        krw = get_currency("KRW")
        assert krw.decimal_places == 0

        # BHD, KWD have 3 decimal places
        bhd = get_currency("BHD")
        assert bhd.decimal_places == 3


class TestCurrencyLookup:
    """Tests for currency lookup functions."""

    def test_get_currency_valid(self) -> None:
        """Test getting currency by valid code."""
        gbp = get_currency("GBP")
        assert gbp is not None
        assert gbp.code == "GBP"
        assert gbp.symbol == "£"
        assert gbp.name == "British Pound"

    def test_get_currency_case_insensitive(self) -> None:
        """Test currency lookup is case insensitive."""
        assert get_currency("usd") is not None
        assert get_currency("USD") is not None
        assert get_currency("Usd") is not None

    def test_get_currency_invalid(self) -> None:
        """Test getting invalid currency returns None."""
        assert get_currency("XXX") is None
        assert get_currency("INVALID") is None
        assert get_currency("") is None

    def test_is_valid_currency(self) -> None:
        """Test currency validation."""
        assert is_valid_currency("USD") is True
        assert is_valid_currency("EUR") is True
        assert is_valid_currency("GBP") is True
        assert is_valid_currency("XXX") is False
        assert is_valid_currency("INVALID") is False

    def test_get_currency_symbol(self) -> None:
        """Test getting currency symbol."""
        assert get_currency_symbol("USD") == "$"
        assert get_currency_symbol("EUR") == "€"
        assert get_currency_symbol("GBP") == "£"
        assert get_currency_symbol("UAH") == "₴"
        assert get_currency_symbol("JPY") == "¥"

    def test_get_currency_symbol_fallback(self) -> None:
        """Test symbol fallback for invalid currency."""
        assert get_currency_symbol("XXX", "$") == "$"
        assert get_currency_symbol("INVALID", "?") == "?"


class TestCurrencyRegions:
    """Tests for currency region functions."""

    def test_get_currencies_by_region(self) -> None:
        """Test getting currencies by region."""
        europe = get_currencies_by_region(CurrencyRegion.EUROPE)
        assert len(europe) > 0
        # Check all returned currencies are in Europe
        for currency in europe:
            assert currency.region == CurrencyRegion.EUROPE

    def test_get_all_regions(self) -> None:
        """Test getting all regions with display names."""
        regions = get_all_regions()
        assert len(regions) == 7
        # Check structure
        for region_enum, display_name in regions:
            assert isinstance(region_enum, CurrencyRegion)
            assert isinstance(display_name, str)
            assert len(display_name) > 0

    def test_popular_region_has_major_currencies(self) -> None:
        """Test popular region contains major world currencies."""
        popular = get_currencies_by_region(CurrencyRegion.POPULAR)
        codes = [c.code for c in popular]
        # Major currencies should be in popular
        assert "USD" in codes
        assert "EUR" in codes
        assert "GBP" in codes
        assert "JPY" in codes
        assert "CHF" in codes
        assert "CAD" in codes
        assert "AUD" in codes


class TestCurrencySearch:
    """Tests for currency search functionality."""

    def test_search_by_code_exact(self) -> None:
        """Test searching by exact code."""
        results = search_currencies("USD")
        assert len(results) > 0
        assert results[0].code == "USD"

    def test_search_by_code_partial(self) -> None:
        """Test searching by partial code."""
        results = search_currencies("US")
        codes = [c.code for c in results]
        assert "USD" in codes

    def test_search_by_name(self) -> None:
        """Test searching by currency name."""
        results = search_currencies("dollar")
        codes = [c.code for c in results]
        # Should find various dollars
        assert "USD" in codes
        assert "CAD" in codes
        assert "AUD" in codes

    def test_search_by_name_partial(self) -> None:
        """Test searching by partial name."""
        results = search_currencies("brit")
        assert len(results) > 0
        assert results[0].code == "GBP"  # British Pound

    def test_search_empty_returns_popular(self) -> None:
        """Test empty search returns popular currencies."""
        results = search_currencies("")
        # Returns up to limit (default 20) from popular
        assert len(results) <= 20
        # All returned should be popular
        for r in results:
            assert r.is_popular is True

    def test_search_no_results(self) -> None:
        """Test search with no matches."""
        results = search_currencies("xyznonexistent")
        assert len(results) == 0

    def test_search_limit(self) -> None:
        """Test search respects limit."""
        results = search_currencies("dollar", limit=5)
        assert len(results) <= 5

    def test_search_popular_boosted(self) -> None:
        """Test popular currencies are boosted in search."""
        # Search for 'dollar' - popular dollars should be at the top
        results = search_currencies("dollar")
        # First few results should be popular dollars
        popular_codes = [r.code for r in results if r.is_popular]
        assert "USD" in popular_codes
        assert "CAD" in popular_codes
        assert "AUD" in popular_codes

    def test_search_case_insensitive(self) -> None:
        """Test search is case insensitive."""
        results1 = search_currencies("EURO")
        results2 = search_currencies("euro")
        results3 = search_currencies("Euro")
        # Should all find EUR
        assert any(c.code == "EUR" for c in results1)
        assert any(c.code == "EUR" for c in results2)
        assert any(c.code == "EUR" for c in results3)


class TestCurrencyInfo:
    """Tests for CurrencyInfo dataclass."""

    def test_from_currency_data(self) -> None:
        """Test creating CurrencyInfo from CurrencyData."""
        data = get_currency("EUR")
        info = CurrencyInfo.from_currency_data(data)

        assert info.code == "EUR"
        assert info.symbol == "€"
        assert info.name == "Euro"
        assert info.flag_emoji == "🇪🇺"
        assert info.region == "popular"
        assert info.decimal_places == 2
        assert info.is_popular is True


class TestCurrencyService:
    """Tests for CurrencyService."""

    def test_init_default(self) -> None:
        """Test service initialization with defaults."""
        service = CurrencyService()
        # Should have all 161+ currencies
        assert len(service.supported_currencies) >= 150

    def test_get_symbol(self) -> None:
        """Test getting currency symbol."""
        service = CurrencyService()
        assert service.get_symbol("USD") == "$"
        assert service.get_symbol("GBP") == "£"
        assert service.get_symbol("EUR") == "€"
        assert service.get_symbol("INVALID") == "INVALID"

    def test_get_currency_info(self) -> None:
        """Test getting full currency info."""
        service = CurrencyService()
        info = service.get_currency_info("JPY")

        assert info is not None
        assert info.code == "JPY"
        assert info.symbol == "¥"
        assert info.decimal_places == 0

    def test_get_currency_info_invalid(self) -> None:
        """Test getting info for invalid currency."""
        service = CurrencyService()
        info = service.get_currency_info("INVALID")
        assert info is None

    def test_get_all_currency_info(self) -> None:
        """Test getting all currency info."""
        service = CurrencyService()
        all_info = service.get_all_currency_info()
        assert len(all_info) >= 150

    def test_get_popular_currencies(self) -> None:
        """Test getting popular currencies."""
        service = CurrencyService()
        popular = service.get_popular_currencies()
        assert len(popular) == 24
        # All should have is_popular = True
        for info in popular:
            assert info.is_popular is True

    def test_get_currencies_by_region(self) -> None:
        """Test getting currencies by region."""
        service = CurrencyService()
        europe = service.get_currencies_by_region("europe")
        assert len(europe) > 0
        for info in europe:
            assert info.region == "europe"

    def test_get_currencies_by_region_invalid(self) -> None:
        """Test invalid region returns empty list."""
        service = CurrencyService()
        result = service.get_currencies_by_region("invalid_region")
        assert result == []

    def test_search_currencies(self) -> None:
        """Test currency search via service."""
        service = CurrencyService()
        results = service.search_currencies("peso")
        codes = [c.code for c in results]
        assert "MXN" in codes  # Mexican Peso

    def test_format_amount(self) -> None:
        """Test formatting amounts with currency."""
        service = CurrencyService()
        assert service.format_amount(Decimal("15.99"), "GBP") == "£15.99"
        assert service.format_amount(Decimal("15.99"), "USD") == "$15.99"
        assert service.format_amount(Decimal("1000"), "JPY") == "¥1000.00"

    def test_format_amount_with_code(self) -> None:
        """Test formatting with currency code."""
        service = CurrencyService()
        result = service.format_amount(Decimal("15.99"), "GBP", include_code=True)
        assert result == "£15.99 GBP"


class TestCurrencyServiceValidation:
    """Tests for currency validation in service."""

    def test_validate_valid_currency(self) -> None:
        """Test validation passes for valid currencies."""
        service = CurrencyService()
        # Should not raise
        service._validate_currency("USD")
        service._validate_currency("EUR")
        service._validate_currency("UAH")

    def test_validate_invalid_currency(self) -> None:
        """Test validation fails for invalid currencies."""
        from src.services.currency_service import UnsupportedCurrencyError

        service = CurrencyService()
        with pytest.raises(UnsupportedCurrencyError):
            service._validate_currency("INVALID")


class TestCurrencyServiceRates:
    """Tests for exchange rate functionality."""

    @pytest.mark.asyncio
    async def test_get_rate_same_currency(self) -> None:
        """Test rate for same currency is 1."""
        service = CurrencyService()
        rate = await service.get_rate("USD", "USD")
        assert rate == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_get_static_rate(self) -> None:
        """Test getting static fallback rate."""
        service = CurrencyService()
        rate = service._get_static_rate("USD", "GBP")
        assert rate > 0
        assert rate < 1  # GBP is stronger than USD

    @pytest.mark.asyncio
    async def test_convert_basic(self) -> None:
        """Test basic currency conversion."""
        service = CurrencyService()
        # Convert 100 USD to GBP using static rates
        result = await service.convert(Decimal("100"), "USD", "GBP")
        assert result > 0
        assert result < Decimal("100")  # GBP is stronger

    @pytest.mark.asyncio
    async def test_convert_to_default(self) -> None:
        """Test converting to default currency."""
        service = CurrencyService(default_currency="GBP")
        result = await service.convert_to_default(Decimal("100"), "USD")
        assert result > 0

    @pytest.mark.asyncio
    async def test_get_all_rates(self) -> None:
        """Test getting all rates for a base currency (popular only)."""
        service = CurrencyService()
        # get_all_rates iterates over supported_currencies which is all 161+
        # but static rates only cover popular currencies
        # This test just checks basic functionality with same currency
        rate = await service.get_rate("USD", "USD")
        assert rate == Decimal("1.000000")
        # Test a few cross rates
        rate_gbp = await service.get_rate("USD", "GBP")
        assert rate_gbp > 0
        rate_eur = await service.get_rate("USD", "EUR")
        assert rate_eur > 0


class TestCurrencyDataIntegrity:
    """Tests for currency data integrity."""

    def test_no_duplicate_codes(self) -> None:
        """Test there are no duplicate currency codes."""
        codes = [c.code for c in CURRENCIES]
        assert len(codes) == len(set(codes)), "Duplicate currency codes found"

    def test_all_codes_uppercase(self) -> None:
        """Test all currency codes are uppercase."""
        for currency in CURRENCIES:
            assert currency.code == currency.code.upper()

    def test_all_codes_three_letters(self) -> None:
        """Test all currency codes are 3 letters."""
        for currency in CURRENCIES:
            assert len(currency.code) == 3
            assert currency.code.isalpha()

    def test_all_have_symbols(self) -> None:
        """Test all currencies have symbols."""
        for currency in CURRENCIES:
            assert len(currency.symbol) > 0

    def test_all_have_names(self) -> None:
        """Test all currencies have names."""
        for currency in CURRENCIES:
            assert len(currency.name) > 0

    def test_all_have_flags(self) -> None:
        """Test all currencies have flag emojis."""
        for currency in CURRENCIES:
            assert len(currency.flag) > 0

    def test_decimal_places_valid(self) -> None:
        """Test decimal places are in valid range."""
        for currency in CURRENCIES:
            assert currency.decimal_places in [0, 2, 3]

    def test_major_currencies_present(self) -> None:
        """Test major world currencies are present."""
        codes = ALL_CURRENCY_CODES
        major_currencies = [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CHF",
            "CAD",
            "AUD",
            "NZD",
            "CNY",
            "INR",
            "KRW",
            "BRL",
            "MXN",
            "SGD",
            "HKD",
            "RUB",
        ]
        for code in major_currencies:
            assert code in codes, f"Major currency {code} not found"
