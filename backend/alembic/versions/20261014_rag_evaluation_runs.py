"""store RAG evaluation history

Revision ID: 20261014_rag_evaluation_runs
Revises: 20261011_inventory_adjustments
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_rag_evaluation_runs"
down_revision = "20261011_inventory_adjustments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("cases", sa.Integer(), nullable=False),
        sa.Column("evaluated_cases", sa.Integer(), nullable=False),
        sa.Column("top1_recall", sa.Float(), nullable=False),
        sa.Column("top3_recall", sa.Float(), nullable=False),
        sa.Column("mrr", sa.Float(), nullable=False),
        sa.Column("misses", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_rag_evaluation_runs_mode", "rag_evaluation_runs", ["mode"])
    op.create_index("ix_rag_evaluation_runs_created_at", "rag_evaluation_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_rag_evaluation_runs_created_at", table_name="rag_evaluation_runs")
    op.drop_index("ix_rag_evaluation_runs_mode", table_name="rag_evaluation_runs")
    op.drop_table("rag_evaluation_runs")
