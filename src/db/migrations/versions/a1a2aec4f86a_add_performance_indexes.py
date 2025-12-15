"""add_performance_indexes

Sprint 2.4.3 - Database Query Optimization

Adds composite indexes for frequently queried columns to improve performance:
- subscriptions: (user_id, is_active, next_payment_date) - Dashboard and upcoming
- subscriptions: (user_id, payment_type, is_active) - Payment type filtering
- subscriptions: (card_id, is_active) - Card balance calculations
- subscriptions: (user_id, category) - Category filtering
- payment_history: (subscription_id, payment_date, status) - Balance calculations
- conversations: (user_id, session_id) - RAG context retrieval
- rag_analytics: (user_id, created_at) - Analytics reporting

Revision ID: a1a2aec4f86a
Revises: h3c4d5e6f789
Create Date: 2025-12-15 21:30:15.706200

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1a2aec4f86a"
down_revision: Union[str, Sequence[str], None] = "h3c4d5e6f789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for query optimization."""

    # ==========================================
    # CRITICAL: Subscriptions table indexes
    # ==========================================

    # Index for dashboard loads and API list queries
    # Used by: get_all(), get_upcoming(), summary calculations
    op.create_index(
        "ix_subscriptions_user_active_next_payment",
        "subscriptions",
        ["user_id", "is_active", "next_payment_date"],
        unique=False,
    )

    # Index for payment type filtering (Money Flow feature)
    # Used by: get_all(payment_type=...), debt/savings views
    op.create_index(
        "ix_subscriptions_user_payment_type_active",
        "subscriptions",
        ["user_id", "payment_type", "is_active"],
        unique=False,
    )

    # Index for card balance calculations
    # Used by: get_balance_summary(), card-related queries
    op.create_index(
        "ix_subscriptions_card_active",
        "subscriptions",
        ["card_id", "is_active"],
        unique=False,
    )

    # Index for category filtering
    # Used by: get_all(category=...), category-based views
    op.create_index(
        "ix_subscriptions_user_category",
        "subscriptions",
        ["user_id", "category"],
        unique=False,
    )

    # ==========================================
    # CRITICAL: Payment History table indexes
    # ==========================================

    # Index for balance calculations and payment lookup
    # Used by: get_balance_summary(), monthly payment calculations
    op.create_index(
        "ix_payment_history_sub_date_status",
        "payment_history",
        ["subscription_id", "payment_date", "status"],
        unique=False,
    )

    # ==========================================
    # MEDIUM: Conversations table indexes
    # ==========================================

    # Composite index for RAG context retrieval
    # Used by: get_context(), session-based queries
    op.create_index(
        "ix_conversations_user_session",
        "conversations",
        ["user_id", "session_id"],
        unique=False,
    )

    # ==========================================
    # LOW: RAG Analytics table indexes
    # ==========================================

    # Index for analytics time-range queries
    # Used by: get_metrics_for_period(), analytics dashboard
    op.create_index(
        "ix_rag_analytics_user_created",
        "rag_analytics",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""

    # Remove indexes in reverse order
    op.drop_index("ix_rag_analytics_user_created", table_name="rag_analytics")
    op.drop_index("ix_conversations_user_session", table_name="conversations")
    op.drop_index("ix_payment_history_sub_date_status", table_name="payment_history")
    op.drop_index("ix_subscriptions_user_category", table_name="subscriptions")
    op.drop_index("ix_subscriptions_card_active", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_payment_type_active", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_active_next_payment", table_name="subscriptions")
