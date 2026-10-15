"""add RAG evaluation experiment metadata

Revision ID: 20261014_rag_eval_metadata
Revises: 20261014_rag_evaluation_runs
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_rag_eval_metadata"
down_revision = "20261014_rag_evaluation_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("rag_evaluation_runs")}
    if "embedding_provider" not in existing:
        op.add_column("rag_evaluation_runs", sa.Column("embedding_provider", sa.String(length=64), nullable=False, server_default="rules"))
    if "embedding_model" not in existing:
        op.add_column("rag_evaluation_runs", sa.Column("embedding_model", sa.String(length=200), nullable=False, server_default="rules"))
    if "retrieval_config" not in existing:
        op.add_column("rag_evaluation_runs", sa.Column("retrieval_config", sa.JSON(), nullable=True))
    op.execute("UPDATE rag_evaluation_runs SET retrieval_config = JSON_OBJECT() WHERE retrieval_config IS NULL")
    op.alter_column("rag_evaluation_runs", "retrieval_config", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    op.drop_column("rag_evaluation_runs", "retrieval_config")
    op.drop_column("rag_evaluation_runs", "embedding_model")
    op.drop_column("rag_evaluation_runs", "embedding_provider")
