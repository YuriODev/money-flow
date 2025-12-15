"""add_one_time_payment_type

Revision ID: e9c0f5g6b234
Revises: d8b9e4f5a123
Create Date: 2025-12-06

This migration originally added the ONE_TIME payment type to the paymenttype enum.
One-time payments are for non-recurring expenses like legal fees, one-off services.

NOTE: ONE_TIME is now included in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e9c0f5g6b234"
down_revision: str | Sequence[str] | None = "d8b9e4f5a123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ONE_TIME to paymenttype enum.

    No-op: ONE_TIME now included in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Remove ONE_TIME from paymenttype enum.

    No-op: Enum is dropped in 0001_initial_schema downgrade.
    """
    pass
