"""Currency conversion service with live exchange rates.

This module provides currency conversion functionality using the Open Exchange Rates API
for live rates with automatic fallback to static rates. Includes caching for performance.

The service supports all 161+ ISO 4217 currencies with real-time exchange rates.
Popular currencies include GBP, EUR, USD, JPY, CHF, and many more.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx

from src.core.config import settings
from src.data.currencies import (
    ALL_CURRENCY_CODES,
    CURRENCIES,
    POPULAR_CURRENCIES,
    CurrencyData,
    CurrencyRegion,
    get_currencies_by_region,
    get_currency,
    is_valid_currency,
    search_currencies,
)

logger = logging.getLogger(__name__)


class CurrencyConversionError(Exception):
    """Raised when currency conversion fails.

    Attributes:
        message: Human-readable error description.
        from_currency: Source currency code.
        to_currency: Target currency code.
    """

    def __init__(
        self,
        message: str,
        from_currency: str | None = None,
        to_currency: str | None = None,
    ) -> None:
        """Initialize currency conversion error.

        Args:
            message: Error description.
            from_currency: Source currency code if applicable.
            to_currency: Target currency code if applicable.
        """
        super().__init__(message)
        self.message = message
        self.from_currency = from_currency
        self.to_currency = to_currency


class UnsupportedCurrencyError(CurrencyConversionError):
    """Raised when an unsupported currency is requested."""

    pass


@dataclass
class CurrencyInfo:
    """Information about a currency.

    Attributes:
        code: ISO 4217 currency code (e.g., 'GBP').
        symbol: Currency symbol (e.g., '£').
        name: Full currency name (e.g., 'British Pound').
        flag_emoji: Country flag emoji for the currency.
        region: Geographic region for grouping.
        decimal_places: Number of decimal places.
        is_popular: Whether this is a commonly used currency.
    """

    code: str
    symbol: str
    name: str
    flag_emoji: str
    region: str = "popular"
    decimal_places: int = 2
    is_popular: bool = False

    @classmethod
    def from_currency_data(cls, data: CurrencyData) -> "CurrencyInfo":
        """Create CurrencyInfo from CurrencyData.

        Args:
            data: CurrencyData instance.

        Returns:
            CurrencyInfo instance.
        """
        return cls(
            code=data.code,
            symbol=data.symbol,
            name=data.name,
            flag_emoji=data.flag,
            region=data.region.value,
            decimal_places=data.decimal_places,
            is_popular=data.is_popular,
        )


@dataclass
class ExchangeRateCache:
    """Cached exchange rates with expiration.

    Attributes:
        rates: Dictionary mapping currency codes to rates.
        base_currency: Base currency for the rates.
        timestamp: When the rates were fetched.
        expires_at: When the cache expires.
    """

    rates: dict[str, Decimal]
    base_currency: str
    timestamp: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if the cache has expired.

        Returns:
            True if cache is expired, False otherwise.
        """
        return datetime.utcnow() > self.expires_at


