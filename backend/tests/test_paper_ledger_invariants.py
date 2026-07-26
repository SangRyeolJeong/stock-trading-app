import asyncio
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.main import app
from app.models.paper import CashLedgerEntry, PaperExecution, PaperOrder, Position

client = TestClient(app)


def order(side: str, quantity: int, price: str, key: str) -> dict[str, object]:
    return {
        "symbol": "QQQM",
        "side": side,
        "order_type": "limit",
        "quantity": quantity,
        "limit_price": price,
        "account_id": "demo-account",
        "idempotency_key": key,
    }


def test_order_execution_ledger_and_position_invariants() -> None:
    assert client.post("/api/v1/paper/orders", json=order("buy", 2, "200", "invariant-buy-01")).status_code == 201
    assert client.post("/api/v1/paper/orders", json=order("sell", 1, "250", "invariant-sell-01")).status_code == 201

    async def inspect() -> dict[str, object]:
        async with async_session_factory() as session:
            position = await session.scalar(
                select(Position).where(
                    Position.account_id == "demo-account",
                    Position.security_symbol == "QQQM",
                )
            )
            assert position is not None
            return {
                "orders": await session.scalar(select(func.count()).select_from(PaperOrder)),
                "executions": await session.scalar(select(func.count()).select_from(PaperExecution)),
                "ledger_entries": await session.scalar(select(func.count()).select_from(CashLedgerEntry)),
                "usd_cash": await session.scalar(
                    select(func.sum(CashLedgerEntry.amount)).where(CashLedgerEntry.currency == "USD")
                ),
                "quantity": position.quantity,
                "average_cost": position.average_cost,
                "realized_pnl": position.realized_pnl,
            }

    state = asyncio.run(inspect())

    assert state == {
        "orders": 2,
        "executions": 2,
        "ledger_entries": 6,
        "usd_cash": Decimal("9849.35000000"),
        "quantity": Decimal("1.00000000"),
        "average_cost": Decimal("200.00000000"),
        "realized_pnl": Decimal("49.75000000"),
    }
