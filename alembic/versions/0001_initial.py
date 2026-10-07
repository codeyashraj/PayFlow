"""create initial payflow tables
Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0001_initial"; down_revision=None; branch_labels=None; depends_on=None

def upgrade():
    op.create_table("users",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("email",sa.String(320),nullable=False,unique=True),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index("ix_users_email","users",["email"])
    op.create_table("orders",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="PENDING"),sa.Column("total_amount",sa.Numeric(12,2),nullable=False),sa.Column("currency",sa.String(3),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index("ix_orders_user_id","orders",["user_id"]); op.create_index("ix_orders_status","orders",["status"]); op.create_index("ix_orders_user_created","orders",["user_id","created_at"])
    op.create_table("order_items",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("order_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("orders.id",ondelete="CASCADE"),nullable=False),sa.Column("product_name",sa.String(255),nullable=False),sa.Column("quantity",sa.Integer,nullable=False),sa.Column("unit_price",sa.Numeric(12,2),nullable=False))
    op.create_index("ix_order_items_order_id","order_items",["order_id"])
    op.create_table("payments",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("order_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("orders.id",ondelete="CASCADE"),nullable=False),sa.Column("provider_payment_id",sa.String(255),unique=True),sa.Column("amount",sa.Numeric(12,2),nullable=False),sa.Column("currency",sa.String(3),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="pending"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index("ix_payments_order_id","payments",["order_id"]); op.create_index("ix_payments_provider_payment_id","payments",["provider_payment_id"]); op.create_index("ix_payments_status","payments",["status"]); op.create_index("ix_payments_order_status","payments",["order_id","status"])
    op.create_table("webhook_events",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("event_id",sa.String(255),nullable=False,unique=True),sa.Column("event_type",sa.String(100),nullable=False),sa.Column("payment_id",sa.String(255),nullable=False),sa.Column("payload",sa.Text,nullable=False),sa.Column("processed",sa.Boolean,nullable=False,server_default=sa.text("false")),sa.Column("received_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("processed_at",sa.DateTime(timezone=True)))
    op.create_index("ix_webhook_events_event_id","webhook_events",["event_id"]); op.create_index("ix_webhook_events_processed","webhook_events",["processed"])

def downgrade():
    op.drop_table("webhook_events"); op.drop_table("payments"); op.drop_table("order_items"); op.drop_table("orders"); op.drop_table("users")
