"""persist embedding rebuild jobs

Revision ID: 20261014_embedding_rebuild_jobs
Revises: 20261014_rag_eval_metadata
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_embedding_rebuild_jobs"
down_revision = "20261014_rag_eval_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "embedding_rebuild_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("profile_id", sa.String(length=255), nullable=False),
        sa.Column("embedding_provider", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("processed_products", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_products", sa.Integer(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_products", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_embedding_rebuild_jobs_job_id", "embedding_rebuild_jobs", ["job_id"])
    op.create_index("ix_embedding_rebuild_jobs_status", "embedding_rebuild_jobs", ["status"])
    op.create_index("ix_embedding_rebuild_jobs_created_at", "embedding_rebuild_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_embedding_rebuild_jobs_created_at", table_name="embedding_rebuild_jobs")
    op.drop_index("ix_embedding_rebuild_jobs_status", table_name="embedding_rebuild_jobs")
    op.drop_index("ix_embedding_rebuild_jobs_job_id", table_name="embedding_rebuild_jobs")
    op.drop_table("embedding_rebuild_jobs")
