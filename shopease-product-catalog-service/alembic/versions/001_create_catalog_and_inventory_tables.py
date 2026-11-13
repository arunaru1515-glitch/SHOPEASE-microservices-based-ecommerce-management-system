"""create catalog and inventory tables

Revision ID: 001_catalog_tables
Revises: 
Create Date: 2026-11-13 11:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_catalog_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Categories Table
    if "categories" not in existing_tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
        op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)

    # 2. Products Table
    if "products" not in existing_tables:
        op.create_table(
            "products",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("sku", sa.String(length=100), nullable=False),
            sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("discount_price", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("brand", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.CheckConstraint("price >= 0", name="chk_positive_price"),
            sa.CheckConstraint("stock_quantity >= 0", name="chk_non_negative_stock"),
            sa.ForeignKeyConstraint(
                ["category_id"],
                ["categories.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
        op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
        op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)
        op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)
        op.create_index(op.f("ix_products_brand"), "products", ["brand"], unique=False)
        op.create_index(op.f("ix_products_is_active"), "products", ["is_active"], unique=False)

    # 3. Inventory Transactions Table
    if "inventory_transactions" not in existing_tables:
        op.create_table(
            "inventory_transactions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("transaction_type", sa.String(length=20), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("previous_stock", sa.Integer(), nullable=False),
            sa.Column("updated_stock", sa.Integer(), nullable=False),
            sa.Column("remarks", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["product_id"],
                ["products.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_inventory_transactions_id"), "inventory_transactions", ["id"], unique=False)
        op.create_index(op.f("ix_inventory_transactions_product_id"), "inventory_transactions", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_table("inventory_transactions")
    op.drop_table("products")
    op.drop_table("categories")

