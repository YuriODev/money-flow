"""add_one_time_payment_type

Revision ID: e9c0f5g6b234
Revises: d8b9e4f5a123
Create Date: 2025-12-06

This migration adds the ONE_TIME payment type to the paymenttype enum.
One-time payments are for non-recurring expenses like legal fees, one-off services.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9c0f5g6b234"
down_revision: str | Sequence[str] | None = "d8b9e4f5a123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ONE_TIME to paymenttype enum."""
    op.execute("ALTER TYPE paymenttype ADD VALUE IF NOT EXISTS 'ONE_TIME';")


def downgrade() -> None:
    """Remove ONE_TIME from paymenttype enum.

    Note: PostgreSQL does not support removing enum values directly.
    A full enum recreation would be needed, but this is rarely necessary.
    """
    pass
