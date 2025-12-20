"""Duplicate detection service for statement imports.

This module provides fuzzy matching to detect potential duplicates
between detected subscriptions and existing user subscriptions.

Features:
- Fuzzy name matching using various algorithms
- Amount similarity checking
- Frequency alignment verification
- Confidence scoring for matches
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

from src.models.subscription import Subscription
from src.services.statement_ai_service import DetectedPattern

logger = logging.getLogger(__name__)


@dataclass
class DuplicateMatch:
    """A potential duplicate match between detected and existing subscription."""

    detected_pattern: DetectedPattern
    existing_subscription: Subscription
    similarity_score: float  # 0.0 to 1.0
    match_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "detected_name": self.detected_pattern.normalized_name,
            "detected_amount": float(self.detected_pattern.amount),
            "existing_id": str(self.existing_subscription.id),
            "existing_name": self.existing_subscription.name,
            "existing_amount": float(self.existing_subscription.amount),
            "similarity_score": self.similarity_score,
            "match_reasons": self.match_reasons,
        }


class DuplicateDetector:
    """Service for detecting duplicate subscriptions.

    Uses multiple matching strategies to find potential duplicates
    between newly detected patterns and existing subscriptions.
    """

    # Similarity thresholds
    NAME_SIMILARITY_THRESHOLD = 0.7
    AMOUNT_SIMILARITY_THRESHOLD = 0.1  # 10% variance allowed
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.65

    # Frequency mappings for normalization
    FREQUENCY_MAP = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,
        "quarterly": 90,
        "yearly": 365,
        "annually": 365,
        "irregular": None,
    }

    def __init__(self) -> None:
        """Initialize the duplicate detector."""
        pass

    def find_duplicates(
        self,
        patterns: list[DetectedPattern],
        existing_subscriptions: list[Subscription],
        min_similarity: float = 0.6,
    ) -> list[DuplicateMatch]:
        """Find potential duplicates for detected patterns.

        Args:
            patterns: List of detected patterns from statement
            existing_subscriptions: User's existing subscriptions
            min_similarity: Minimum similarity score to consider a match

        Returns:
            List of duplicate matches sorted by similarity
        """
        matches: list[DuplicateMatch] = []

        for pattern in patterns:
            for subscription in existing_subscriptions:
                match = self._check_match(pattern, subscription)
                if match and match.similarity_score >= min_similarity:
                    matches.append(match)

        # Sort by similarity score (highest first)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        return matches

    def find_best_match(
        self,
        pattern: DetectedPattern,
        existing_subscriptions: list[Subscription],
        min_similarity: float = 0.6,
    ) -> DuplicateMatch | None:
        """Find the best matching existing subscription for a pattern.

        Args:
            pattern: Detected pattern to match
            existing_subscriptions: User's existing subscriptions
            min_similarity: Minimum similarity score to consider a match

        Returns:
            Best matching DuplicateMatch or None if no match found
        """
        best_match: DuplicateMatch | None = None

        for subscription in existing_subscriptions:
            match = self._check_match(pattern, subscription)
            if match and match.similarity_score >= min_similarity:
                if best_match is None or match.similarity_score > best_match.similarity_score:
                    best_match = match

        return best_match

    def _check_match(
        self,
        pattern: DetectedPattern,
        subscription: Subscription,
    ) -> DuplicateMatch | None:
        """Check if a pattern matches an existing subscription.

        Args:
            pattern: Detected pattern
            subscription: Existing subscription

        Returns:
            DuplicateMatch if there's a match, None otherwise
        """
        match_reasons: list[str] = []
        scores: list[tuple[float, float]] = []  # (score, weight)

        # 1. Name similarity (weighted: 0.4)
        name_score = self._calculate_name_similarity(
            pattern.normalized_name,
            subscription.name,
        )
        if name_score >= self.NAME_SIMILARITY_THRESHOLD:
            match_reasons.append(f"Name match: {name_score:.0%}")
            scores.append((name_score, 0.4))
        elif name_score < 0.4:
            # Names too different, skip this match
            return None

        # 2. Amount similarity (weighted: 0.35)
        amount_score = self._calculate_amount_similarity(
            pattern.amount,
            subscription.amount,
        )
        if amount_score >= (1 - self.AMOUNT_SIMILARITY_THRESHOLD):
            match_reasons.append(f"Amount match: {amount_score:.0%}")
            scores.append((amount_score, 0.35))
        else:
            scores.append((amount_score * 0.5, 0.35))  # Penalize amount mismatch

        # 3. Frequency alignment (weighted: 0.25)
        freq_score = self._calculate_frequency_similarity(
            pattern.frequency.value,
            subscription.frequency.value if subscription.frequency else "monthly",
        )
        if freq_score > 0.8:
            match_reasons.append("Frequency match")
            scores.append((freq_score, 0.25))
        else:
            scores.append((freq_score * 0.7, 0.25))

        # Calculate weighted average
        if not scores:
            return None

        total_weight = sum(weight for _, weight in scores)
        similarity_score = sum(score * weight for score, weight in scores) / total_weight

        if similarity_score < 0.4:
            return None

        return DuplicateMatch(
            detected_pattern=pattern,
            existing_subscription=subscription,
            similarity_score=round(similarity_score, 2),
            match_reasons=match_reasons,
        )

    def _calculate_name_similarity(
        self,
        name1: str,
        name2: str,
    ) -> float:
        """Calculate similarity between two names.

        Uses multiple strategies:
        1. Exact match (after normalization)
        2. Sequence matching
        3. Token overlap
        4. Common word matching

        Args:
            name1: First name (normalized pattern name)
            name2: Second name (existing subscription name)

        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Normalize both names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)

        if not norm1 or not norm2:
            return 0.0

        # Exact match
        if norm1 == norm2:
            return 1.0

        # Substring match
        if norm1 in norm2 or norm2 in norm1:
            return 0.9

        # Sequence matching
        sequence_score = SequenceMatcher(None, norm1, norm2).ratio()

        # Token overlap
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())
        if tokens1 and tokens2:
            common_tokens = tokens1 & tokens2
            token_score = len(common_tokens) / max(len(tokens1), len(tokens2))
        else:
            token_score = 0.0

        # Take the best score
        return max(sequence_score, token_score)

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison.

        Args:
            name: Original name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        # Lowercase
        name = name.lower().strip()

        # Remove common suffixes
        suffixes_to_remove = [
            r"\s*(ltd|limited|inc|llc|plc|corp|corporation)\.?$",
            r"\s*subscription$",
            r"\s*monthly$",
            r"\s*premium$",
        ]
        for suffix in suffixes_to_remove:
            name = re.sub(suffix, "", name, flags=re.IGNORECASE)

        # Remove special characters except spaces
        name = re.sub(r"[^\w\s]", "", name)

        # Normalize whitespace
        name = " ".join(name.split())

        return name.strip()

    def _calculate_amount_similarity(
        self,
        amount1: Decimal,
        amount2: Decimal,
    ) -> float:
        """Calculate similarity between two amounts.

        Args:
            amount1: First amount (detected)
            amount2: Second amount (existing)

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if amount1 == amount2:
            return 1.0

        # Use absolute values
        a1 = abs(float(amount1))
        a2 = abs(float(amount2))

        if a1 == 0 or a2 == 0:
            return 0.0

        # Calculate percentage difference
        diff = abs(a1 - a2)
        avg = (a1 + a2) / 2
        percentage_diff = diff / avg

        # Convert to similarity (0% diff = 1.0, 100% diff = 0.0)
        similarity = max(0.0, 1.0 - percentage_diff)

        return similarity

    def _calculate_frequency_similarity(
        self,
        freq1: str,
        freq2: str,
    ) -> float:
        """Calculate similarity between two frequencies.

        Args:
            freq1: First frequency (detected)
            freq2: Second frequency (existing)

        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Normalize frequency names
        freq1 = freq1.lower().strip()
        freq2 = freq2.lower().strip()

        if freq1 == freq2:
            return 1.0

        # Get day equivalents
        days1 = self.FREQUENCY_MAP.get(freq1)
        days2 = self.FREQUENCY_MAP.get(freq2)

        if days1 is None or days2 is None:
            # If one is irregular, low similarity
            return 0.3 if (days1 is None) != (days2 is None) else 0.5

        # Calculate similarity based on day difference
        diff = abs(days1 - days2)
        max_days = max(days1, days2)

        if diff == 0:
            return 1.0
        elif diff <= 3:
            return 0.9  # Close enough (e.g., 28 vs 30 days)
        elif diff <= 7:
            return 0.7
        else:
            return max(0.0, 1.0 - (diff / max_days))


def get_duplicate_detector() -> DuplicateDetector:
    """Factory function for duplicate detector.

    Returns:
        Configured DuplicateDetector instance
    """
    return DuplicateDetector()
