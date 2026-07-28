"""Create the transactional paper-trading ledger.

Revision ID: 20260726_0001
Revises:
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260726_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "paper_accounts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paper_accounts")),
    )
    op.create_index(op.f("ix_paper_accounts_user_id"), "paper_accounts", ["user_id"])
    op.create_table(
        "securities",
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("market", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("symbol", name=op.f("pk_securities")),
    )
    op.create_table(
        "paper_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("security_symbol", sa.String(length=12), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("order_type", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("requested_price", sa.Numeric(precision=28, scale=8), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_paper_orders_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], name=op.f("fk_paper_orders_account_id_paper_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["security_symbol"], ["securities.symbol"], name=op.f("fk_paper_orders_security_symbol_securities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paper_orders")),
        sa.UniqueConstraint(
            "account_id",
            "idempotency_key",
            name="uq_paper_orders_account_id_idempotency_key",
        ),
    )
    op.create_index("ix_paper_orders_account_created", "paper_orders", ["account_id", "created_at"])
    op.create_index(op.f("ix_paper_orders_account_id"), "paper_orders", ["account_id"])
    op.create_table(
        "paper_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("price", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("gross_amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("fee", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "executed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint("price > 0", name=op.f("ck_paper_executions_price_positive")),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_paper_executions_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["order_id"], ["paper_orders.id"], name=op.f("fk_paper_executions_order_id_paper_orders")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paper_executions")),
        sa.UniqueConstraint("order_id", name=op.f("uq_paper_executions_order_id")),
    )
    op.create_table(
        "cash_ledger_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("entry_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], name=op.f("fk_cash_ledger_entries_account_id_paper_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["paper_orders.id"], name=op.f("fk_cash_ledger_entries_order_id_paper_orders")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_ledger_entries")),
    )
    op.create_index(op.f("ix_cash_ledger_entries_account_id"), "cash_ledger_entries", ["account_id"])
    op.create_index(
        "ix_cash_ledger_account_currency_created",
        "cash_ledger_entries",
        ["account_id", "currency", "created_at"],
    )
    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("security_symbol", sa.String(length=12), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_positions_quantity_nonnegative")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], name=op.f("fk_positions_account_id_paper_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["security_symbol"], ["securities.symbol"], name=op.f("fk_positions_security_symbol_securities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_positions")),
        sa.UniqueConstraint("account_id", "security_symbol", name="uq_positions_account_id_security_symbol"),
    )
    op.create_index(op.f("ix_positions_account_id"), "positions", ["account_id"])
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("cash_value", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("positions_value", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], name=op.f("fk_portfolio_snapshots_account_id_paper_accounts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_portfolio_snapshots")),
    )
    op.create_index(op.f("ix_portfolio_snapshots_account_id"), "portfolio_snapshots", ["account_id"])
    op.create_index(
        "ix_portfolio_snapshots_account_created",
        "portfolio_snapshots",
        ["account_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_portfolio_snapshots_account_created", table_name="portfolio_snapshots")
    op.drop_index(op.f("ix_portfolio_snapshots_account_id"), table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
    op.drop_index(op.f("ix_positions_account_id"), table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_cash_ledger_account_currency_created", table_name="cash_ledger_entries")
    op.drop_index(op.f("ix_cash_ledger_entries_account_id"), table_name="cash_ledger_entries")
    op.drop_table("cash_ledger_entries")
    op.drop_table("paper_executions")
    op.drop_index(op.f("ix_paper_orders_account_id"), table_name="paper_orders")
    op.drop_index("ix_paper_orders_account_created", table_name="paper_orders")
    op.drop_table("paper_orders")
    op.drop_table("securities")
    op.drop_index(op.f("ix_paper_accounts_user_id"), table_name="paper_accounts")
    op.drop_table("paper_accounts")
