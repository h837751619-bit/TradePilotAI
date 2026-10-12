"""add Agent Run timestamps

Revision ID: 20261011_agent_run_timestamps
Revises: 20261009_refresh_tokens
"""

from alembic import op
import sqlalchemy as sa


revision = "20261011_agent_run_timestamps"
down_revision = "20261009_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    if "created_at" not in columns:
        op.add_column("agent_runs", sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    if "created_at" in columns:
        op.drop_column("agent_runs", "created_at")
