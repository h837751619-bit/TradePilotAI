"""add refresh tokens

Revision ID: 20261009_refresh_tokens
Revises: 20261009_users
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_refresh_tokens"
down_revision = "20261009_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
        )
    indexes = {index["name"] for index in inspector.get_indexes("refresh_tokens")}
    if "ix_refresh_tokens_user_id" not in indexes:
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    if "ix_refresh_tokens_token_hash" not in indexes:
        op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
