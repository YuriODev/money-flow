"""add_payment_mode_column

Revision ID: 369d67886082
Revises: e86b93e0cf9a
Create Date: 2025-12-18 18:45:59.221300

This migration adds the payment_mode column and migrates data from payment_type.

Payment Mode Mapping (payment_type values are UPPERCASE in PostgreSQL):
- SUBSCRIPTION -> RECURRING
- HOUSING -> RECURRING
- UTILITY -> RECURRING
- PROFESSIONAL_SERVICE -> RECURRING
- INSURANCE -> RECURRING
- DEBT -> DEBT
- SAVINGS -> SAVINGS
- TRANSFER -> RECURRING
- ONE_TIME -> ONE_TIME
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "369d67886082"
down_revision: Union[str, Sequence[str], None] = "e86b93e0cf9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mapping from old payment_type to new payment_mode
# Note: payment_type values in DB are UPPERCASE (PostgreSQL enum)
PAYMENT_TYPE_TO_MODE = {
    "SUBSCRIPTION": "recurring",
    "HOUSING": "recurring",
    "UTILITY": "recurring",
    "PROFESSIONAL_SERVICE": "recurring",
    "INSURANCE": "recurring",
    "DEBT": "debt",
    "SAVINGS": "savings",
    "TRANSFER": "recurring",
    "ONE_TIME": "one_time",
}


def upgrade() -> None:
    """Upgrade schema - add payment_mode column and migrate data."""
    # 1. Create the PaymentMode enum type
    paymentmode_enum = sa.Enum(
        "RECURRING", "ONE_TIME", "DEBT", "SAVINGS", name="paymentmode", create_type=False
    )
    paymentmode_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add payment_mode column with default 'RECURRING' (allows NULL temporarily)
    op.add_column(
        "subscriptions",
        sa.Column(
            "payment_mode",
            sa.Enum("RECURRING", "ONE_TIME", "DEBT", "SAVINGS", name="paymentmode"),
            nullable=True,
            server_default="RECURRING",
        ),
    )

    # 3. Migrate data from payment_type to payment_mode
    connection = op.get_bind()

    # Update each payment_type to corresponding payment_mode
    for old_type, new_mode in PAYMENT_TYPE_TO_MODE.items():
        connection.execute(
            sa.text(
                f"UPDATE subscriptions SET payment_mode = '{new_mode.upper()}' "
                f"WHERE payment_type = '{old_type}'"
            )
        )

    # 4. Set default for any remaining NULL values
    connection.execute(
        sa.text("UPDATE subscriptions SET payment_mode = 'RECURRING' WHERE payment_mode IS NULL")
    )

    # 5. Make the column NOT NULL now that all data is migrated
    op.alter_column("subscriptions", "payment_mode", nullable=False)

    # 6. Create index on payment_mode
    op.create_index(
        op.f("ix_subscriptions_payment_mode"), "subscriptions", ["payment_mode"], unique=False
    )

    # 7. Remove the old index from categories (was incorrectly detected)
    # Only drop if it exists
    try:
        op.drop_index(op.f("ix_categories_user_active"), table_name="categories")
    except Exception:
        pass  # Index may not exist


def downgrade() -> None:
    """Downgrade schema - remove payment_mode column."""
    # Drop the index
    op.drop_index(op.f("ix_subscriptions_payment_mode"), table_name="subscriptions")

    # Drop the column
    op.drop_column("subscriptions", "payment_mode")

    # Drop the enum type
    paymentmode_enum = sa.Enum("RECURRING", "ONE_TIME", "DEBT", "SAVINGS", name="paymentmode")
    paymentmode_enum.drop(op.get_bind(), checkfirst=True)

    # Recreate the categories index if it was dropped
    op.create_index(
        op.f("ix_categories_user_active"), "categories", ["user_id", "is_active"], unique=False
    )
