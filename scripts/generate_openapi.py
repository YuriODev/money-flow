#!/usr/bin/env python3
"""Generate OpenAPI specification from FastAPI app.

This script exports the OpenAPI schema to a JSON file for:
- Contract testing with Schemathesis
- API documentation versioning
- Breaking change detection

Usage:
    python scripts/generate_openapi.py [output_path]

    Default output: docs/openapi.json
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Disable rate limiting and other features that require external services
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("RAG_ENABLED", "false")
os.environ.setdefault("SENTRY_DSN", "")


def generate_openapi_spec(output_path: str | None = None) -> dict:
    """Generate OpenAPI spec from FastAPI app.

    Args:
        output_path: Optional path to write the spec. If None, returns dict only.

    Returns:
        OpenAPI specification as dictionary.
    """
    # Import app after setting environment
    from src.main import app

    # Get OpenAPI schema
    openapi_schema = app.openapi()

    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "Money Flow API Support",
        "url": "https://github.com/subscription-tracker/issues",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    # Write to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(openapi_schema, f, indent=2)

        print(f"OpenAPI spec written to: {output_file}")
        print(f"Endpoints: {len(openapi_schema.get('paths', {}))}")
        print(f"Schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")

    return openapi_schema


def validate_spec(spec: dict) -> bool:
    """Validate OpenAPI spec structure.

    Args:
        spec: OpenAPI specification dictionary.

    Returns:
        True if valid, raises exception otherwise.
    """
    try:
        from openapi_spec_validator import validate

        validate(spec)
        print("OpenAPI spec is valid!")
        return True
    except ImportError:
        print("Warning: openapi-spec-validator not installed, skipping validation")
        return True
    except Exception as e:
        print(f"OpenAPI spec validation failed: {e}")
        return False


if __name__ == "__main__":
    # Default output path
    default_output = project_root / "docs" / "openapi.json"
    output_path = sys.argv[1] if len(sys.argv) > 1 else str(default_output)

    # Generate spec
    spec = generate_openapi_spec(output_path)

    # Validate
    validate_spec(spec)
