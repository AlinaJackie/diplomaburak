"""initial full schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-11

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("street", sa.String(length=120), nullable=True),
        sa.Column("house", sa.String(length=50), nullable=True),
        sa.Column("extra_info", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)

    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("price_level", sa.String(length=20), nullable=True),
        sa.Column("eta", sa.String(length=50), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("categories", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("opening_time", sa.String(length=5), nullable=True),
        sa.Column("closing_time", sa.String(length=5), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("minimum_order_amount", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("weight", sa.String(length=50), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("delivery_type", sa.String(length=50), nullable=True),
        sa.Column("delivery_fee", sa.Integer(), nullable=True),
        sa.Column("eta_minutes", sa.Integer(), nullable=True),
        sa.Column("total_price", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "partner_application",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_person", sa.String(length=120), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("verification_link", sa.String(length=255), nullable=False),
        sa.Column("planned_locations_count", sa.Integer(), nullable=False),
        sa.Column("edrpou_or_ipn", sa.String(length=50), nullable=False),
        sa.Column("business_description", sa.String(
            length=1000), nullable=False),
        sa.Column("personal_data_agreement", sa.Boolean(), nullable=False),
        sa.Column("representation_agreement", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_token"),
        "password_reset_tokens",
        ["token"],
        unique=True,
    )

    op.create_table(
        "favorite_restaurants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "restaurant_id",
            name="uq_user_restaurant_favorite",
        ),
    )

    op.create_table(
        "favorite_menu_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "menu_item_id",
            name="uq_user_menu_item_favorite",
        ),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )


def downgrade():
    op.drop_table("reviews")
    op.drop_table("order_status_history")
    op.drop_table("order_items")
    op.drop_table("favorite_menu_items")
    op.drop_table("favorite_restaurants")
    op.drop_index(op.f("ix_password_reset_tokens_token"),
                  table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("partner_application")
    op.drop_table("notifications")
    op.drop_table("orders")
    op.drop_table("menu_items")
    op.drop_table("restaurants")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
