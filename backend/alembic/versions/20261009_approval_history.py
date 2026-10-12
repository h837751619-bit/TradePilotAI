"""add quote approval history

Revision ID: 20261009_approval_history
Revises: 20261007_product_match_tags
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_approval_history"
down_revision = "20261007_product_match_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("approval_history"):
        op.create_table(
            "approval_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("quote_id", sa.Integer(), nullable=False),
            sa.Column("from_status", sa.String(length=32), nullable=False),
            sa.Column("to_status", sa.String(length=32), nullable=False),
            sa.Column("actor", sa.String(length=120), nullable=False, server_default="manual-review"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    if "ix_approval_history_quote_id" not in {index["name"] for index in inspector.get_indexes("approval_history")}:
        op.create_index("ix_approval_history_quote_id", "approval_history", ["quote_id"])


def downgrade() -> None:
    op.drop_index("ix_approval_history_quote_id", table_name="approval_history")
    op.drop_table("approval_history")
