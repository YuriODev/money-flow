"""Bank profile service for managing bank statement parsing configurations.

This service provides:
- CRUD operations for bank profiles
- Bank detection from file content
- Seeding from JSON data file
- Caching of frequently used bank profiles
"""

from __future__ import annotations

import fnmatch
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bank_profile import BankProfile

logger = logging.getLogger(__name__)


class BankService:
    """Service for managing bank profiles and statement parsing configurations."""

    def __init__(self, db: AsyncSession, user_id: str | None = None) -> None:
        """Initialize bank service.

        Args:
            db: Async database session
            user_id: Optional user ID (for future user-specific banks)
        """
        self.db = db
        self.user_id = user_id

    async def get_all(
        self,
        country_code: str | None = None,
        verified_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BankProfile]:
        """Get all bank profiles with optional filtering.

        Args:
            country_code: Filter by country code (e.g., "GB", "US")
            verified_only: Only return admin-verified profiles
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of bank profiles
        """
        query = select(BankProfile)

        if country_code:
            query = query.where(BankProfile.country_code == country_code.upper())

        if verified_only:
            query = query.where(BankProfile.is_verified.is_(True))

        query = query.order_by(BankProfile.usage_count.desc(), BankProfile.name)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> BankProfile | None:
        """Get a bank profile by slug.

        Args:
            slug: Bank slug (e.g., "monzo", "chase")

        Returns:
            Bank profile or None
        """
        query = select(BankProfile).where(BankProfile.slug == slug.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, bank_id: str) -> BankProfile | None:
        """Get a bank profile by ID.

        Args:
            bank_id: Bank UUID

        Returns:
            Bank profile or None
        """
        try:
            bank_uuid = uuid.UUID(bank_id)
        except ValueError:
            return None

        query = select(BankProfile).where(BankProfile.id == bank_uuid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_country(self, country_code: str) -> list[BankProfile]:
        """Get all banks for a specific country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            List of bank profiles for that country
        """
        return await self.get_all(country_code=country_code)

    async def search(self, query: str, limit: int = 20) -> list[BankProfile]:
        """Search banks by name or slug.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching bank profiles
        """
        search_pattern = f"%{query.lower()}%"
        stmt = (
            select(BankProfile)
            .where(
                (func.lower(BankProfile.name).like(search_pattern))
                | (BankProfile.slug.like(search_pattern))
            )
            .order_by(BankProfile.usage_count.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        name: str,
        slug: str,
        country_code: str,
        currency: str = "GBP",
        csv_mapping: dict | None = None,
        detection_patterns: dict | None = None,
        logo_url: str | None = None,
        website: str | None = None,
        is_verified: bool = False,
    ) -> BankProfile:
        """Create a new bank profile.

        Args:
            name: Human-readable bank name
            slug: URL-friendly identifier
            country_code: ISO country code
            currency: Default currency
            csv_mapping: Column mappings for CSV parsing
            detection_patterns: Patterns for auto-detection
            logo_url: Bank logo URL
            website: Bank website
            is_verified: Admin verified flag

        Returns:
            Created bank profile
        """
        bank = BankProfile(
            name=name,
            slug=slug.lower(),
            country_code=country_code.upper(),
            currency=currency.upper(),
            csv_mapping=csv_mapping or {},
            detection_patterns=detection_patterns or {},
            pdf_patterns={},
            logo_url=logo_url,
            website=website,
            is_verified=is_verified,
        )

        self.db.add(bank)
        await self.db.commit()
        await self.db.refresh(bank)

        logger.info(f"Created bank profile: {bank.slug}")
        return bank

    async def update(
        self,
        bank: BankProfile,
        **kwargs: Any,
    ) -> BankProfile:
        """Update a bank profile.

        Args:
            bank: Bank profile to update
            **kwargs: Fields to update

        Returns:
            Updated bank profile
        """
        allowed_fields = {
            "name",
            "country_code",
            "currency",
            "csv_mapping",
            "pdf_patterns",
            "detection_patterns",
            "logo_url",
            "website",
            "is_verified",
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(bank, key, value)

        await self.db.commit()
        await self.db.refresh(bank)

        logger.info(f"Updated bank profile: {bank.slug}")
        return bank

    async def delete(self, bank: BankProfile) -> None:
        """Delete a bank profile.

        Args:
            bank: Bank profile to delete
        """
        slug = bank.slug
        await self.db.delete(bank)
        await self.db.commit()
        logger.info(f"Deleted bank profile: {slug}")

    async def increment_usage(self, bank: BankProfile) -> None:
        """Increment the usage count for a bank profile.

        Args:
            bank: Bank profile to update
        """
        bank.increment_usage()
        await self.db.commit()

    async def detect_bank(
        self,
        filename: str | None = None,
        headers: list[str] | None = None,
        content: str | None = None,
    ) -> BankProfile | None:
        """Auto-detect bank from file characteristics.

        Args:
            filename: Original filename
            headers: CSV header row
            content: File content sample

        Returns:
            Detected bank profile or None
        """
        banks = await self.get_all()

        for bank in banks:
            patterns = bank.detection_patterns

            # Check filename patterns
            if filename and patterns.get("filename_patterns"):
                for pattern in patterns["filename_patterns"]:
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        logger.info(f"Detected bank {bank.slug} from filename: {filename}")
                        return bank

            # Check header keywords
            if headers and patterns.get("header_keywords"):
                header_text = " ".join(headers).lower()
                for keyword in patterns["header_keywords"]:
                    if keyword.lower() in header_text:
                        logger.info(f"Detected bank {bank.slug} from headers: {keyword}")
                        return bank

            # Check content patterns
            if content and patterns.get("content_patterns"):
                for pattern in patterns["content_patterns"]:
                    try:
                        if re.search(pattern, content, re.IGNORECASE):
                            logger.info(f"Detected bank {bank.slug} from content: {pattern}")
                            return bank
                    except re.error:
                        # Invalid regex, try as literal string
                        if pattern.lower() in content.lower():
                            return bank

        return None

    async def get_countries(self) -> list[dict[str, Any]]:
        """Get list of countries with bank counts.

        Returns:
            List of dicts with country_code and count
        """
        query = (
            select(BankProfile.country_code, func.count(BankProfile.id).label("count"))
            .group_by(BankProfile.country_code)
            .order_by(func.count(BankProfile.id).desc())
        )
        result = await self.db.execute(query)
        return [{"country_code": row.country_code, "count": row.count} for row in result]

    async def count(self, country_code: str | None = None) -> int:
        """Count bank profiles.

        Args:
            country_code: Optional country filter

        Returns:
            Number of bank profiles
        """
        query = select(func.count(BankProfile.id))
        if country_code:
            query = query.where(BankProfile.country_code == country_code.upper())
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def seed_from_json(self, json_path: str | Path | None = None) -> int:
        """Seed bank profiles from JSON file.

        Args:
            json_path: Path to JSON file (defaults to data/bank_profiles.json)

        Returns:
            Number of banks seeded
        """
        if json_path is None:
            # Check for DATA_DIR env var (Docker) or use relative path
            data_dir = os.environ.get("DATA_DIR", None)
            if data_dir:
                json_path = Path(data_dir) / "bank_profiles.json"
            else:
                # Try /app/data (Docker) then project root
                docker_path = Path("/app/data/bank_profiles.json")
                if docker_path.exists():
                    json_path = docker_path
                else:
                    json_path = Path(__file__).parent.parent.parent / "data" / "bank_profiles.json"
        else:
            json_path = Path(json_path)

        if not json_path.exists():
            logger.warning(f"Bank profiles JSON not found: {json_path}")
            return 0

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        banks = data.get("banks", [])
        seeded = 0

        for bank_data in banks:
            # Check if bank already exists
            existing = await self.get_by_slug(bank_data["slug"])
            if existing:
                logger.debug(f"Bank already exists: {bank_data['slug']}")
                continue

            # Create new bank
            await self.create(
                name=bank_data["name"],
                slug=bank_data["slug"],
                country_code=bank_data["country_code"],
                currency=bank_data.get("currency", "GBP"),
                csv_mapping=bank_data.get("csv_mapping", {}),
                detection_patterns=bank_data.get("detection_patterns", {}),
                logo_url=bank_data.get("logo_url"),
                website=bank_data.get("website"),
                is_verified=bank_data.get("is_verified", False),
            )
            seeded += 1

        logger.info(f"Seeded {seeded} bank profiles from {json_path}")
        return seeded


async def get_bank_service(db: AsyncSession) -> BankService:
    """Factory function for bank service.

    Args:
        db: Database session

    Returns:
        Configured bank service
    """
    return BankService(db)
