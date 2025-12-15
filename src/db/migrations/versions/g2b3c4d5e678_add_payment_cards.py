"""add_payment_cards

Revision ID: g2b3c4d5e678
Revises: f1a2b3c4d567
Create Date: 2025-12-07

This migration originally added the payment_cards table and links subscriptions to cards.
Allows tracking which card pays for each subscription and calculating
required balances per card.

NOTE: payment_cards and card_id are now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "g2b3c4d5e678"
down_revision: str | Sequence[str] | None = "f1a2b3c4d567"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create payment_cards table and add card_id to subscriptions.

    No-op: These are now created in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Remove payment_cards table and card_id from subscriptions.

    No-op: These are dropped in 0001_initial_schema downgrade.
    """
    pass
