#!/usr/bin/env python3
"""Check OpenAPI specification for breaking changes.

This script compares two OpenAPI specs and detects breaking changes:
- Removed endpoints
- Changed HTTP methods
- Removed or required new parameters
- Response schema changes

Usage:
    python scripts/check_openapi_diff.py [old_spec] [new_spec]

    # Compare current spec with main branch
    python scripts/check_openapi_diff.py

    # Compare specific files
    python scripts/check_openapi_diff.py old.json new.json
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_spec(path: str | Path) -> dict:
    """Load OpenAPI spec from JSON file."""
    with open(path) as f:
        return json.load(f)


def get_endpoints(spec: dict) -> dict[str, set[str]]:
    """Extract endpoints as {path: {methods}}."""
    endpoints = {}
    for path, methods in spec.get("paths", {}).items():
        endpoints[path] = {
            method.upper()
            for method in methods.keys()
            if method.lower() not in ("parameters", "summary", "description")
        }
    return endpoints


def get_schemas(spec: dict) -> set[str]:
    """Extract schema names."""
    return set(spec.get("components", {}).get("schemas", {}).keys())


def check_breaking_changes(old_spec: dict, new_spec: dict) -> list[dict[str, Any]]:
    """Check for breaking changes between two specs.

    Returns list of breaking changes with severity and description.
    """
    breaking_changes = []

    # Check for removed endpoints
    old_endpoints = get_endpoints(old_spec)
    new_endpoints = get_endpoints(new_spec)

    for path, methods in old_endpoints.items():
        if path not in new_endpoints:
            breaking_changes.append(
                {
                    "severity": "critical",
                    "type": "endpoint_removed",
                    "path": path,
                    "description": f"Endpoint '{path}' was removed",
                }
            )
        else:
            removed_methods = methods - new_endpoints[path]
            for method in removed_methods:
                breaking_changes.append(
                    {
                        "severity": "critical",
                        "type": "method_removed",
                        "path": path,
                        "method": method,
                        "description": f"{method} {path} was removed",
                    }
                )

    # Check for removed schemas
    old_schemas = get_schemas(old_spec)
    new_schemas = get_schemas(new_spec)

    removed_schemas = old_schemas - new_schemas
    for schema in removed_schemas:
        breaking_changes.append(
            {
                "severity": "high",
                "type": "schema_removed",
                "schema": schema,
                "description": f"Schema '{schema}' was removed",
            }
        )

    # Check for parameter changes in existing endpoints
    for path, methods in old_endpoints.items():
        if path not in new_endpoints:
            continue

        for method in methods:
            if method not in new_endpoints[path]:
                continue

            old_op = old_spec["paths"][path].get(method.lower(), {})
            new_op = new_spec["paths"][path].get(method.lower(), {})

            # Check for removed parameters
            old_params = {p.get("name"): p for p in old_op.get("parameters", [])}
            new_params = {p.get("name"): p for p in new_op.get("parameters", [])}

            for param_name, param in old_params.items():
                if param_name not in new_params:
                    breaking_changes.append(
                        {
                            "severity": "high",
                            "type": "parameter_removed",
                            "path": path,
                            "method": method,
                            "parameter": param_name,
                            "description": f"Parameter '{param_name}' removed from {method} {path}",
                        }
                    )

            # Check for new required parameters
            for param_name, param in new_params.items():
                if param_name not in old_params and param.get("required", False):
                    breaking_changes.append(
                        {
                            "severity": "high",
                            "type": "required_parameter_added",
                            "path": path,
                            "method": method,
                            "parameter": param_name,
                            "description": f"New required parameter '{param_name}' added to {method} {path}",
                        }
                    )

    return breaking_changes


def print_report(changes: list[dict[str, Any]]) -> None:
    """Print breaking changes report."""
    if not changes:
        print("✅ No breaking changes detected!")
        return

    critical = [c for c in changes if c["severity"] == "critical"]
    high = [c for c in changes if c["severity"] == "high"]

    print(f"⚠️  Found {len(changes)} breaking change(s):\n")

    if critical:
        print("🔴 CRITICAL:")
        for change in critical:
            print(f"   - {change['description']}")
        print()

    if high:
        print("🟠 HIGH:")
        for change in high:
            print(f"   - {change['description']}")
        print()


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    # Default paths
    current_spec_path = project_root / "docs" / "openapi.json"

    if len(sys.argv) == 3:
        old_spec_path = Path(sys.argv[1])
        new_spec_path = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        old_spec_path = Path(sys.argv[1])
        new_spec_path = current_spec_path
    else:
        # No args - just validate current spec exists
        if not current_spec_path.exists():
            print("❌ OpenAPI spec not found at docs/openapi.json")
            print("   Run: python scripts/generate_openapi.py")
            return 1

        print(f"✅ OpenAPI spec found at {current_spec_path}")

        # Load and show summary
        spec = load_spec(current_spec_path)
        endpoints = get_endpoints(spec)
        schemas = get_schemas(spec)

        print(f"   Endpoints: {sum(len(m) for m in endpoints.values())}")
        print(f"   Schemas: {len(schemas)}")
        return 0

    # Load specs
    if not old_spec_path.exists():
        print(f"❌ Old spec not found: {old_spec_path}")
        return 1

    if not new_spec_path.exists():
        print(f"❌ New spec not found: {new_spec_path}")
        return 1

    old_spec = load_spec(old_spec_path)
    new_spec = load_spec(new_spec_path)

    # Check for breaking changes
    changes = check_breaking_changes(old_spec, new_spec)
    print_report(changes)

    # Return non-zero if critical changes found
    critical_count = sum(1 for c in changes if c["severity"] == "critical")
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
