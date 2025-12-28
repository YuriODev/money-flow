"""add_webhook_tables

Revision ID: 6ad2c590d49f
Revises: 7a2b3c4d5e6f
Create Date: 2025-12-28 10:38:19.443674

Sprint 5.6 - Webhooks System
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6ad2c590d49f'
down_revision: Union[str, Sequence[str], None] = '7a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add webhook tables for Sprint 5.6."""
    # Create webhook_subscriptions table
    op.create_table('webhook_subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('secret', sa.String(length=64), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String(length=50)), nullable=False),
        sa.Column('headers', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'DISABLED', 'DELETED', name='webhookstatus'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False),
        sa.Column('max_failures', sa.Integer(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_subscriptions_user_id'), 'webhook_subscriptions', ['user_id'], unique=False)

    # Create webhook_deliveries table
    op.create_table('webhook_deliveries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('webhook_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'RETRYING', name='deliverystatus'), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.String(length=1000), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_deliveries_created_at'), 'webhook_deliveries', ['created_at'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_event_type'), 'webhook_deliveries', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_status'), 'webhook_deliveries', ['status'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_webhook_id'), 'webhook_deliveries', ['webhook_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove webhook tables."""
    op.drop_index(op.f('ix_webhook_deliveries_webhook_id'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_status'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_event_type'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_created_at'), table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index(op.f('ix_webhook_subscriptions_user_id'), table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS deliverystatus")
    op.execute("DROP TYPE IF EXISTS webhookstatus")
