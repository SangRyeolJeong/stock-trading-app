"""Enforce paper-order states and store transition history.

Revision ID: 20260901_0005
Revises: 20260823_0004
Create Date: 2026-09-01
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "20260901_0005"
down_revision: str | None = "20260823_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUSES = "'accepted', 'filled', 'cancelled', 'rejected'"


def upgrade() -> None:
    op.create_table(
        "order_status_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"previous_status IS NULL OR previous_status IN ({STATUSES})",
            name=op.f("ck_order_status_events_previous_status_valid"),
        ),
        sa.CheckConstraint(
            f"new_status IN ({STATUSES})",
            name=op.f("ck_order_status_events_new_status_valid"),
        ),
        sa.CheckConstraint(
            "(previous_status IS NULL AND new_status = 'accepted') OR "
            "(previous_status = 'accepted' AND "
            "new_status IN ('filled', 'cancelled', 'rejected'))",
            name=op.f("ck_order_status_events_transition_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["paper_orders.id"],
            name=op.f("fk_order_status_events_order_id_paper_orders"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_events")),
        sa.UniqueConstraint(
            "order_id",
            "sequence",
            name="uq_order_status_events_order_sequence",
        ),
    )
    op.create_index(
        "ix_order_status_events_order_created",
        "order_status_events",
        ["order_id", "created_at"],
    )
    op.create_index(
        op.f("ix_order_status_events_order_id"),
        "order_status_events",
        ["order_id"],
    )

    orders = sa.table(
        "paper_orders",
        sa.column("id", sa.Uuid()),
        sa.column("status", sa.String(length=20)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    events = sa.table(
        "order_status_events",
        sa.column("id", sa.Uuid()),
        sa.column("order_id", sa.Uuid()),
        sa.column("sequence", sa.Integer()),
        sa.column("previous_status", sa.String(length=20)),
        sa.column("new_status", sa.String(length=20)),
        sa.column("reason", sa.String(length=100)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    connection = op.get_bind()
    for order in connection.execute(sa.select(orders)).mappings():
        connection.execute(
            events.insert().values(
                id=uuid4(),
                order_id=order["id"],
                sequence=1,
                previous_status=None,
                new_status="accepted",
                reason="migration_backfill",
                created_at=order["created_at"],
            )
        )
        if order["status"] != "accepted":
            connection.execute(
                events.insert().values(
                    id=uuid4(),
                    order_id=order["id"],
                    sequence=2,
                    previous_status="accepted",
                    new_status=order["status"],
                    reason="migration_backfill",
                    created_at=order["created_at"],
                )
            )

    with op.batch_alter_table("paper_orders") as batch_op:
        batch_op.create_check_constraint(
            "status_valid",
            f"status IN ({STATUSES})",
        )


def downgrade() -> None:
    with op.batch_alter_table("paper_orders") as batch_op:
        batch_op.drop_constraint("status_valid", type_="check")
    op.drop_index(
        op.f("ix_order_status_events_order_id"),
        table_name="order_status_events",
    )
    op.drop_index(
        "ix_order_status_events_order_created",
        table_name="order_status_events",
    )
    op.drop_table("order_status_events")
