"""Add notification_preferences table.

Revision ID: i4d5e6f7g890
Revises: h3c4d5e6f789
Create Date: 2025-12-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i4d5e6f7g890"
down_revision: str | None = "a1a2aec4f86a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create notification_preferences table."""
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        # Telegram integration
        sa.Column("telegram_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("telegram_chat_id", sa.String(50), nullable=True),
        sa.Column("telegram_username", sa.String(255), nullable=True),
        sa.Column("telegram_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("telegram_verification_code", sa.String(20), nullable=True),
        sa.Column("telegram_verification_expires", sa.DateTime(), nullable=True),
        # Reminder settings
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reminder_days_before", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reminder_time", sa.Time(), nullable=False, server_default="09:00:00"),
        sa.Column("overdue_alerts", sa.Boolean(), nullable=False, server_default="true"),
        # Digest settings
        sa.Column("daily_digest", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("weekly_digest", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("weekly_digest_day", sa.Integer(), nullable=False, server_default="0"),
        # Quiet hours
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    # Create index for user_id lookup
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
    )

    # Create index for Telegram chat_id lookup (for webhook handling)
    op.create_index(
        "ix_notification_preferences_telegram_chat_id",
        "notification_preferences",
        ["telegram_chat_id"],
    )


def downgrade() -> None:
    """Drop notification_preferences table."""
    op.drop_index(
        "ix_notification_preferences_telegram_chat_id", table_name="notification_preferences"
    )
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
