"""initial TradePilot schema

Revision ID: 20260929_initial
"""
import sqlalchemy as sa

from alembic import op

revision = "20260929_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(64), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("category", sa.String(100), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("material", sa.String(200), nullable=False), sa.Column("colors", sa.String(200), nullable=False), sa.Column("min_order_quantity", sa.Integer(), nullable=False), sa.Column("lead_time_days", sa.Integer(), nullable=False), sa.Column("unit_price_usd", sa.Float(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.UniqueConstraint("sku"))
    op.create_table("inventory", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(64), nullable=False), sa.Column("on_hand_quantity", sa.Integer(), nullable=False), sa.Column("reserved_quantity", sa.Integer(), nullable=False), sa.UniqueConstraint("sku"))
    op.create_table("customers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_name", sa.String(200), nullable=False), sa.Column("contact_name", sa.String(120), nullable=False), sa.Column("country", sa.String(80), nullable=False), sa.Column("email", sa.String(200), nullable=False), sa.UniqueConstraint("company_name"))
    op.create_table("quotes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_name", sa.String(200), nullable=False), sa.Column("inquiry_text", sa.Text(), nullable=False), sa.Column("sku", sa.String(64), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("unit_price_usd", sa.Float(), nullable=False), sa.Column("total_price_usd", sa.Float(), nullable=False), sa.Column("discount_percent", sa.Integer(), nullable=False), sa.Column("status", sa.String(32), nullable=False))
    op.create_table("agent_runs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("run_id", sa.String(64), nullable=False), sa.Column("inquiry_text", sa.Text(), nullable=False), sa.Column("steps", sa.JSON(), nullable=False), sa.UniqueConstraint("run_id"))


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("quotes")
    op.drop_table("customers")
    op.drop_table("inventory")
    op.drop_table("products")
