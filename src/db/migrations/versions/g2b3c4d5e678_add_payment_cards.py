"""add_payment_cards

Revision ID: g2b3c4d5e678
Revises: f1a2b3c4d567
Create Date: 2025-12-07

This migration adds the payment_cards table and links subscriptions to cards.
Allows tracking which card pays for each subscription and calculating
required balances per card.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g2b3c4d5e678"
down_revision: str | Sequence[str] | None = "f1a2b3c4d567"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create payment_cards table and add card_id to subscriptions."""
    # Create CardType enum using raw SQL with DO block for IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE cardtype AS ENUM ('debit', 'credit', 'prepaid', 'bank_account');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create payment_cards table using String for card_type column
    # and then alter to use the enum (to avoid SQLAlchemy auto-creating enum)
    op.create_table(
        "payment_cards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, index=True),
        sa.Column("card_type", sa.String(20), nullable=False, server_default="debit"),
        sa.Column("last_four", sa.String(4), nullable=True),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="GBP"),
        sa.Column("color", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Alter column to use the enum type
    op.execute(
        "ALTER TABLE payment_cards ALTER COLUMN card_type TYPE cardtype USING card_type::cardtype"
    )

    # Add card_id foreign key to subscriptions
    op.add_column(
        "subscriptions",
        sa.Column("card_id", sa.String(36), nullable=True),
    )
    op.create_index("ix_subscriptions_card_id", "subscriptions", ["card_id"])
    op.create_foreign_key(
        "fk_subscriptions_card_id",
        "subscriptions",
        "payment_cards",
        ["card_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove payment_cards table and card_id from subscriptions."""
    # Remove foreign key and column from subscriptions
    op.drop_constraint("fk_subscriptions_card_id", "subscriptions", type_="foreignkey")
    op.drop_index("ix_subscriptions_card_id", table_name="subscriptions")
    op.drop_column("subscriptions", "card_id")

    # Drop payment_cards table
    op.drop_table("payment_cards")

    # Drop CardType enum
    sa.Enum(name="cardtype").drop(op.get_bind(), checkfirst=True)
