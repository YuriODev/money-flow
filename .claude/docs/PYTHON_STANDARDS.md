# Python Coding Standards

## Overview

This document defines the Python coding standards for the Subscription Tracker project. All Python code must follow these guidelines to ensure consistency, maintainability, and quality.

## Table of Contents

1. [Code Style](#code-style)
2. [Type Hints](#type-hints)
3. [Documentation](#documentation)
4. [Agentic Code Standards](#agentic-code-standards)
5. [Testing](#testing)
6. [Error Handling](#error-handling)
7. [Async/Await](#asyncawait)
8. [Database Operations](#database-operations)
9. [Redis Caching](#redis-caching)
10. [Linting and Formatting](#linting-and-formatting)

---

## Code Style

### PEP 8 Compliance

All code MUST follow [PEP 8](https://pep8.org/) guidelines with the following modifications:

```python
# ✅ GOOD: Clear, descriptive names
def get_active_subscriptions(user_id: str) -> list[Subscription]:
    """Retrieve all active subscriptions for a user."""
    pass

# ❌ BAD: Unclear names, no type hints
def get_subs(u):
    pass
```

### Line Length

- **Maximum line length**: 100 characters (not 79)
- **Docstring line length**: 88 characters

```python
# ✅ GOOD: Within 100 characters
subscription = await subscription_service.get_by_id(
    subscription_id=sub_id,
    include_inactive=False
)

# ❌ BAD: Exceeds 100 characters
subscription = await subscription_service.get_by_id(subscription_id=sub_id, include_inactive=False, user_id=user.id)
```

### Import Organization

Imports MUST be organized in the following order:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# ✅ GOOD: Properly organized imports
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription
from src.schemas.subscription import SubscriptionCreate
from src.services.subscription_service import SubscriptionService
```

Use `ruff` to automatically sort imports:

```bash
ruff check --select I --fix src/
```

### Naming Conventions

```python
# Classes: PascalCase
class SubscriptionService:
    pass

# Functions/Methods: snake_case
def calculate_next_payment_date():
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_CURRENCY = "GBP"
MAX_RETRY_ATTEMPTS = 3

# Private methods: _leading_underscore
def _validate_amount(self, amount: Decimal) -> bool:
    pass

# Variables: snake_case
subscription_count = 10
is_active = True
```

---

## Type Hints

### Mandatory Type Hints

ALL functions, methods, and class attributes MUST have type hints.

```python
# ✅ GOOD: Complete type hints
from decimal import Decimal
from typing import Optional

async def create_subscription(
    name: str,
    amount: Decimal,
    currency: str = "GBP",
    frequency: str = "monthly"
) -> Subscription:
    """Create a new subscription."""
    pass

# ❌ BAD: Missing type hints
async def create_subscription(name, amount, currency="GBP"):
    pass
```

### Modern Python Type Hints (3.11+)

Use modern type hint syntax:

```python
# ✅ GOOD: Python 3.11+ syntax
from typing import Optional

def get_subscription(id: str) -> Subscription | None:
    pass

def get_all() -> list[Subscription]:
    pass

def get_summary() -> dict[str, Decimal]:
    pass

# ❌ BAD: Old syntax (don't use)
from typing import List, Dict, Union

def get_subscription(id: str) -> Union[Subscription, None]:
    pass

def get_all() -> List[Subscription]:
    pass
```

### TypedDict for Complex Dictionaries

```python
from typing import TypedDict

class CommandResult(TypedDict):
    intent: str
    entities: dict[str, any]
    confidence: float

def parse_command(command: str) -> CommandResult:
    return {
        "intent": "CREATE",
        "entities": {},
        "confidence": 0.95
    }
```

---

## Documentation

### Docstrings

ALL public functions, classes, and methods MUST have docstrings using Google style.

```python
def convert_currency(
    amount: Decimal,
    from_currency: str,
    to_currency: str
) -> Decimal:
    """
    Convert an amount from one currency to another.

    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., "USD")
        to_currency: Target currency code (e.g., "GBP")

    Returns:
        The converted amount as a Decimal

    Raises:
        ValueError: If currency codes are invalid

    Example:
        >>> convert_currency(Decimal("100"), "USD", "GBP")
        Decimal("79.00")
    """
    pass
```

### Module Docstrings

```python
"""
Subscription management service.

This module provides business logic for managing subscriptions,
including CRUD operations, payment calculations, and analytics.
"""

from datetime import date
from decimal import Decimal
```

### Class Docstrings

```python
class SubscriptionService:
    """
    Service for managing subscription lifecycle and operations.

    This service handles all business logic related to subscriptions including:
    - Creating and updating subscriptions
    - Calculating next payment dates
    - Computing spending summaries
    - Managing subscription status (active/inactive)

    Attributes:
        db: AsyncSession instance for database operations
        cache: Redis client for caching (optional)

    Example:
        >>> async with get_db() as session:
        ...     service = SubscriptionService(session)
        ...     subscription = await service.create(data)
    """

    def __init__(self, db: AsyncSession, cache: Optional[Redis] = None) -> None:
        """
        Initialize the subscription service.

        Args:
            db: Async database session for operations
            cache: Optional Redis client for caching results
        """
        self.db = db
        self.cache = cache
```

### Method Docstrings - Complete Format

All methods MUST follow this comprehensive docstring format:

```python
async def calculate_next_payment_date(
    self,
    start_date: date,
    frequency: PaymentFrequency,
    frequency_interval: int = 1,
    reference_date: Optional[date] = None
) -> date:
    """
    Calculate the next payment date for a subscription.

    Computes the next payment date based on the subscription's start date,
    payment frequency, and frequency interval. Handles edge cases like
    month-end dates and leap years.

    Args:
        start_date: The date when the subscription started
        frequency: Payment frequency enum (DAILY, WEEKLY, MONTHLY, etc.)
        frequency_interval: Number of frequency periods between payments.
            For example, 2 for "every 2 weeks" (default: 1)
        reference_date: Optional date to calculate from. If None, uses today's
            date (default: None)

    Returns:
        The next payment date as a date object. Always returns a future date
        relative to the reference_date.

    Raises:
        ValueError: If start_date is in the future relative to reference_date
        ValueError: If frequency_interval is less than 1

    Example:
        >>> service = SubscriptionService(db)
        >>> start = date(2025, 1, 1)
        >>> next_date = await service.calculate_next_payment_date(
        ...     start_date=start,
        ...     frequency=PaymentFrequency.MONTHLY,
        ...     frequency_interval=1
        ... )
        >>> print(next_date)
        2025-02-01

    Note:
        For monthly subscriptions starting on the 31st, if the next month
        has fewer days, the payment date will be the last day of that month.
    """
    if frequency_interval < 1:
        raise ValueError("Frequency interval must be at least 1")

    ref_date = reference_date or date.today()
    if start_date > ref_date:
        raise ValueError("Start date cannot be in the future")

    # Implementation...
```

### Docstring Best Practices

1. **First line**: Brief one-line summary (< 80 chars)
2. **Blank line**: Always separate summary from description
3. **Description**: Detailed explanation of functionality (optional but recommended for complex functions)
4. **Args section**: Document every parameter
   - Include type information (even though type hints exist)
   - Explain valid values, ranges, formats
   - Note default values
5. **Returns section**: Describe what is returned
   - Include type information
   - Explain the structure for complex returns
6. **Raises section**: Document all exceptions that can be raised
   - Explain conditions that trigger each exception
7. **Example section**: Provide usage examples (highly recommended)
   - Use doctests when possible
   - Show realistic use cases
8. **Note/Warning sections**: Add important caveats (optional)

---

## Agentic Code Standards

### Naming Conventions for AI/Agent Code

For agentic and AI-related code, use clear, intent-focused naming:

```python
# ✅ GOOD: Clear agentic naming
class CommandParser:
    """Parse natural language commands into structured intents."""

    async def parse_command(self, user_input: str) -> ParsedCommand:
        """Extract intent and entities from user command."""
        pass

    async def classify_intent(self, text: str) -> Intent:
        """Classify user's intention from natural language."""
        pass

    async def extract_entities(
        self,
        text: str,
        intent: Intent
    ) -> dict[str, Any]:
        """Extract relevant entities based on detected intent."""
        pass

class AgentExecutor:
    """Execute commands based on parsed intent and entities."""

    async def execute_command(self, command: ParsedCommand) -> ExecutionResult:
        """Execute the parsed command and return result."""
        pass

    async def handle_create_intent(self, entities: dict[str, Any]) -> Subscription:
        """Handle CREATE intent for subscription."""
        pass

# ❌ BAD: Vague naming
class Processor:
    async def process(self, input: str) -> Any:
        pass

class Handler:
    async def handle(self, data: dict) -> Any:
        pass
```

### Agentic Function Documentation

Agent-related functions require extra documentation about LLM behavior:

```python
async def parse_natural_language_command(
    self,
    user_input: str,
    context: Optional[dict[str, Any]] = None
) -> ParsedCommand:
    """
    Parse natural language input into structured command using Claude AI.

    Uses Claude Haiku 4.5 model to understand user intent and extract relevant
    entities from natural language. Falls back to regex patterns if AI parsing
    fails or is unavailable.

    Args:
        user_input: Raw natural language input from user.
            Examples:
            - "Add Netflix for £15.99 monthly"
            - "Show my active subscriptions"
            - "Cancel Disney+"
        context: Optional context for parsing such as user preferences,
            recent subscriptions, or conversation history (default: None)

    Returns:
        ParsedCommand object containing:
        - intent: The classified intent (CREATE, READ, UPDATE, DELETE, etc.)
        - entities: Dictionary of extracted entities (name, amount, frequency)
        - confidence: Confidence score from 0.0 to 1.0
        - raw_input: Original user input for reference

    Raises:
        AIParsingException: If both AI and regex parsing fail
        ValueError: If user_input is empty or None

    Example:
        >>> parser = CommandParser(api_key="...")
        >>> command = await parser.parse_natural_language_command(
        ...     "Add Netflix for £15.99 monthly"
        ... )
        >>> print(command.intent)
        Intent.CREATE
        >>> print(command.entities)
        {'name': 'Netflix', 'amount': Decimal('15.99'), 'currency': 'GBP',
         'frequency': 'monthly'}

    AI Behavior:
        - Model: Claude Haiku 4.5 (claude-haiku-4.5-20250929)
        - Temperature: 0.0 for deterministic output
        - Max tokens: 1024
        - System prompt: Loaded from prompts.xml
        - Fallback: Regex patterns if AI unavailable

    Performance:
        - Typical latency: 200-500ms with AI
        - Fallback latency: <10ms with regex
        - Cache: Results cached in Redis for 5 minutes (if available)
    """
    if not user_input or not user_input.strip():
        raise ValueError("User input cannot be empty")

    # Check cache first
    if self.cache:
        cached = await self.cache.get(f"parse:{user_input}")
        if cached:
            return ParsedCommand.parse_raw(cached)

    # Try AI parsing
    try:
        result = await self._parse_with_ai(user_input, context)
    except Exception as e:
        logger.warning(f"AI parsing failed: {e}, falling back to regex")
        result = await self._parse_with_regex(user_input)

    # Cache result
    if self.cache:
        await self.cache.setex(
            f"parse:{user_input}",
            300,  # 5 minutes
            result.json()
        )

    return result
```

### Prompt and LLM Interaction Standards

```python
class PromptLoader:
    """
    Load and format AI prompts from XML configuration.

    Manages system prompts, few-shot examples, and response templates for
    Claude API interactions. Supports XML-based prompt engineering with
    structured sections.

    Attributes:
        tree: Parsed XML element tree
        system_prompt: Cached system prompt string
        examples: List of few-shot examples
    """

    def get_system_prompt(self, include_examples: bool = True) -> str:
        """
        Get formatted system prompt for Claude API.

        Args:
            include_examples: Whether to include few-shot examples in prompt
                (default: True)

        Returns:
            Formatted system prompt string ready for Claude API

        Example:
            >>> loader = PromptLoader()
            >>> prompt = loader.get_system_prompt()
            >>> # Use with Claude API
            >>> response = await client.messages.create(
            ...     model="claude-haiku-4.5-20250929",
            ...     system=prompt,
            ...     messages=[...]
            ... )
        """
        pass
```

### Intent and Entity Naming

```python
from enum import Enum

class Intent(str, Enum):
    """
    User intent classifications for subscription management.

    These intents represent all possible user actions in the system.
    Each intent maps to specific handler methods in AgentExecutor.
    """
    # CRUD operations
    CREATE = "CREATE"  # Create new subscription
    READ = "READ"  # View subscriptions
    UPDATE = "UPDATE"  # Modify existing subscription
    DELETE = "DELETE"  # Remove subscription

    # Analytics
    SUMMARY = "SUMMARY"  # View spending summary
    UPCOMING = "UPCOMING"  # View upcoming payments
    CATEGORY = "CATEGORY"  # Group by category

    # Currency
    CONVERT = "CONVERT"  # Convert between currencies

    # Status management
    PAUSE = "PAUSE"  # Temporarily pause subscription
    RESUME = "RESUME"  # Resume paused subscription

    # Unknown
    UNKNOWN = "UNKNOWN"  # Could not determine intent

# Entity type definitions with clear descriptions
EntityName = str  # Subscription name (e.g., "Netflix", "Spotify")
EntityAmount = Decimal  # Payment amount (positive decimal)
EntityCurrency = str  # ISO 4217 currency code (e.g., "GBP", "USD")
EntityFrequency = str  # Payment frequency (e.g., "monthly", "weekly")
```

---

## Testing

### Test Structure

```python
import pytest
from decimal import Decimal

from src.services.subscription_service import SubscriptionService


class TestSubscriptionService:
    """Test suite for SubscriptionService."""

    @pytest.fixture
    async def service(self, db_session):
        """Provide a SubscriptionService instance."""
        return SubscriptionService(db_session)

    async def test_create_subscription_success(self, service):
        """Test creating a subscription with valid data."""
        # Arrange
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("15.99"),
            start_date=date.today()
        )

        # Act
        result = await service.create(data)

        # Assert
        assert result.name == "Netflix"
        assert result.amount == Decimal("15.99")
        assert result.is_active is True

    async def test_create_subscription_invalid_amount(self, service):
        """Test creating a subscription with invalid amount."""
        # Arrange
        data = SubscriptionCreate(
            name="Netflix",
            amount=Decimal("-10.00"),
            start_date=date.today()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.create(data)
```

### Test Coverage

- **Minimum coverage**: 80%
- **Target coverage**: 90%+

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

---

## Error Handling

### Use Specific Exceptions

```python
# ✅ GOOD: Specific exceptions
async def get_subscription(id: str) -> Subscription:
    subscription = await db.get(Subscription, id)
    if not subscription:
        raise NotFoundException(f"Subscription {id} not found")
    return subscription

# ❌ BAD: Generic exceptions
async def get_subscription(id: str) -> Subscription:
    subscription = await db.get(Subscription, id)
    if not subscription:
        raise Exception("Not found")
    return subscription
```

### Custom Exceptions

```python
class SubscriptionTrackerException(Exception):
    """Base exception for subscription tracker."""
    pass


class NotFoundException(SubscriptionTrackerException):
    """Raised when a resource is not found."""
    pass


class ValidationException(SubscriptionTrackerException):
    """Raised when validation fails."""
    pass


class CurrencyConversionException(SubscriptionTrackerException):
    """Raised when currency conversion fails."""
    pass
```

### Error Logging

```python
import logging

logger = logging.getLogger(__name__)

async def process_payment(subscription_id: str) -> None:
    try:
        subscription = await get_subscription(subscription_id)
        # Process payment...
    except NotFoundException as e:
        logger.warning(f"Subscription not found: {subscription_id}")
        raise
    except Exception as e:
        logger.error(f"Payment processing failed: {e}", exc_info=True)
        raise
```

---

## Async/Await

### Always Use Async for I/O

```python
# ✅ GOOD: Async for database operations
async def get_all_subscriptions(db: AsyncSession) -> list[Subscription]:
    result = await db.execute(select(Subscription))
    return result.scalars().all()

# ❌ BAD: Blocking I/O
def get_all_subscriptions(db: Session) -> list[Subscription]:
    return db.query(Subscription).all()
```

### Avoid Blocking Calls in Async Functions

```python
# ✅ GOOD: Use async libraries
import httpx

async def fetch_exchange_rates() -> dict[str, Decimal]:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.exchangerate.com/rates")
        return response.json()

# ❌ BAD: Blocking requests
import requests

async def fetch_exchange_rates() -> dict[str, Decimal]:
    response = requests.get("https://api.exchangerate.com/rates")  # Blocks!
    return response.json()
```

---

## Database Operations

### Use SQLAlchemy 2.0 Style

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ GOOD: SQLAlchemy 2.0 style
async def get_active_subscriptions(db: AsyncSession) -> list[Subscription]:
    stmt = select(Subscription).where(Subscription.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()

# ❌ BAD: Old query style
async def get_active_subscriptions(db: AsyncSession) -> list[Subscription]:
    return await db.query(Subscription).filter(Subscription.is_active == True).all()
```

### Use Context Managers for Sessions

```python
# ✅ GOOD: Context manager
async with get_db() as session:
    subscription = await session.get(Subscription, sub_id)
    subscription.amount = new_amount
    await session.commit()
```

---

## Redis Caching

### Redis Client Setup

```python
from typing import Optional
import redis.asyncio as redis
from src.core.config import settings

class RedisCache:
    """
    Async Redis cache manager for the application.

    Provides type-safe caching operations with automatic serialization
    and deserialization of Python objects.

    Attributes:
        client: Async Redis client instance
        default_ttl: Default time-to-live in seconds (default: 300)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300
    ) -> None:
        """
        Initialize Redis cache client.

        Args:
            redis_url: Redis connection URL. If None, uses settings.REDIS_URL
                (default: None)
            default_ttl: Default cache expiration in seconds (default: 300)
        """
        url = redis_url or settings.REDIS_URL
        self.client = redis.from_url(url, encoding="utf-8", decode_responses=True)
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise
        """
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds. If None, uses default_ttl
                (default: None)
        """
        expiry = ttl if ttl is not None else self.default_ttl
        await self.client.setex(key, expiry, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.client.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()
```

### Cache Key Naming Conventions

Use structured, predictable cache keys:

```python
# ✅ GOOD: Structured cache keys
# Pattern: {resource}:{identifier}:{operation}

# Single entity
CACHE_KEY_SUBSCRIPTION = "subscription:{subscription_id}"
CACHE_KEY_USER = "user:{user_id}"

# Lists and collections
CACHE_KEY_ACTIVE_SUBS = "subscriptions:active:{user_id}"
CACHE_KEY_CATEGORY_SUBS = "subscriptions:category:{category}:{user_id}"

# Computed results
CACHE_KEY_SUMMARY = "summary:spending:{user_id}:{period}"
CACHE_KEY_UPCOMING = "upcoming:payments:{user_id}:{days}"

# AI/Agent results
CACHE_KEY_PARSE = "parse:command:{hash}"
CACHE_KEY_INTENT = "intent:{text_hash}"

# ❌ BAD: Inconsistent cache keys
subscription_123 = "sub_123"
active = "active_list"
summary1 = "sum_user_1"
```

### Caching Patterns

#### 1. Cache-Aside Pattern

```python
async def get_subscription(
    self,
    subscription_id: str,
    cache: Optional[RedisCache] = None
) -> Optional[Subscription]:
    """
    Get subscription with cache-aside pattern.

    Args:
        subscription_id: Subscription unique identifier
        cache: Optional Redis cache instance

    Returns:
        Subscription if found, None otherwise
    """
    # Try cache first
    if cache:
        cache_key = f"subscription:{subscription_id}"
        cached = await cache.get(cache_key)
        if cached:
            return Subscription.parse_raw(cached)

    # Cache miss - query database
    subscription = await self.db.get(Subscription, subscription_id)

    # Update cache
    if subscription and cache:
        await cache.set(cache_key, subscription.json(), ttl=600)

    return subscription
```

#### 2. Cache Invalidation

```python
async def update_subscription(
    self,
    subscription_id: str,
    data: SubscriptionUpdate,
    cache: Optional[RedisCache] = None
) -> Optional[Subscription]:
    """
    Update subscription and invalidate related caches.

    Args:
        subscription_id: Subscription unique identifier
        data: Update data
        cache: Optional Redis cache instance

    Returns:
        Updated subscription if found, None otherwise
    """
    subscription = await self.db.get(Subscription, subscription_id)
    if not subscription:
        return None

    # Update subscription
    for field, value in data.dict(exclude_unset=True).items():
        setattr(subscription, field, value)

    await self.db.commit()
    await self.db.refresh(subscription)

    # Invalidate caches
    if cache:
        # Invalidate specific subscription
        await cache.delete(f"subscription:{subscription_id}")

        # Invalidate user's subscription lists
        await cache.delete(f"subscriptions:active:{subscription.user_id}")
        await cache.delete(f"subscriptions:all:{subscription.user_id}")

        # Invalidate summaries
        await cache.delete(f"summary:spending:{subscription.user_id}:*")

    return subscription
```

#### 3. Cache Warming

```python
async def warm_subscription_cache(
    self,
    user_id: str,
    cache: RedisCache
) -> None:
    """
    Pre-populate cache with frequently accessed data.

    Args:
        user_id: User identifier
        cache: Redis cache instance
    """
    # Warm active subscriptions
    active_subs = await self.get_active_subscriptions(user_id)
    cache_key = f"subscriptions:active:{user_id}"
    await cache.set(
        cache_key,
        json.dumps([sub.dict() for sub in active_subs]),
        ttl=300
    )

    # Warm spending summary
    summary = await self.get_spending_summary(user_id)
    cache_key = f"summary:spending:{user_id}:monthly"
    await cache.set(cache_key, summary.json(), ttl=600)
```

#### 4. Function-Level Caching Decorator

```python
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

def cached(
    key_pattern: str,
    ttl: int = 300
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for caching function results in Redis.

    Args:
        key_pattern: Cache key pattern with {param} placeholders
        ttl: Cache time-to-live in seconds (default: 300)

    Returns:
        Decorated function with caching

    Example:
        >>> @cached(key_pattern="user:{user_id}:subscriptions", ttl=600)
        ... async def get_user_subscriptions(user_id: str) -> list[Subscription]:
        ...     # Function implementation
        ...     pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Build cache key from pattern and args
            cache_key = key_pattern.format(**kwargs)

            # Try cache
            if hasattr(wrapper, '_cache'):
                cached = await wrapper._cache.get(cache_key)
                if cached:
                    # Deserialize based on return type
                    return deserialize(cached, func.__annotations__['return'])

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if hasattr(wrapper, '_cache'):
                await wrapper._cache.set(cache_key, serialize(result), ttl)

            return result

        return wrapper
    return decorator
```

### Redis Best Practices

1. **Connection Pooling**: Use connection pools for better performance
2. **TTL Management**: Always set appropriate TTLs to prevent memory bloat
3. **Key Expiration**: Use Redis expiration instead of manual deletion
4. **Serialization**: Use efficient serialization (JSON, MessagePack, Pickle)
5. **Error Handling**: Gracefully handle Redis unavailability
6. **Monitoring**: Monitor cache hit rates and adjust TTLs accordingly

### Cache Configuration

```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # Cache TTLs (in seconds)
    CACHE_TTL_SHORT: int = 60  # 1 minute
    CACHE_TTL_MEDIUM: int = 300  # 5 minutes
    CACHE_TTL_LONG: int = 3600  # 1 hour

    # Cache Keys
    CACHE_PREFIX: str = "subtracker"

    class Config:
        env_file = ".env"
```

### Testing with Redis

```python
import pytest
import pytest_asyncio
from redis.asyncio import Redis

@pytest_asyncio.fixture
async def redis_cache():
    """Provide a Redis cache instance for testing."""
    cache = RedisCache(redis_url="redis://localhost:6379/1")  # Use DB 1 for tests
    yield cache

    # Cleanup
    await cache.client.flushdb()  # Clear test database
    await cache.close()

async def test_cache_subscription(redis_cache, subscription_service):
    """Test caching subscription data."""
    # Create subscription
    subscription = await subscription_service.create(test_data)

    # First call - cache miss
    result1 = await subscription_service.get_subscription(
        subscription.id,
        cache=redis_cache
    )

    # Second call - cache hit
    result2 = await subscription_service.get_subscription(
        subscription.id,
        cache=redis_cache
    )

    assert result1 == result2
    # Verify cache was used (check Redis directly)
    cached = await redis_cache.get(f"subscription:{subscription.id}")
    assert cached is not None
```

---

## Linting and Formatting

### Ruff Configuration

Located in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
    "ANN", # flake8-annotations
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "RUF", # Ruff-specific rules
]
ignore = ["ANN101", "ANN102"]  # Don't require type hints for self/cls

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ANN"]  # Don't require annotations in tests
```

### Running Ruff

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### MyPy Configuration

Located in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

### Running MyPy

```bash
# Type check all code
mypy src/

# Type check specific file
mypy src/services/subscription_service.py
```

---

## Quick Checklist

Before committing code, ensure:

- [ ] All functions have type hints
- [ ] All public functions have comprehensive docstrings (Google style)
- [ ] Docstrings include Args, Returns, Raises, and Example sections
- [ ] Code passes `ruff check`
- [ ] Code passes `ruff format --check`
- [ ] Code passes `mypy`
- [ ] Tests are written and passing
- [ ] Coverage is above 80%
- [ ] No `print()` statements (use logging)
- [ ] No hardcoded values (use config/env)
- [ ] Error handling is appropriate
- [ ] Async/await used correctly
- [ ] Agentic code follows intent-based naming
- [ ] AI/LLM functions document model behavior
- [ ] Cache invalidation implemented where needed
- [ ] Redis caching uses structured key patterns

---

## Example: Complete Module

```python
"""
Currency conversion service module.

Provides functionality for converting between different currencies
using both static and live exchange rates.
"""

import logging
from decimal import Decimal
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class CurrencyConversionException(Exception):
    """Raised when currency conversion fails."""
    pass


class CurrencyService:
    """Handle currency conversions and exchange rate management."""

    STATIC_RATES = {
        "GBP": {"USD": Decimal("1.27"), "EUR": Decimal("1.17")},
        "USD": {"GBP": Decimal("0.79"), "EUR": Decimal("0.92")},
        "EUR": {"GBP": Decimal("0.85"), "USD": Decimal("1.09")},
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the currency service.

        Args:
            api_key: Optional API key for live rates
        """
        self.api_key = api_key
        self.use_live_rates = api_key is not None

    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "GBP")

        Returns:
            Converted amount

        Raises:
            CurrencyConversionException: If conversion fails

        Example:
            >>> service = CurrencyService()
            >>> await service.convert(Decimal("100"), "USD", "GBP")
            Decimal("79.00")
        """
        if amount < 0:
            raise ValueError("Amount must be positive")

        if from_currency == to_currency:
            return amount

        try:
            rate = await self._get_rate(from_currency, to_currency)
            return (amount * rate).quantize(Decimal("0.01"))
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            raise CurrencyConversionException(str(e)) from e

    async def _get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate
        """
        if self.use_live_rates:
            return await self._fetch_live_rate(from_currency, to_currency)

        return self.STATIC_RATES[from_currency][to_currency]

    async def _fetch_live_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """Fetch live exchange rate from API."""
        # Implementation here...
        pass
```

---

**Last Updated**: 2025-11-28
**Maintained By**: Development Team
