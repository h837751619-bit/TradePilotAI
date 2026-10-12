"""add manual inventory adjustment audit records

Revision ID: 20261011_inventory_adjustments
Revises: 20261011_inventory_movements
"""

from alembic import op
import sqlalchemy as sa


revision = "20261011_inventory_adjustments"
down_revision = "20261011_inventory_movements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("previous_quantity", sa.Integer(), nullable=False),
        sa.Column("new_quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False, server_default="manual adjustment"),
        sa.Column("actor", sa.String(length=120), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_inventory_adjustments_sku", "inventory_adjustments", ["sku"])


def downgrade() -> None:
    op.drop_index("ix_inventory_adjustments_sku", table_name="inventory_adjustments")
    op.drop_table("inventory_adjustments")
