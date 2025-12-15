"""Initial schema - create base tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-11-28 00:00:00.000000

This is the initial migration that creates the base tables:
- subscriptions: Main table for tracking recurring payments
- payment_cards: Payment methods for subscriptions
- users: User accounts for multi-tenant support

Note: This migration was created retroactively to fix CI which needs
proper Alembic migrations rather than relying on Base.metadata.create_all().
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table first (subscriptions references it)
    # Note: sa.Enum will auto-create the userrole type
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        # Profile fields
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        # Role and status
        # Note: SQLAlchemy uses enum NAMES (uppercase) by default, not values
        sa.Column(
            "role",
            sa.Enum("USER", "ADMIN", name="userrole", create_type=True),
            nullable=False,
            server_default="USER",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        # User preferences
        sa.Column("preferences", sa.Text(), nullable=True),
        # Security tracking
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_role", "users", ["role"])

    # Create payment_cards table (subscriptions references it)
    op.create_table(
        "payment_cards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "card_type",
            sa.Enum("debit", "credit", "prepaid", "bank_account", name="cardtype"),
            nullable=False,
        ),
        sa.Column("last_four", sa.String(length=4), nullable=True),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="GBP"),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#3B82F6"),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funding_card_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["funding_card_id"], ["payment_cards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_cards_name", "payment_cards", ["name"])

    # Create subscriptions table with all current fields
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="GBP"),
        sa.Column(
            "frequency",
            sa.Enum(
                "daily",
                "weekly",
                "biweekly",
                "monthly",
                "quarterly",
                "yearly",
                "custom",
                name="frequency",
            ),
            nullable=False,
            server_default="monthly",
        ),
        sa.Column("frequency_interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("next_payment_date", sa.Date(), nullable=False),
        sa.Column("last_payment_date", sa.Date(), nullable=True),
        sa.Column(
            "payment_type",
            sa.Enum(
                "subscription",
                "housing",
                "utility",
                "professional_service",
                "insurance",
                "debt",
                "savings",
                "transfer",
                "one_time",
                name="paymenttype",
            ),
            nullable=False,
            server_default="subscription",
        ),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        # Payment tracking fields
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("reminder_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#3B82F6"),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"),
        # Installment fields
        sa.Column("is_installment", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_installments", sa.Integer(), nullable=True),
        sa.Column("completed_installments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("installment_start_date", sa.Date(), nullable=True),
        sa.Column("installment_end_date", sa.Date(), nullable=True),
        # Debt fields
        sa.Column("total_owed", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("remaining_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("creditor", sa.String(length=255), nullable=True),
        # Savings/Transfer fields
        sa.Column("target_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("current_saved", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("recipient", sa.String(length=255), nullable=True),
        # Foreign keys
        sa.Column("card_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["card_id"], ["payment_cards.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_name", "subscriptions", ["name"])
    op.create_index("ix_subscriptions_payment_type", "subscriptions", ["payment_type"])
    op.create_index("ix_subscriptions_card_id", "subscriptions", ["card_id"])
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    # Create payment_history table
    op.create_table(
        "payment_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="GBP"),
        sa.Column(
            "status",
            sa.Enum("completed", "pending", "failed", "cancelled", name="paymentstatus"),
            nullable=False,
            server_default="completed",
        ),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("installment_number", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_history_subscription_id", "payment_history", ["subscription_id"])
    op.create_index("ix_payment_history_payment_date", "payment_history", ["payment_date"])
    op.create_index("ix_payment_history_status", "payment_history", ["status"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("payment_history")
    op.drop_table("subscriptions")
    op.drop_table("payment_cards")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymenttype")
    op.execute("DROP TYPE IF EXISTS frequency")
    op.execute("DROP TYPE IF EXISTS cardtype")
    op.execute("DROP TYPE IF EXISTS userrole")
