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

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1a2aec4f86a"
down_revision: str | Sequence[str] | None = "h3c4d5e6f789"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes for query optimization."""
    # Use raw SQL with IF NOT EXISTS for PostgreSQL compatibility
    # This handles cases where init_db() creates tables via create_all()
    # before migrations run (e.g., in E2E tests)
    from sqlalchemy import text

    bind = op.get_bind()

    def create_index_if_not_exists(index_name: str, table: str, columns: list[str]) -> None:
        """Create index only if it doesn't exist."""
        cols = ", ".join(columns)
        bind.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({cols})"))

    # ==========================================
    # CRITICAL: Subscriptions table indexes
    # ==========================================

    # Index for dashboard loads and API list queries
    # Used by: get_all(), get_upcoming(), summary calculations
    create_index_if_not_exists(
        "ix_subscriptions_user_active_next_payment",
        "subscriptions",
        ["user_id", "is_active", "next_payment_date"],
    )

    # Index for payment type filtering (Money Flow feature)
    # Used by: get_all(payment_type=...), debt/savings views
    create_index_if_not_exists(
        "ix_subscriptions_user_payment_type_active",
        "subscriptions",
        ["user_id", "payment_type", "is_active"],
    )

    # Index for card balance calculations
    # Used by: get_balance_summary(), card-related queries
    create_index_if_not_exists(
        "ix_subscriptions_card_active",
        "subscriptions",
        ["card_id", "is_active"],
    )

    # Index for category filtering
    # Used by: get_all(category=...), category-based views
    create_index_if_not_exists(
        "ix_subscriptions_user_category",
        "subscriptions",
        ["user_id", "category"],
    )

    # ==========================================
    # CRITICAL: Payment History table indexes
    # ==========================================

    # Index for balance calculations and payment lookup
    # Used by: get_balance_summary(), monthly payment calculations
    create_index_if_not_exists(
        "ix_payment_history_sub_date_status",
        "payment_history",
        ["subscription_id", "payment_date", "status"],
    )

    # ==========================================
    # MEDIUM: Conversations table indexes
    # ==========================================

    # Composite index for RAG context retrieval
    # Used by: get_context(), session-based queries
    create_index_if_not_exists(
        "ix_conversations_user_session",
        "conversations",
        ["user_id", "session_id"],
    )

    # ==========================================
    # LOW: RAG Analytics table indexes
    # ==========================================

    # Index for analytics time-range queries
    # Used by: get_metrics_for_period(), analytics dashboard
    create_index_if_not_exists(
        "ix_rag_analytics_user_created",
        "rag_analytics",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    """Remove performance indexes."""
    from sqlalchemy import text

    bind = op.get_bind()

    def drop_index_if_exists(index_name: str) -> None:
        """Drop index only if it exists."""
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))

    # Remove indexes in reverse order
    drop_index_if_exists("ix_rag_analytics_user_created")
    drop_index_if_exists("ix_conversations_user_session")
    drop_index_if_exists("ix_payment_history_sub_date_status")
    drop_index_if_exists("ix_subscriptions_user_category")
    drop_index_if_exists("ix_subscriptions_card_active")
    drop_index_if_exists("ix_subscriptions_user_payment_type_active")
    drop_index_if_exists("ix_subscriptions_user_active_next_payment")
