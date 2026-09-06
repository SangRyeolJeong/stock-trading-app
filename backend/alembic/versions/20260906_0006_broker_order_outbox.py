"""Add broker orders and transactional outbox.

Revision ID: 20260906_0006
Revises: 20260901_0005
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260906_0006"
down_revision: str | None = "20260901_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("client_order_id", sa.String(length=128), nullable=False),
        sa.Column("broker_order_id", sa.String(length=128), nullable=True),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("order_type", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("limit_price", sa.Numeric(28, 8), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("last_error", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("side IN ('buy', 'sell')", name=op.f("ck_broker_orders_side_valid")),
        sa.CheckConstraint("order_type IN ('market', 'limit')", name=op.f("ck_broker_orders_order_type_valid")),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_broker_orders_quantity_positive")),
        sa.CheckConstraint(
            "status IN ('pending_submission', 'submitted', 'cancel_pending', "
            "'cancelled', 'reconciliation_required')",
            name=op.f("ck_broker_orders_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], name=op.f("fk_broker_orders_account_id_paper_accounts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broker_orders")),
        sa.UniqueConstraint("broker_order_id", name=op.f("uq_broker_orders_broker_order_id")),
        sa.UniqueConstraint(
            "account_id", "client_order_id", name="uq_broker_orders_account_client_order"
        ),
    )
    op.create_index("ix_broker_orders_account_created", "broker_orders", ["account_id", "created_at"])
    op.create_index(op.f("ix_broker_orders_account_id"), "broker_orders", ["account_id"])
    op.create_table(
        "broker_outbox_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("last_error", sa.String(length=200), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('submit_order', 'cancel_order')",
            name=op.f("ck_broker_outbox_events_event_type_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processed', 'failed')",
            name=op.f("ck_broker_outbox_events_status_valid"),
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name=op.f("ck_broker_outbox_events_attempt_count_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["broker_orders.id"], name=op.f("fk_broker_outbox_events_order_id_broker_orders")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broker_outbox_events")),
    )
    op.create_index(
        "ix_broker_outbox_due",
        "broker_outbox_events",
        ["status", "next_attempt_at", "created_at"],
    )
    op.create_index(op.f("ix_broker_outbox_events_order_id"), "broker_outbox_events", ["order_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_broker_outbox_events_order_id"), table_name="broker_outbox_events")
    op.drop_index("ix_broker_outbox_due", table_name="broker_outbox_events")
    op.drop_table("broker_outbox_events")
    op.drop_index(op.f("ix_broker_orders_account_id"), table_name="broker_orders")
    op.drop_index("ix_broker_orders_account_created", table_name="broker_orders")
    op.drop_table("broker_orders")
