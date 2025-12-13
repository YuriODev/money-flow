"""Comprehensive tests for CurrencyService.

Tests cover:
- Currency conversion with live and static rates
- Exchange rate caching
- Error handling and fallbacks
- Currency information retrieval
- Amount formatting
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.currency_service import (
    CurrencyConversionError,
    CurrencyInfo,
    CurrencyService,
    ExchangeRateCache,
    UnsupportedCurrencyError,
)


class TestCurrencyInfo:
    """Tests for CurrencyInfo dataclass."""

    def test_create_currency_info(self):
        """Test creating CurrencyInfo instance."""
        info = CurrencyInfo(code="GBP", symbol="£", name="British Pound", flag_emoji="🇬🇧")

        assert info.code == "GBP"
        assert info.symbol == "£"
        assert info.name == "British Pound"
        assert info.flag_emoji == "🇬🇧"


class TestExchangeRateCache:
    """Tests for ExchangeRateCache dataclass."""

    def test_cache_not_expired(self):
        """Test cache is not expired when within TTL."""
        cache = ExchangeRateCache(
            rates={"USD": Decimal("1.00")},
            base_currency="USD",
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        assert cache.is_expired() is False

    def test_cache_expired(self):
        """Test cache is expired when past TTL."""
        cache = ExchangeRateCache(
            rates={"USD": Decimal("1.00")},
            base_currency="USD",
            timestamp=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        assert cache.is_expired() is True


class TestCurrencyService:
    """Tests for CurrencyService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = CurrencyService()

    def test_init_without_api_key(self):
        """Test initialization without API key uses static rates."""
        service = CurrencyService(api_key=None)

        assert service.api_key is None
        assert service.default_currency == "GBP"
        assert len(service.supported_currencies) == 4

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        service = CurrencyService(api_key="test-key")

        assert service.api_key == "test-key"

    def test_init_custom_defaults(self):
        """Test initialization with custom defaults."""
        service = CurrencyService(
            default_currency="USD",
            cache_ttl=7200,
        )

        assert service.default_currency == "USD"
        assert service.cache_ttl == 7200

    def test_get_symbol(self):
        """Test getting currency symbols."""
        assert self.service.get_symbol("GBP") == "£"
        assert self.service.get_symbol("EUR") == "€"
        assert self.service.get_symbol("USD") == "$"
        assert self.service.get_symbol("UAH") == "₴"

    def test_get_symbol_lowercase(self):
        """Test getting symbol with lowercase input."""
        assert self.service.get_symbol("gbp") == "£"

    def test_get_symbol_unknown(self):
        """Test getting symbol for unknown currency returns code."""
        assert self.service.get_symbol("XYZ") == "XYZ"

    def test_get_currency_info(self):
        """Test getting full currency info."""
        info = self.service.get_currency_info("GBP")

        assert info is not None
        assert info.code == "GBP"
        assert info.symbol == "£"
        assert info.name == "British Pound"
        assert info.flag_emoji == "🇬🇧"

    def test_get_currency_info_none(self):
        """Test getting info for unknown currency returns None."""
        info = self.service.get_currency_info("XYZ")

        assert info is None

    def test_get_all_currency_info(self):
        """Test getting all currency info."""
        all_info = self.service.get_all_currency_info()

        assert len(all_info) == 4
        codes = [info.code for info in all_info]
        assert "GBP" in codes
        assert "EUR" in codes
        assert "USD" in codes
        assert "UAH" in codes

    def test_format_amount(self):
        """Test formatting amount with currency symbol."""
        formatted = self.service.format_amount(Decimal("15.99"), "GBP")

        assert formatted == "£15.99"

    def test_format_amount_with_code(self):
        """Test formatting amount with currency code."""
        formatted = self.service.format_amount(Decimal("15.99"), "GBP", include_code=True)

        assert formatted == "£15.99 GBP"

    def test_format_amount_uah(self):
        """Test formatting UAH amount."""
        formatted = self.service.format_amount(Decimal("1000.00"), "UAH")

        assert formatted == "₴1000.00"

    def test_validate_currency_valid(self):
        """Test validation of valid currency."""
        # Should not raise
        self.service._validate_currency("GBP")
        self.service._validate_currency("EUR")
        self.service._validate_currency("USD")
        self.service._validate_currency("UAH")

    def test_validate_currency_invalid(self):
        """Test validation of invalid currency raises error."""
        with pytest.raises(UnsupportedCurrencyError) as exc_info:
            self.service._validate_currency("XYZ")

        assert "XYZ" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    def test_get_static_rate_same_currency(self):
        """Test static rate for same currency is 1."""
        rate = self.service._get_static_rate("USD", "USD")

        assert rate == Decimal("1.000000")

    def test_get_static_rate_usd_to_gbp(self):
        """Test static rate USD to GBP."""
        rate = self.service._get_static_rate("USD", "GBP")

        assert rate == Decimal("0.790000")

    def test_get_static_rate_gbp_to_usd(self):
        """Test static rate GBP to USD."""
        rate = self.service._get_static_rate("GBP", "USD")

        # 1 / 0.79 ≈ 1.27
        assert rate > Decimal("1.0")


