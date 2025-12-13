"""add_users_table

Revision ID: h3c4d5e6f789
Revises: 8288763654e3
Create Date: 2025-12-13

This migration adds the users table for authentication and authorization.
Also adds user_id foreign key to subscriptions for multi-user support.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h3c4d5e6f789"
down_revision: str | Sequence[str] | None = "8288763654e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table and add user_id to subscriptions."""
    # Create UserRole enum using raw SQL with DO block for IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('user', 'admin');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", index=True),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("preferences", sa.Text, nullable=True),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Alter role column to use the enum type
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")

    # Add user_id foreign key to subscriptions
    op.add_column(
        "subscriptions",
        sa.Column("user_id", sa.String(36), nullable=True),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_foreign_key(
        "fk_subscriptions_user_id",
        "subscriptions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Remove users table and user_id from subscriptions."""
    # Remove foreign key and column from subscriptions
    op.drop_constraint("fk_subscriptions_user_id", "subscriptions", type_="foreignkey")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_column("subscriptions", "user_id")

    # Drop users table
    op.drop_table("users")

    # Drop UserRole enum
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
