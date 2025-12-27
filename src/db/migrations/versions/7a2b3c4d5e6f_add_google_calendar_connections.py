"""add_google_calendar_connections

Revision ID: 7a2b3c4d5e6f
Revises: 69107cd3b0ea
Create Date: 2025-12-27 10:00:00.000000

Sprint 5.6 - Google Calendar OAuth Integration
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '69107cd3b0ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create google_calendar_connections table."""
    op.create_table(
        'google_calendar_connections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  unique=True, nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('calendar_id', sa.String(255), default='primary'),
        sa.Column('sync_status', sa.String(20), nullable=False, default='connected'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), default=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create index for user lookup
    op.create_index(
        'ix_google_calendar_connections_user_id',
        'google_calendar_connections',
        ['user_id'],
        unique=True
    )


def downgrade() -> None:
    """Drop google_calendar_connections table."""
    op.drop_index('ix_google_calendar_connections_user_id', table_name='google_calendar_connections')
    op.drop_table('google_calendar_connections')
