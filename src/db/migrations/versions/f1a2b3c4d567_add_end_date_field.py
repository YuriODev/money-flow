"""add_end_date_field

Revision ID: f1a2b3c4d567
Revises: e9c0f5g6b234
Create Date: 2025-12-07

This migration originally added the end_date field to the subscriptions table.
The end_date is optional and used for:
- Fixed-term subscriptions
- Installment plans with a defined end
- One-time payments
- Council tax years or seasonal subscriptions

NOTE: end_date is now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d567"
down_revision: str | Sequence[str] | None = "e9c0f5g6b234"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add end_date column to subscriptions table.

    No-op: end_date now created in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Remove end_date column from subscriptions table.

    No-op: Column is dropped in 0001_initial_schema downgrade.
    """
    pass
