"""add_payment_tracking_fields

Revision ID: 41ee05d4b675
Revises:
Create Date: 2025-11-29 02:29:05.487746

This migration adds:
- Payment tracking fields to subscriptions (last_payment_date, reminder_days, etc.)
- Installment plan fields (is_installment, total_installments, etc.)
- Visual fields for UI (icon_url, color)
- New payment_history table for tracking individual payments
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "41ee05d4b675"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Adds payment tracking and installment fields to subscriptions table,
    and creates the payment_history table.
    """
    # Add new columns to subscriptions table with server defaults for existing rows
    op.add_column("subscriptions", sa.Column("last_payment_date", sa.Date(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("payment_method", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("reminder_days", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column("subscriptions", sa.Column("icon_url", sa.String(length=500), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#3B82F6"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("is_installment", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("subscriptions", sa.Column("total_installments", sa.Integer(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("completed_installments", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("subscriptions", sa.Column("installment_start_date", sa.Date(), nullable=True))
    op.add_column("subscriptions", sa.Column("installment_end_date", sa.Date(), nullable=True))

    # Create payment_history table
    op.create_table(
        "payment_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("installment_number", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on subscription_id for faster lookups
    op.create_index(
        "ix_payment_history_subscription_id",
        "payment_history",
        ["subscription_id"],
    )


def downgrade() -> None:
    """Downgrade schema.

    Removes payment tracking fields and payment_history table.
    """
    # Drop payment_history table
    op.drop_index("ix_payment_history_subscription_id", table_name="payment_history")
    op.drop_table("payment_history")

    # Remove columns from subscriptions table
    op.drop_column("subscriptions", "installment_end_date")
    op.drop_column("subscriptions", "installment_start_date")
    op.drop_column("subscriptions", "completed_installments")
    op.drop_column("subscriptions", "total_installments")
    op.drop_column("subscriptions", "is_installment")
    op.drop_column("subscriptions", "auto_renew")
    op.drop_column("subscriptions", "color")
    op.drop_column("subscriptions", "icon_url")
    op.drop_column("subscriptions", "reminder_days")
    op.drop_column("subscriptions", "payment_method")
    op.drop_column("subscriptions", "last_payment_date")