class TestCurrencyServiceAsync:
    """Async tests for CurrencyService."""

    @pytest.fixture
    def service(self):
        """Create service for testing."""
        return CurrencyService()

    @pytest.mark.asyncio
    async def test_get_rate_same_currency(self, service):
        """Test rate for same currency is 1."""
        rate = await service.get_rate("GBP", "GBP")

        assert rate == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_get_rate_uses_static_fallback(self, service):
        """Test getting rate without API key uses static rates."""
        rate = await service.get_rate("USD", "GBP")

        assert rate == Decimal("0.790000")

    @pytest.mark.asyncio
    async def test_get_rate_invalid_from_currency(self, service):
        """Test getting rate with invalid from currency."""
        with pytest.raises(UnsupportedCurrencyError):
            await service.get_rate("XYZ", "GBP")

    @pytest.mark.asyncio
    async def test_get_rate_invalid_to_currency(self, service):
        """Test getting rate with invalid to currency."""
        with pytest.raises(UnsupportedCurrencyError):
            await service.get_rate("GBP", "XYZ")

    @pytest.mark.asyncio
    async def test_convert_amount(self, service):
        """Test converting amount between currencies."""
        result = await service.convert(Decimal("100.00"), "USD", "GBP")

        # $100 * 0.79 = £79.00
        assert result == Decimal("79.00")

    @pytest.mark.asyncio
    async def test_convert_negative_raises(self, service):
        """Test converting negative amount raises error."""
        with pytest.raises(ValueError, match="non-negative"):
            await service.convert(Decimal("-10.00"), "USD", "GBP")

    @pytest.mark.asyncio
    async def test_convert_to_default(self, service):
        """Test converting to default currency."""
        result = await service.convert_to_default(Decimal("100.00"), "USD")

        # Default is GBP: $100 * 0.79 = £79.00
        assert result == Decimal("79.00")

    @pytest.mark.asyncio
    async def test_get_all_rates(self, service):
        """Test getting all rates for a base currency."""
        rates = await service.get_all_rates("USD")

        assert "USD" in rates
        assert "GBP" in rates
        assert "EUR" in rates
        assert "UAH" in rates
        assert rates["USD"] == Decimal("1.000000")

    @pytest.mark.asyncio
    async def test_cache_is_used(self, service):
        """Test that cache is used for subsequent calls."""
        # First call populates cache
        await service.get_rate("USD", "GBP")

        # Cache should now exist
        assert service._cache is not None
        assert not service._cache.is_expired()


class TestCurrencyServiceWithMockedAPI:
    """Tests for CurrencyService with mocked API calls."""

    @pytest.fixture
    def service_with_key(self):
        """Create service with API key."""
        return CurrencyService(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_fetch_live_rates_success(self, service_with_key):
        """Test fetching live rates from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {
                "GBP": 0.79,
                "EUR": 0.92,
                "USD": 1.0,
                "UAH": 41.50,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            rates = await service_with_key._fetch_live_rates()

            assert "GBP" in rates
            assert rates["GBP"] == Decimal("0.79")

    @pytest.mark.asyncio
    async def test_api_error_falls_back_to_static(self, service_with_key):
        """Test that API errors fall back to static rates."""
        with patch.object(
            service_with_key, "_fetch_live_rates", side_effect=CurrencyConversionError("API Error")
        ):
            # Should not raise, should use static rates
            rate = await service_with_key.get_rate("USD", "GBP")

            assert rate == Decimal("0.790000")
