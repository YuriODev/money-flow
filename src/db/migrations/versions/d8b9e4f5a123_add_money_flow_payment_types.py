"""add_money_flow_payment_types

Revision ID: d8b9e4f5a123
Revises: c7a8f3d2e591
Create Date: 2025-12-01

This migration originally added Money Flow support to the subscriptions table:
- payment_type: Top-level classification (subscription, debt, savings, etc.)
- Debt-specific fields: total_owed, remaining_balance, creditor
- Savings-specific fields: target_amount, current_saved, recipient

NOTE: These fields are now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "d8b9e4f5a123"
down_revision: str | Sequence[str] | None = "c7a8f3d2e591"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    No-op: Fields now created in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Downgrade schema.

    No-op: Fields are dropped in 0001_initial_schema downgrade.
    """
    pass
