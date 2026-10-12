"""add product match tags

Revision ID: 20261007_product_match_tags
Revises: 20260929_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "20261007_product_match_tags"
down_revision = "20260929_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("match_tags", sa.String(length=500), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("products", "match_tags")
