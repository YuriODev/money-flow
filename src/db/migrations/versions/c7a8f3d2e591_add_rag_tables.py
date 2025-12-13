"""add_rag_tables

Revision ID: c7a8f3d2e591
Revises: 41ee05d4b675
Create Date: 2025-11-30

This migration adds RAG (Retrieval-Augmented Generation) tables:
- conversations: Store conversation turns for context retrieval
- rag_analytics: Track RAG query metrics and performance
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a8f3d2e591"
down_revision: str | Sequence[str] | None = "41ee05d4b675"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Creates RAG tables for conversation storage and analytics.
    """
    # Create conversations table for storing conversation turns
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),  # user or assistant
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "entities", sa.JSON(), nullable=True
        ),  # Extracted entities (subscription names, etc.)
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient queries
    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
    )
    op.create_index(
        "ix_conversations_session_id",
        "conversations",
        ["session_id"],
    )
    op.create_index(
        "ix_conversations_timestamp",
        "conversations",
        ["timestamp"],
    )
    # Composite index for common query pattern
    op.create_index(
        "ix_conversations_user_session",
        "conversations",
        ["user_id", "session_id"],
    )

    # Create rag_analytics table for tracking RAG performance
    op.create_table(
        "rag_analytics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("resolved_query", sa.Text(), nullable=True),  # Query after reference resolution
        sa.Column(
            "context_turns", sa.Integer(), nullable=False, server_default="0"
        ),  # Number of context turns used
        sa.Column("relevant_history_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "embedding_latency_ms", sa.Integer(), nullable=True
        ),  # Time to generate embedding
        sa.Column("search_latency_ms", sa.Integer(), nullable=True),  # Time to search vector DB
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),  # Total RAG latency
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("avg_relevance_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("entities_resolved", sa.JSON(), nullable=True),  # Entities that were resolved
        sa.Column("error", sa.Text(), nullable=True),  # Error message if RAG failed
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for analytics queries
    op.create_index(
        "ix_rag_analytics_user_id",
        "rag_analytics",
        ["user_id"],
    )
    op.create_index(
        "ix_rag_analytics_created_at",
        "rag_analytics",
        ["created_at"],
    )
    op.create_index(
        "ix_rag_analytics_cache_hit",
        "rag_analytics",
        ["cache_hit"],
    )


def downgrade() -> None:
    """Downgrade schema.

    Removes RAG tables.
    """
    # Drop indexes
    op.drop_index("ix_rag_analytics_cache_hit", table_name="rag_analytics")
    op.drop_index("ix_rag_analytics_created_at", table_name="rag_analytics")
    op.drop_index("ix_rag_analytics_user_id", table_name="rag_analytics")
    op.drop_table("rag_analytics")

    op.drop_index("ix_conversations_user_session", table_name="conversations")
    op.drop_index("ix_conversations_timestamp", table_name="conversations")
    op.drop_index("ix_conversations_session_id", table_name="conversations")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
