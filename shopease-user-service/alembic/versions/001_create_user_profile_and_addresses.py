"""Create user_profiles and user_addresses tables

Revision ID: 001_create_user_profile_and_addresses
Revises: 
Create Date: 2026-11-11 11:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_create_user_profile_and_addresses"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Create user_profiles table if it does not already exist
    if "user_profiles" not in existing_tables:
        op.create_table(
            "user_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("auth_user_id", sa.Integer(), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("phone_number", sa.String(length=20), nullable=True),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("gender", sa.String(length=20), nullable=True),
            sa.Column("profile_image", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        try:
            op.create_index(op.f("ix_user_profiles_id"), "user_profiles", ["id"], unique=False)
            op.create_index(op.f("ix_user_profiles_auth_user_id"), "user_profiles", ["auth_user_id"], unique=True)
        except Exception:
            pass

    # 2. Create user_addresses table if it does not already exist
    if "user_addresses" not in existing_tables:
        op.create_table(
            "user_addresses",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("address_type", sa.String(length=50), server_default="Home", nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("phone_number", sa.String(length=20), nullable=False),
            sa.Column("address_line_1", sa.String(length=255), nullable=False),
            sa.Column("address_line_2", sa.String(length=255), nullable=True),
            sa.Column("city", sa.String(length=100), nullable=False),
            sa.Column("state", sa.String(length=100), nullable=False),
            sa.Column("country", sa.String(length=100), nullable=False),
            sa.Column("postal_code", sa.String(length=20), nullable=False),
            sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        try:
            op.create_index(op.f("ix_user_addresses_id"), "user_addresses", ["id"], unique=False)
            op.create_index(op.f("ix_user_addresses_user_id"), "user_addresses", ["user_id"], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "user_addresses" in existing_tables:
        try:
            op.drop_index(op.f("ix_user_addresses_user_id"), table_name="user_addresses")
            op.drop_index(op.f("ix_user_addresses_id"), table_name="user_addresses")
        except Exception:
            pass
        op.drop_table("user_addresses")

    if "user_profiles" in existing_tables:
        try:
            op.drop_index(op.f("ix_user_profiles_auth_user_id"), table_name="user_profiles")
            op.drop_index(op.f("ix_user_profiles_id"), table_name="user_profiles")
        except Exception:
            pass
        op.drop_table("user_profiles")
