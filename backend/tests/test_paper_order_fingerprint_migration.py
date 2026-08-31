import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.schemas.paper import PaperOrderRequest
from app.services.paper_trading import order_request_fingerprint


def test_migration_backfills_existing_order_fingerprint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "paper-order-migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    get_settings.cache_clear()
    alembic_config = Config("alembic.ini")

    try:
        command.upgrade(alembic_config, "20260729_0003")
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                """
                INSERT INTO paper_accounts
                    (id, user_id, name, base_currency, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("legacy-account", "legacy-user", "Legacy", "USD", "active"),
            )
            connection.execute(
                """
                INSERT INTO securities (symbol, name, currency, market)
                VALUES (?, ?, ?, ?)
                """,
                ("QQQM", "Invesco NASDAQ 100 ETF", "USD", "NASDAQ"),
            )
            connection.execute(
                """
                INSERT INTO paper_orders
                    (id, account_id, security_symbol, idempotency_key, side,
                     order_type, quantity, requested_price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "11111111111111111111111111111111",
                    "legacy-account",
                    "QQQM",
                    "legacy-key",
                    "buy",
                    "limit",
                    "1.00000000",
                    "200.00000000",
                    "accepted",
                ),
            )

        command.upgrade(alembic_config, "head")

        expected = order_request_fingerprint(
            PaperOrderRequest(
                symbol="QQQM",
                side="buy",
                order_type="limit",
                quantity=Decimal("1.00000000"),
                limit_price=Decimal("200.00000000"),
                idempotency_key="legacy-key",
            )
        )
        with sqlite3.connect(database_path) as connection:
            fingerprint = connection.execute("SELECT request_fingerprint FROM paper_orders").fetchone()
            events = connection.execute(
                """
                SELECT sequence, previous_status, new_status, reason
                FROM order_status_events
                ORDER BY sequence
                """
            ).fetchall()
            columns = connection.execute("PRAGMA table_info('paper_orders')").fetchall()
            revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("UPDATE paper_orders SET status = 'unknown'")

        assert fingerprint == (expected,)
        assert events == [(1, None, "accepted", "migration_backfill")]
        assert next(column for column in columns if column[1] == "request_fingerprint")[3] == 1
        assert revision == ("20260901_0005",)
    finally:
        get_settings.cache_clear()
