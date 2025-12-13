#!/usr/bin/env python3
"""Data migration script to reclassify subscriptions to proper Money Flow payment types.

This script updates existing subscriptions from the default 'SUBSCRIPTION' type
to their appropriate payment types based on name and category patterns.

Usage:
    # Dry run (preview changes without applying)
    python scripts/migrate_payment_types.py --dry-run

    # Apply changes
    python scripts/migrate_payment_types.py

    # Via Docker
    docker exec subscription-backend python scripts/migrate_payment_types.py --dry-run
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Classification rules based on name patterns and categories
RECLASSIFICATION_RULES = {
    # INSURANCE - Health and device protection
    "INSURANCE": {
        "name_patterns": [
            "bupa",
            "health insurance",
            "applecare",
            "ac+",  # AppleCare+
            "insurance",
        ],
        "category_patterns": ["insurance"],
    },
    # UTILITY - Internet, phone, utilities
    "UTILITY": {
        "name_patterns": [
            "virgin media",
            "vodafone",
            "edf",
            "thames water",
            "council tax",
            "electric",
            "gas",
            "water",
            "broadband",
        ],
        "category_patterns": ["utilities"],
    },
    # PROFESSIONAL_SERVICE - Health services, coaching, training
    "PROFESSIONAL_SERVICE": {
        "name_patterns": [
            "therapy",
            "therapist",
            "gym session",
            "coach",
            "trainer",
            "tutor",
            "lesson",
        ],
        "category_patterns": [],  # Health category items need individual review
    },
}

# Specific item overrides (highest priority)
SPECIFIC_OVERRIDES = {
    # Insurance items
    "Bupa Health Insurance": "INSURANCE",
    "Applecare+ Ipad": "INSURANCE",
    "Applecare+ Iphone": "INSURANCE",
    "Ac+ For Mac Mini (M4)": "INSURANCE",
    # Utilities
    "Virgin Media": "UTILITY",
    "Vodafone": "UTILITY",
    # Professional services
    "Therapy Session": "PROFESSIONAL_SERVICE",
    "Gym Sessions": "PROFESSIONAL_SERVICE",
}


def classify_subscription(name: str, category: str | None) -> str | None:
    """Determine the new payment type for a subscription.

    Args:
        name: Subscription name.
        category: Current category.

    Returns:
        New PaymentType string or None if no change needed.
    """
    name_lower = name.lower()
    category_lower = (category or "").lower()

    # Check specific overrides first
    if name in SPECIFIC_OVERRIDES:
        return SPECIFIC_OVERRIDES[name]

    # Check classification rules
    for payment_type, rules in RECLASSIFICATION_RULES.items():
        # Check name patterns
        for pattern in rules["name_patterns"]:
            if pattern in name_lower:
                return payment_type

        # Check category patterns
        for pattern in rules["category_patterns"]:
            if pattern in category_lower:
                return payment_type

    # No change needed
    return None


async def migrate_payment_types(dry_run: bool = True) -> None:
    """Run the payment type migration.

    Args:
        dry_run: If True, only preview changes without applying.
    """
    import os

    # Connect to database - use environment variable or default to Docker internal network
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://subscriptions:localdev@db:5432/subscriptions"
    )
    engine = create_async_engine(database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # Fetch all subscriptions
        result = await session.execute(
            text("SELECT id, name, payment_type, category FROM subscriptions ORDER BY name")
        )
        subscriptions = result.fetchall()

        print(f"\n{'='*70}")
        print(f"Money Flow Payment Type Migration")
        print(f"{'='*70}")
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE (applying changes)'}")
        print(f"Total subscriptions: {len(subscriptions)}")
        print(f"{'='*70}\n")

        changes = []
        no_changes = []

        for sub_id, name, current_type, category in subscriptions:
            new_type = classify_subscription(name, category)

            if new_type and new_type != current_type:
                changes.append({
                    "id": sub_id,
                    "name": name,
                    "from": current_type,
                    "to": new_type,
                    "category": category,
                })
            else:
                no_changes.append(name)

        # Print changes
        if changes:
            print("📝 CHANGES TO BE APPLIED:")
            print("-" * 70)
            for change in changes:
                print(f"  {change['name']}")
                print(f"    Category: {change['category'] or 'None'}")
                print(f"    {change['from']} → {change['to']}")
                print()

            if not dry_run:
                print("\n🔄 Applying changes...")
                for change in changes:
                    await session.execute(
                        text("UPDATE subscriptions SET payment_type = :new_type WHERE id = :id"),
                        {"new_type": change["to"], "id": change["id"]},
                    )
                await session.commit()
                print("✅ Changes applied successfully!")
            else:
                print("\n⚠️  DRY RUN - No changes applied.")
                print("    Run without --dry-run to apply these changes.")
        else:
            print("✅ No changes needed - all subscriptions are correctly classified.")

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"  Total subscriptions: {len(subscriptions)}")
        print(f"  To be reclassified:  {len(changes)}")
        print(f"  Already correct:     {len(no_changes)}")

        if changes:
            print(f"\nReclassification breakdown:")
            by_type = {}
            for change in changes:
                to_type = change["to"]
                by_type[to_type] = by_type.get(to_type, 0) + 1
            for ptype, count in sorted(by_type.items()):
                print(f"  → {ptype}: {count} item(s)")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate subscription payment types to Money Flow classifications"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    args = parser.parse_args()

    asyncio.run(migrate_payment_types(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
