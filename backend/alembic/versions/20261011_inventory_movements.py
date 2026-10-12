"""add inventory movement audit and reservation records

Revision ID: 20261011_inventory_movements
Revises: 20261011_agent_run_timestamps
"""

from alembic import op
import sqlalchemy as sa


revision = "20261011_inventory_movements"
down_revision = "20261011_agent_run_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_inventory_movements_quote_id", "inventory_movements", ["quote_id"])
    op.create_index("ix_inventory_movements_sku", "inventory_movements", ["sku"])
    op.create_index("ix_inventory_movements_movement_type", "inventory_movements", ["movement_type"])


def downgrade() -> None:
    op.drop_index("ix_inventory_movements_movement_type", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_sku", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_quote_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
