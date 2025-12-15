"""add_funding_card_id_to_payment_cards

Revision ID: 8288763654e3
Revises: g2b3c4d5e678
Create Date: 2025-12-07 17:42:08.700695

This migration originally added funding_card_id to payment_cards for card funding relationships.

NOTE: funding_card_id is now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "8288763654e3"
down_revision: str | Sequence[str] | None = "g2b3c4d5e678"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    No-op: funding_card_id now created in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Downgrade schema.

    No-op: Column is dropped in 0001_initial_schema downgrade.
    """
    pass
