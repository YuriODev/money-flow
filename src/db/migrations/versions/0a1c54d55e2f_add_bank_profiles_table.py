"""add_bank_profiles_table

Revision ID: 0a1c54d55e2f
Revises: 55688a8830bc
Create Date: 2025-12-20 12:47:49.306024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0a1c54d55e2f'
down_revision: Union[str, Sequence[str], None] = '55688a8830bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bank_profiles table for dynamic bank statement parsing configuration."""
    op.create_table(
        'bank_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='GBP'),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('csv_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('pdf_patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('detection_patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_verified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_bank_profiles_name', 'bank_profiles', ['name'], unique=False)
    op.create_index('ix_bank_profiles_slug', 'bank_profiles', ['slug'], unique=True)
    op.create_index('ix_bank_profiles_country_code', 'bank_profiles', ['country_code'], unique=False)


def downgrade() -> None:
    """Drop bank_profiles table."""
    op.drop_index('ix_bank_profiles_country_code', table_name='bank_profiles')
    op.drop_index('ix_bank_profiles_slug', table_name='bank_profiles')
    op.drop_index('ix_bank_profiles_name', table_name='bank_profiles')
    op.drop_table('bank_profiles')
