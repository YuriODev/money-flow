"""add_open_banking_tables

Revision ID: e631c2e23154
Revises: c3c81f458195
Create Date: 2025-12-28 19:04:32.247489

Sprint 5.7 - Open Banking Integration

This migration creates tables for:
- bank_connections: Open Banking connections to Plaid/TrueLayer
- bank_accounts: Individual bank accounts within connections
- bank_transactions: Imported transactions for recurring detection
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e631c2e23154"
down_revision: str | Sequence[str] | None = "c3c81f458195"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Open Banking tables."""
    # Create bank_connections table
    op.create_table(
        "bank_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.Enum("PLAID", "TRUELAYER", name="bankprovider"), nullable=False),
        sa.Column("institution_id", sa.String(length=100), nullable=False),
        sa.Column("institution_name", sa.String(length=255), nullable=False),
        sa.Column("institution_logo_url", sa.String(length=500), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("item_id", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACTIVE",
                "EXPIRED",
                "REVOKED",
                "ERROR",
                "DISCONNECTED",
                name="connectionstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "consent_status",
            sa.Enum(
                "PENDING", "AUTHORIZED", "REJECTED", "EXPIRED", "REVOKED", name="consentstatus"
            ),
            nullable=False,
        ),
        sa.Column("consent_expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("sync_cursor", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("accounts_count", sa.Integer(), nullable=False),
        sa.Column("is_auto_sync_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bank_connections_institution_id"),
        "bank_connections",
        ["institution_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_connections_item_id"), "bank_connections", ["item_id"], unique=False
    )
    op.create_index(
        op.f("ix_bank_connections_provider"), "bank_connections", ["provider"], unique=False
    )
    op.create_index(
        op.f("ix_bank_connections_status"), "bank_connections", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_bank_connections_user_id"), "bank_connections", ["user_id"], unique=False
    )

    # Create bank_accounts table
    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("account_id_external", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("official_name", sa.String(length=255), nullable=True),
        sa.Column(
            "account_type",
            sa.Enum(
                "CHECKING", "SAVINGS", "CREDIT", "LOAN", "INVESTMENT", "OTHER", name="accounttype"
            ),
            nullable=False,
        ),
        sa.Column("subtype", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("current_balance", sa.Float(), nullable=True),
        sa.Column("available_balance", sa.Float(), nullable=True),
        sa.Column("credit_limit", sa.Float(), nullable=True),
        sa.Column("mask", sa.String(length=4), nullable=True),
        sa.Column("is_syncing", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["bank_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bank_accounts_account_id_external"),
        "bank_accounts",
        ["account_id_external"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_accounts_connection_id"), "bank_accounts", ["connection_id"], unique=False
    )

    # Create bank_transactions table
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id_external", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "SUBSCRIPTION",
                "UTILITIES",
                "RENT",
                "INSURANCE",
                "LOAN",
                "TRANSFER",
                "INCOME",
                "SHOPPING",
                "FOOD",
                "TRANSPORT",
                "ENTERTAINMENT",
                "HEALTH",
                "OTHER",
                name="transactioncategory",
            ),
            nullable=False,
        ),
        sa.Column("category_raw", sa.String(length=100), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("pending", sa.Boolean(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False),
        sa.Column("recurring_stream_id", sa.String(length=100), nullable=True),
        sa.Column("matched_subscription_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["bank_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["bank_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["matched_subscription_id"], ["subscriptions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bank_transactions_account_id"), "bank_transactions", ["account_id"], unique=False
    )
    op.create_index(
        op.f("ix_bank_transactions_category"), "bank_transactions", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_bank_transactions_connection_id"),
        "bank_transactions",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_created_at"), "bank_transactions", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_bank_transactions_date"), "bank_transactions", ["date"], unique=False)
    op.create_index(
        op.f("ix_bank_transactions_is_recurring"),
        "bank_transactions",
        ["is_recurring"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_matched_subscription_id"),
        "bank_transactions",
        ["matched_subscription_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_merchant_name"),
        "bank_transactions",
        ["merchant_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_recurring_stream_id"),
        "bank_transactions",
        ["recurring_stream_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_transaction_id_external"),
        "bank_transactions",
        ["transaction_id_external"],
        unique=False,
    )


def downgrade() -> None:
    """Drop Open Banking tables."""
    # Drop bank_transactions table
    op.drop_index(
        op.f("ix_bank_transactions_transaction_id_external"), table_name="bank_transactions"
    )
    op.drop_index(op.f("ix_bank_transactions_recurring_stream_id"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_merchant_name"), table_name="bank_transactions")
    op.drop_index(
        op.f("ix_bank_transactions_matched_subscription_id"), table_name="bank_transactions"
    )
    op.drop_index(op.f("ix_bank_transactions_is_recurring"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_date"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_created_at"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_connection_id"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_category"), table_name="bank_transactions")
    op.drop_index(op.f("ix_bank_transactions_account_id"), table_name="bank_transactions")
    op.drop_table("bank_transactions")

    # Drop bank_accounts table
    op.drop_index(op.f("ix_bank_accounts_connection_id"), table_name="bank_accounts")
    op.drop_index(op.f("ix_bank_accounts_account_id_external"), table_name="bank_accounts")
    op.drop_table("bank_accounts")

    # Drop bank_connections table
    op.drop_index(op.f("ix_bank_connections_user_id"), table_name="bank_connections")
    op.drop_index(op.f("ix_bank_connections_status"), table_name="bank_connections")
    op.drop_index(op.f("ix_bank_connections_provider"), table_name="bank_connections")
    op.drop_index(op.f("ix_bank_connections_item_id"), table_name="bank_connections")
    op.drop_index(op.f("ix_bank_connections_institution_id"), table_name="bank_connections")
    op.drop_table("bank_connections")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transactioncategory")
    op.execute("DROP TYPE IF EXISTS accounttype")
    op.execute("DROP TYPE IF EXISTS consentstatus")
    op.execute("DROP TYPE IF EXISTS connectionstatus")
    op.execute("DROP TYPE IF EXISTS bankprovider")
