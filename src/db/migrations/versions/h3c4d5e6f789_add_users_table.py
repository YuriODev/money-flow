"""add_users_table

Revision ID: h3c4d5e6f789
Revises: 8288763654e3
Create Date: 2025-12-13

This migration originally added the users table for authentication and authorization.
Also adds user_id foreign key to subscriptions for multi-user support.

NOTE: users table and user_id are now created in the initial migration (0001_initial_schema).
This migration is kept for chain continuity but performs no operations.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "h3c4d5e6f789"
down_revision: str | Sequence[str] | None = "8288763654e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table and add user_id to subscriptions.

    No-op: These are now created in 0001_initial_schema migration.
    """
    pass


def downgrade() -> None:
    """Remove users table and user_id from subscriptions.

    No-op: These are dropped in 0001_initial_schema downgrade.
    """
    pass
