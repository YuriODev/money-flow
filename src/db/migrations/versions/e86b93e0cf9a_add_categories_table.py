"""Add categories table and category_id to subscriptions.

Sprint 5.2.2.1 - Categories Model

Creates the categories table for user-defined subscription organization with:
- Custom colors and icons
- Optional budget tracking per category
- User ownership for multi-tenant support

Also adds category_id foreign key to subscriptions table.

Revision ID: e86b93e0cf9a
Revises: i4d5e6f7g890
Create Date: 2025-12-18 17:37:44.946939
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e86b93e0cf9a"
down_revision: str | Sequence[str] | None = "i4d5e6f7g890"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create categories table and add category_id to subscriptions."""
    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366F1"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("budget_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_currency", sa.String(3), nullable=False, server_default="GBP"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for categories
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_user_id", "categories", ["user_id"])
    op.create_index("ix_categories_user_active", "categories", ["user_id", "is_active"])

    # Add category_id to subscriptions
    op.add_column(
        "subscriptions", sa.Column("category_id", sa.String(length=36), nullable=True)
    )
    op.create_index(
        op.f("ix_subscriptions_category_id"), "subscriptions", ["category_id"], unique=False
    )
    op.create_foreign_key(
        "fk_subscriptions_category_id",
        "subscriptions",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Drop categories table and remove category_id from subscriptions."""
    # Remove category_id from subscriptions
    op.drop_constraint("fk_subscriptions_category_id", "subscriptions", type_="foreignkey")
    op.drop_index(op.f("ix_subscriptions_category_id"), table_name="subscriptions")
    op.drop_column("subscriptions", "category_id")

    # Drop categories indexes
    op.drop_index("ix_categories_user_active", table_name="categories")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")

    # Drop categories table
    op.drop_table("categories")
