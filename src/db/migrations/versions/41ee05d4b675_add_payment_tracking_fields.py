"""add_payment_tracking_fields

Revision ID: 41ee05d4b675
Revises: 0001_initial_schema
Create Date: 2025-11-29 02:29:05.487746

This migration originally added:
- Payment tracking fields to subscriptions (last_payment_date, reminder_days, etc.)
- Installment plan fields (is_installment, total_installments, etc.)
- Visual fields for UI (icon_url, color)
- New payment_history table for tracking individual payments

NOTE: These fields are now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "41ee05d4b675"
down_revision: str | Sequence[str] | None = "0001_initial_schema"
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
