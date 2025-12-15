"""API Contract Tests using Schemathesis.

This module provides property-based API testing using Schemathesis to:
- Fuzz test all API endpoints with generated data
- Verify responses match OpenAPI schema
- Detect edge cases and unexpected behaviors
- Ensure API contract consistency

Usage:
    pytest tests/contract/test_api_contract.py -v

    # Run with more examples per endpoint
    pytest tests/contract/test_api_contract.py -v --hypothesis-seed=0
"""

import os
import sys
from pathlib import Path

from hypothesis import HealthCheck, settings

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment before importing app
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("RAG_ENABLED", "false")
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_contract.db")

# Import schemathesis and app (must be after env vars are set)
from schemathesis.openapi import from_asgi  # noqa: E402

from src.main import app  # noqa: E402

# Create Schemathesis schema from FastAPI app
schema = from_asgi("/openapi.json", app)

# Configure Hypothesis settings
settings.register_profile(
    "contract",
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
settings.load_profile("contract")


# Test all endpoints - basic server error check
@schema.parametrize()
@settings(max_examples=5)
def test_api_no_server_errors(case):
    """Test that API endpoints don't return 5xx errors.

    This is the most basic contract test - ensures the API
    doesn't crash on any valid input generated from the OpenAPI spec.
    """
    response = case.call()
    # Endpoints may return 4xx for auth/validation errors
    # but should never return 5xx server errors
    assert response.status_code < 500, (
        f"Server error on {case.operation.method.upper()} {case.operation.path.path}: "
        f"{response.status_code} - {response.text[:200] if response.text else 'No body'}"
    )


# Separate test for checking schema validation
@schema.parametrize()
@settings(max_examples=3)
def test_api_response_schema(case):
    """Test that API responses match their defined schemas.

    Validates that successful responses (2xx) conform to the
    response schema defined in the OpenAPI spec.
    """
    response = case.call()

    # Only validate successful responses
    if 200 <= response.status_code < 300:
        case.validate_response(response)
