"""add_end_date_field

Revision ID: f1a2b3c4d567
Revises: e9c0f5g6b234
Create Date: 2025-12-07

This migration adds the end_date field to the subscriptions table.
The end_date is optional and used for:
- Fixed-term subscriptions
- Installment plans with a defined end
- One-time payments
- Council tax years or seasonal subscriptions
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d567"
down_revision: str | Sequence[str] | None = "e9c0f5g6b234"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add end_date column to subscriptions table."""
    op.add_column(
        "subscriptions",
        sa.Column("end_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    """Remove end_date column from subscriptions table."""
    op.drop_column("subscriptions", "end_date")
