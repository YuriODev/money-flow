"""add_integration_tables

Revision ID: c3c81f458195
Revises: 6ad2c590d49f
Create Date: 2025-12-28 18:10:14.351580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3c81f458195'
down_revision: Union[str, Sequence[str], None] = '6ad2c590d49f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),
        sa.Column('integration_type', sa.Enum('ZAPIER', 'IFTTT', 'CUSTOM', name='integrationtype'), nullable=False),
        sa.Column('scopes', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)

    # Create rest_hook_subscriptions table
    op.create_table('rest_hook_subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('api_key_id', sa.String(length=36), nullable=True),
        sa.Column('integration_type', sa.Enum('ZAPIER', 'IFTTT', 'CUSTOM', name='integrationtype'), nullable=False),
        sa.Column('target_url', sa.String(length=2000), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'EXPIRED', 'REVOKED', name='integrationstatus'), nullable=False),
        sa.Column('delivery_count', sa.Integer(), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('last_delivery_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rest_hook_subscriptions_created_at'), 'rest_hook_subscriptions', ['created_at'], unique=False)
    op.create_index(op.f('ix_rest_hook_subscriptions_event_type'), 'rest_hook_subscriptions', ['event_type'], unique=False)
    op.create_index(op.f('ix_rest_hook_subscriptions_integration_type'), 'rest_hook_subscriptions', ['integration_type'], unique=False)
    op.create_index(op.f('ix_rest_hook_subscriptions_user_id'), 'rest_hook_subscriptions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop rest_hook_subscriptions table
    op.drop_index(op.f('ix_rest_hook_subscriptions_user_id'), table_name='rest_hook_subscriptions')
    op.drop_index(op.f('ix_rest_hook_subscriptions_integration_type'), table_name='rest_hook_subscriptions')
    op.drop_index(op.f('ix_rest_hook_subscriptions_event_type'), table_name='rest_hook_subscriptions')
    op.drop_index(op.f('ix_rest_hook_subscriptions_created_at'), table_name='rest_hook_subscriptions')
    op.drop_table('rest_hook_subscriptions')

    # Drop api_keys table
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_table('api_keys')

    # Drop enums
    sa.Enum(name='integrationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='integrationtype').drop(op.get_bind(), checkfirst=True)