class CurrencyService:
    """Handle currency conversions with live and fallback rates.

    This service provides currency conversion functionality using the Open Exchange
    Rates API for live rates. When the API is unavailable or no API key is configured,
    it falls back to static rates.

    The service uses an in-memory cache to reduce API calls and improve performance.
    Cache TTL is configurable via settings. Supports all 161+ ISO 4217 currencies.

    Attributes:
        api_key: Open Exchange Rates API key.
        base_url: API base URL.
        supported_currencies: List of all supported currency codes (161+).
        default_currency: Default currency for conversions.
        _cache: In-memory rate cache.
        _lock: Async lock for thread-safe cache updates.

    Example:
        >>> service = CurrencyService()
        >>> rate = await service.get_rate('USD', 'GBP')
        >>> print(rate)
        Decimal('0.79')

        >>> amount = await service.convert(Decimal('100'), 'USD', 'GBP')
        >>> print(amount)
        Decimal('79.00')
    """

    # Minimal fallback static rates (base: USD) - only used when ALL APIs fail
    # These are approximate and should rarely be used
    STATIC_RATES_USD_BASE: dict[str, Decimal] = {
        "USD": Decimal("1.00"),
        "EUR": Decimal("0.85"),
        "GBP": Decimal("0.75"),
        "JPY": Decimal("155.00"),
        "CNY": Decimal("7.00"),
        "CHF": Decimal("0.80"),
        "CAD": Decimal("1.38"),
        "AUD": Decimal("1.51"),
        "INR": Decimal("90.00"),
        "UAH": Decimal("42.00"),
    }

    # Primary API: fawazahmed0/currency-api (free, no API key, 200+ currencies)
    # https://github.com/fawazahmed0/exchange-api
    PRIMARY_API_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
    # Fallback mirror
    FALLBACK_API_URL = "https://latest.currency-api.pages.dev/v1/currencies/usd.json"

    # Secondary API: Open Exchange Rates (requires API key)
    OPENEXCHANGERATES_API_URL = "https://openexchangerates.org/api"

    def __init__(
        self,
        api_key: str | None = None,
        default_currency: str | None = None,
        cache_ttl: int | None = None,
    ) -> None:
        """Initialize the currency service.

        Args:
            api_key: Open Exchange Rates API key. If None, uses settings or
                falls back to static rates.
            default_currency: Default currency code. If None, uses settings.default_currency.
            cache_ttl: Cache time-to-live in seconds. If None, uses settings.cache_ttl_exchange_rates.

        Example:
            >>> # Use with API key
            >>> service = CurrencyService(api_key="your-api-key")

            >>> # Use with static rates only
            >>> service = CurrencyService()
        """
        self.api_key = api_key or settings.exchange_rate_api_key or None
        self.default_currency = default_currency or settings.default_currency
        self.supported_currencies = ALL_CURRENCY_CODES  # All 161+ currencies
        self.cache_ttl = cache_ttl or settings.cache_ttl_exchange_rates

        self._cache: ExchangeRateCache | None = None
        self._lock = asyncio.Lock()

        if not self.api_key:
            logger.info(
                "No Open Exchange Rates API key configured. "
                "Using free fawazahmed0/currency-api for live rates."
            )

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """Get exchange rate between two currencies.

        Fetches the current exchange rate from the API (with caching) or falls
        back to static rates if the API is unavailable.

        Args:
            from_currency: Source currency code (e.g., 'USD').
            to_currency: Target currency code (e.g., 'GBP').

        Returns:
            Exchange rate as Decimal. Multiply the source amount by this rate
            to get the target amount.

        Raises:
            UnsupportedCurrencyError: If either currency is not supported.
            CurrencyConversionError: If conversion fails and no fallback available.

        Example:
            >>> service = CurrencyService()
            >>> rate = await service.get_rate('USD', 'GBP')
            >>> print(rate)  # e.g., Decimal('0.79')
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Validate currencies
        self._validate_currency(from_currency)
        self._validate_currency(to_currency)

        # Same currency = rate of 1
        if from_currency == to_currency:
            return Decimal("1.00")

        try:
            # Try to get live rates
            rates = await self._get_rates()

            # Calculate cross rate through USD (API uses USD as base)
            from_rate = rates.get(from_currency)
            to_rate = rates.get(to_currency)

            # Check for missing rates - fall back to static if not found in API response
            if from_rate is None:
                logger.warning(f"Rate for {from_currency} not found in live rates, using static")
                from_rate = self.STATIC_RATES_USD_BASE.get(from_currency)
                if from_rate is None:
                    raise UnsupportedCurrencyError(
                        f"No rate available for currency '{from_currency}'",
                        from_currency=from_currency,
                        to_currency=to_currency,
                    )

            if to_rate is None:
                logger.warning(f"Rate for {to_currency} not found in live rates, using static")
                to_rate = self.STATIC_RATES_USD_BASE.get(to_currency)
                if to_rate is None:
                    raise UnsupportedCurrencyError(
                        f"No rate available for currency '{to_currency}'",
                        from_currency=from_currency,
                        to_currency=to_currency,
                    )

            # Guard against zero rates (corrupted data)
            if from_rate == Decimal("0"):
                logger.error(f"Zero rate found for {from_currency}, using fallback")
                raise CurrencyConversionError(
                    f"Invalid zero rate for currency '{from_currency}'",
                    from_currency=from_currency,
                    to_currency=to_currency,
                )

            # from_currency -> USD -> to_currency
            rate = to_rate / from_rate
            return rate.quantize(Decimal("0.000001"))

        except (UnsupportedCurrencyError, CurrencyConversionError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            logger.warning(f"Failed to get live rate, using static: {e}")
            return self._get_static_rate(from_currency, to_currency)

    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """Convert an amount from one currency to another.

        Args:
            amount: Amount to convert. Must be non-negative.
            from_currency: Source currency code (e.g., 'USD').
            to_currency: Target currency code (e.g., 'GBP').

        Returns:
            Converted amount rounded to 2 decimal places.

        Raises:
            ValueError: If amount is negative.
            UnsupportedCurrencyError: If either currency is not supported.
            CurrencyConversionError: If conversion fails.

        Example:
            >>> service = CurrencyService()
            >>> gbp = await service.convert(Decimal('100.00'), 'USD', 'GBP')
            >>> print(gbp)  # e.g., Decimal('79.00')
        """
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        rate = await self.get_rate(from_currency, to_currency)
        converted = amount * rate
        return converted.quantize(Decimal("0.01"))

    async def convert_to_default(
        self,
        amount: Decimal,
        from_currency: str,
    ) -> Decimal:
        """Convert an amount to the default currency.

        Convenience method for converting any currency to the app's default
        currency (GBP by default).

        Args:
            amount: Amount to convert. Must be non-negative.
            from_currency: Source currency code.

        Returns:
            Converted amount in default currency, rounded to 2 decimal places.

        Example:
            >>> service = CurrencyService()  # default_currency='GBP'
            >>> gbp = await service.convert_to_default(Decimal('100'), 'USD')
        """
        return await self.convert(amount, from_currency, self.default_currency)

    async def get_all_rates(
        self,
        base_currency: str | None = None,
    ) -> dict[str, Decimal]:
        """Get all exchange rates for a base currency.

        Args:
            base_currency: Base currency code. If None, uses default currency.

        Returns:
            Dictionary mapping currency codes to exchange rates relative to
            the base currency.

        Raises:
            UnsupportedCurrencyError: If base currency is not supported.

        Example:
            >>> service = CurrencyService()
            >>> rates = await service.get_all_rates('GBP')
            >>> print(rates)
            {'GBP': Decimal('1.00'), 'USD': Decimal('1.27'), ...}
        """
        base = (base_currency or self.default_currency).upper()
        self._validate_currency(base)

        result: dict[str, Decimal] = {}
        for currency in self.supported_currencies:
            rate = await self.get_rate(base, currency)
            result[currency] = rate

        return result

    def get_symbol(self, currency_code: str) -> str:
        """Get currency symbol for a currency code.

        Args:
            currency_code: ISO 4217 currency code (e.g., 'GBP').

        Returns:
            Currency symbol (e.g., '£'). Returns the currency code itself
            if not found.

        Example:
            >>> service = CurrencyService()
            >>> service.get_symbol('GBP')
            '£'
            >>> service.get_symbol('UAH')
            '₴'
        """
        data = get_currency(currency_code)
        return data.symbol if data else currency_code

    def get_currency_info(self, currency_code: str) -> CurrencyInfo | None:
        """Get full currency information.

        Args:
            currency_code: ISO 4217 currency code.

        Returns:
            CurrencyInfo object with code, symbol, name, and flag,
            or None if currency not found.

        Example:
            >>> service = CurrencyService()
            >>> info = service.get_currency_info('GBP')
            >>> print(f"{info.flag_emoji} {info.name}: {info.symbol}")
            🇬🇧 British Pound: £
        """
        data = get_currency(currency_code)
        return CurrencyInfo.from_currency_data(data) if data else None

    def get_all_currency_info(self) -> list[CurrencyInfo]:
        """Get information about all supported currencies.

        Returns:
            List of CurrencyInfo objects for all 161+ supported currencies.

        Example:
            >>> service = CurrencyService()
            >>> currencies = service.get_all_currency_info()
            >>> for c in currencies:
            ...     print(f"{c.flag_emoji} {c.code}")
        """
        return [CurrencyInfo.from_currency_data(c) for c in CURRENCIES]

    def get_popular_currencies(self) -> list[CurrencyInfo]:
        """Get information about popular currencies only.

        Returns:
            List of CurrencyInfo for the most commonly used currencies (24).

        Example:
            >>> service = CurrencyService()
            >>> popular = service.get_popular_currencies()
            >>> print(len(popular))  # 24 popular currencies
        """
        return [CurrencyInfo.from_currency_data(c) for c in POPULAR_CURRENCIES]

    def get_currencies_by_region(self, region: str) -> list[CurrencyInfo]:
        """Get currencies for a specific region.

        Args:
            region: Region name ('europe', 'americas', 'asia_pacific',
                   'middle_east', 'africa', 'caribbean', 'popular').

        Returns:
            List of CurrencyInfo for currencies in that region.

        Example:
            >>> service = CurrencyService()
            >>> european = service.get_currencies_by_region('europe')
            >>> print(len(european))  # 15 European currencies
        """
        try:
            region_enum = CurrencyRegion(region.lower())
            currencies = get_currencies_by_region(region_enum)
            return [CurrencyInfo.from_currency_data(c) for c in currencies]
        except ValueError:
            return []

    def search_currencies(self, query: str, limit: int = 20) -> list[CurrencyInfo]:
        """Search currencies by code, name, or symbol.

        Args:
            query: Search string (case-insensitive).
            limit: Maximum number of results to return.

        Returns:
            List of matching CurrencyInfo objects, sorted by relevance.

        Example:
            >>> service = CurrencyService()
            >>> results = service.search_currencies('dollar')
            >>> print([c.code for c in results])
            ['USD', 'CAD', 'AUD', 'NZD', 'HKD', 'SGD', ...]
        """
        currencies = search_currencies(query, limit)
        return [CurrencyInfo.from_currency_data(c) for c in currencies]

    def format_amount(
        self,
        amount: Decimal,
        currency_code: str,
        include_code: bool = False,
    ) -> str:
        """Format an amount with currency symbol.

        Args:
            amount: Amount to format.
            currency_code: Currency code for symbol lookup.
            include_code: Whether to append currency code (e.g., '£100.00 GBP').

        Returns:
            Formatted amount string.

        Example:
            >>> service = CurrencyService()
            >>> service.format_amount(Decimal('15.99'), 'GBP')
            '£15.99'
            >>> service.format_amount(Decimal('15.99'), 'GBP', include_code=True)
            '£15.99 GBP'
        """
        symbol = self.get_symbol(currency_code)
        formatted = f"{symbol}{amount:.2f}"
        if include_code:
            formatted += f" {currency_code.upper()}"
        return formatted

    def _validate_currency(self, currency_code: str) -> None:
        """Validate that a currency is supported.

        Args:
            currency_code: Currency code to validate.

        Raises:
            UnsupportedCurrencyError: If currency is not supported.
        """
        if not is_valid_currency(currency_code):
            raise UnsupportedCurrencyError(
                f"Currency '{currency_code}' is not a valid ISO 4217 currency code.",
            )

    async def _get_rates(self) -> dict[str, Decimal]:
        """Get exchange rates from cache or API.

        Always attempts to fetch live rates from the free API first.
        Falls back to Open Exchange Rates API if configured, then static rates.

        Returns:
            Dictionary of currency codes to USD-based rates.

        Raises:
            CurrencyConversionError: If unable to fetch rates.
        """
        # Check cache first
        if self._cache and not self._cache.is_expired():
            return self._cache.rates

        # Acquire lock to prevent concurrent API calls
        async with self._lock:
            # Double-check cache after acquiring lock
            if self._cache and not self._cache.is_expired():
                return self._cache.rates

            # Always try to fetch live rates (free API doesn't need key)
            rates = await self._fetch_live_rates()

            # Update cache
            now = datetime.utcnow()
            self._cache = ExchangeRateCache(
                rates=rates,
                base_currency="USD",
                timestamp=now,
                expires_at=now + timedelta(seconds=self.cache_ttl),
            )

            return rates

    async def _fetch_live_rates(self) -> dict[str, Decimal]:
        """Fetch live exchange rates from free currency API.

        Tries multiple sources in order:
        1. fawazahmed0/currency-api (free, no API key, 200+ currencies)
        2. Fallback mirror of the same API
        3. Open Exchange Rates API (if API key configured)
        4. Static fallback rates (last resort)

        Returns:
            Dictionary of currency codes to USD-based rates.

        Raises:
            CurrencyConversionError: If all API requests fail.
        """
        # Try primary free API first (fawazahmed0/currency-api)
        try:
            rates = await self._fetch_from_free_api(self.PRIMARY_API_URL)
            if rates:
                logger.info(f"Fetched {len(rates)} rates from primary free API")
                return rates
        except Exception as e:
            logger.warning(f"Primary free API failed: {e}")

        # Try fallback mirror
        try:
            rates = await self._fetch_from_free_api(self.FALLBACK_API_URL)
            if rates:
                logger.info(f"Fetched {len(rates)} rates from fallback free API")
                return rates
        except Exception as e:
            logger.warning(f"Fallback free API failed: {e}")

        # Try Open Exchange Rates if API key is configured
        if self.api_key:
            try:
                rates = await self._fetch_from_openexchangerates()
                if rates:
                    logger.info(f"Fetched {len(rates)} rates from Open Exchange Rates")
                    return rates
            except Exception as e:
                logger.warning(f"Open Exchange Rates API failed: {e}")

        # Last resort: use static rates
        logger.warning("All exchange rate APIs failed, using static fallback rates")
        return self.STATIC_RATES_USD_BASE.copy()

    async def _fetch_from_free_api(self, url: str) -> dict[str, Decimal]:
        """Fetch rates from fawazahmed0/currency-api.

        Args:
            url: API URL to fetch from.

        Returns:
            Dictionary of currency codes to USD-based rates.

        Raises:
            Exception: If request fails.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: dict[str, Any] = response.json()

        rates: dict[str, Decimal] = {}
        # The API returns {"date": "...", "usd": {"eur": 0.85, "gbp": 0.75, ...}}
        usd_rates = data.get("usd", {})

        for code, rate in usd_rates.items():
            # Convert to uppercase and filter valid ISO 4217 currencies
            code_upper = code.upper()
            if is_valid_currency(code_upper) and isinstance(rate, (int, float)):
                rates[code_upper] = Decimal(str(rate))

        # Ensure USD is always 1.00
        rates["USD"] = Decimal("1.00")

        return rates

    async def _fetch_from_openexchangerates(self) -> dict[str, Decimal]:
        """Fetch rates from Open Exchange Rates API.

        Returns:
            Dictionary of currency codes to USD-based rates.

        Raises:
            Exception: If request fails.
        """
        url = f"{self.OPENEXCHANGERATES_API_URL}/latest.json"
        params: dict[str, str] = {"app_id": self.api_key or ""}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data: dict[str, Any] = response.json()

        rates: dict[str, Decimal] = {}
        for code, rate in data.get("rates", {}).items():
            if is_valid_currency(code):
                rates[code] = Decimal(str(rate))

        return rates

    def _get_static_rate(
        self,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """Get exchange rate from static rates.

        Args:
            from_currency: Source currency code.
            to_currency: Target currency code.

        Returns:
            Exchange rate from static rates.

        Raises:
            UnsupportedCurrencyError: If currency not in static rates.
            CurrencyConversionError: If from_rate is zero.
        """
        # Static rates are USD-based, calculate cross rate
        from_rate = self.STATIC_RATES_USD_BASE.get(from_currency)
        to_rate = self.STATIC_RATES_USD_BASE.get(to_currency)

        # Validate rates exist
        if from_rate is None:
            raise UnsupportedCurrencyError(
                f"Currency '{from_currency}' not available in static rates. "
                f"Available: {', '.join(self.STATIC_RATES_USD_BASE.keys())}",
                from_currency=from_currency,
                to_currency=to_currency,
            )
        if to_rate is None:
            raise UnsupportedCurrencyError(
                f"Currency '{to_currency}' not available in static rates. "
                f"Available: {', '.join(self.STATIC_RATES_USD_BASE.keys())}",
                from_currency=from_currency,
                to_currency=to_currency,
            )

        # Guard against zero rate (should never happen with static data, but safety first)
        if from_rate == Decimal("0"):
            raise CurrencyConversionError(
                f"Invalid zero rate for currency '{from_currency}'",
                from_currency=from_currency,
                to_currency=to_currency,
            )

        rate = to_rate / from_rate
        return rate.quantize(Decimal("0.000001"))

    async def refresh_cache(self) -> None:
        """Force refresh of the exchange rate cache.

        Invalidates the current cache and fetches fresh rates.

        Example:
            >>> service = CurrencyService(api_key="your-key")
            >>> await service.refresh_cache()
        """
        async with self._lock:
            self._cache = None
            await self._get_rates()
            logger.info("Exchange rate cache refreshed")
