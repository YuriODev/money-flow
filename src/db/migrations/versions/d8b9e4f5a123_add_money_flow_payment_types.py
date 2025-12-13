"""add_money_flow_payment_types

Revision ID: d8b9e4f5a123
Revises: c7a8f3d2e591
Create Date: 2025-12-01

This migration adds Money Flow support to the subscriptions table:
- payment_type: Top-level classification (subscription, debt, savings, etc.)
- Debt-specific fields: total_owed, remaining_balance, creditor
- Savings-specific fields: target_amount, current_saved, recipient
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8b9e4f5a123"
down_revision: str | Sequence[str] | None = "c7a8f3d2e591"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Adds Money Flow payment type classification and related fields.
    All existing subscriptions default to payment_type='subscription'.
    """
    # Create the payment_type enum type using raw SQL
    # NOTE: SQLAlchemy uses uppercase enum member NAMES (not values) for PostgreSQL enums
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymenttype') THEN
                CREATE TYPE paymenttype AS ENUM (
                    'SUBSCRIPTION',
                    'HOUSING',
                    'UTILITY',
                    'PROFESSIONAL_SERVICE',
                    'INSURANCE',
                    'DEBT',
                    'SAVINGS',
                    'TRANSFER'
                );
            END IF;
        END$$;
        """
    )

    # Add payment_type column with default value for existing records
    op.execute(
        """
        ALTER TABLE subscriptions
        ADD COLUMN payment_type paymenttype NOT NULL DEFAULT 'SUBSCRIPTION';
        """
    )

    # Create index on payment_type for efficient filtering
    op.create_index(
        "ix_subscriptions_payment_type",
        "subscriptions",
        ["payment_type"],
    )

    # Add debt-specific fields
    op.add_column(
        "subscriptions",
        sa.Column("total_owed", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("remaining_balance", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("creditor", sa.String(length=255), nullable=True),
    )

    # Add savings-specific fields
    op.add_column(
        "subscriptions",
        sa.Column("target_amount", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("current_saved", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("recipient", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema.

    Removes Money Flow payment type and related fields.
    """
    # Drop savings-specific fields
    op.drop_column("subscriptions", "recipient")
    op.drop_column("subscriptions", "current_saved")
    op.drop_column("subscriptions", "target_amount")

    # Drop debt-specific fields
    op.drop_column("subscriptions", "creditor")
    op.drop_column("subscriptions", "remaining_balance")
    op.drop_column("subscriptions", "total_owed")

    # Drop payment_type column and index
    op.drop_index("ix_subscriptions_payment_type", table_name="subscriptions")
    op.drop_column("subscriptions", "payment_type")

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS paymenttype;")
