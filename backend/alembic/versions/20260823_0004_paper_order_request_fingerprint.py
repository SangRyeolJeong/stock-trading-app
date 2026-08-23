"""Store normalized paper-order request fingerprints.

Revision ID: 20260823_0004
Revises: 20260729_0003
Create Date: 2026-08-23
"""

import json
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256
from typing import Any

import sqlalchemy as sa

from alembic import op

revision: str = "20260823_0004"
down_revision: str | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DECIMAL_QUANTUM = Decimal("0.00000001")
FINGERPRINT_VERSION = 1


def _canonical_decimal(value: Decimal) -> str:
    return format(value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP), "f")


def _request_fingerprint(row: Mapping[str, Any]) -> str:
    limit_price = row["requested_price"]
    payload = json.dumps(
        {
            "limit_price": (_canonical_decimal(Decimal(limit_price)) if limit_price is not None else None),
            "order_type": row["order_type"],
            "quantity": _canonical_decimal(Decimal(row["quantity"])),
            "side": row["side"],
            "symbol": row["security_symbol"],
            "version": FINGERPRINT_VERSION,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column(
        "paper_orders",
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
    )

    paper_orders = sa.table(
        "paper_orders",
        sa.column("id", sa.Uuid()),
        sa.column("security_symbol", sa.String(length=12)),
        sa.column("side", sa.String(length=4)),
        sa.column("order_type", sa.String(length=10)),
        sa.column("quantity", sa.Numeric(28, 8)),
        sa.column("requested_price", sa.Numeric(28, 8)),
        sa.column("request_fingerprint", sa.String(length=64)),
    )
    connection = op.get_bind()
    rows = (
        connection.execute(
            sa.select(
                paper_orders.c.id,
                paper_orders.c.security_symbol,
                paper_orders.c.side,
                paper_orders.c.order_type,
                paper_orders.c.quantity,
                paper_orders.c.requested_price,
            )
        )
        .mappings()
        .all()
    )
    for row in rows:
        connection.execute(
            paper_orders.update()
            .where(paper_orders.c.id == row["id"])
            .values(request_fingerprint=_request_fingerprint(row))
        )

    with op.batch_alter_table("paper_orders") as batch_op:
        batch_op.alter_column(
            "request_fingerprint",
            existing_type=sa.String(length=64),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("paper_orders") as batch_op:
        batch_op.drop_column("request_fingerprint")
