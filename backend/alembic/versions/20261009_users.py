"""add users table

Revision ID: 20261009_users
Revises: 20261009_approval_history
"""
from alembic import op
import sqlalchemy as sa


revision = "20261009_users"
down_revision = "20261009_approval_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(length=120), nullable=False),
            sa.Column("password_hash", sa.String(length=300), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False, server_default="viewer"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "ix_users_username" not in {index["name"] for index in inspector.get_indexes("users")}:
        op.create_index("ix_users_username", "users", ["username"], unique=True)
    if "ix_users_is_active" not in {index["name"] for index in inspector.get_indexes("users")}:
        op.create_index("ix_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
