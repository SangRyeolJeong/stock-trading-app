from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import delete, select, update

from app.core.auth import DEMO_USER_ID
from app.db.session import async_session_factory
from app.models.paper import CashLedgerEntry, PaperExecution, PaperOrder, Position
from app.schemas.market import Quote
from app.schemas.paper import PaperOrderRequest
from app.services.paper_ledger_reconciliation import paper_ledger_reconciler
from app.services.paper_trading import paper_trading_service


def quote(price: str = "100") -> Quote:
    return Quote(
        symbol="QQQM",
        name="인베스코 나스닥 100 ETF",
        currency="USD",
        price=Decimal(price),
        change=Decimal("0"),
        change_rate=Decimal("0"),
        market_open=True,
        as_of=datetime.now(UTC),
    )


def order_request(key: str, *, side: str = "buy") -> PaperOrderRequest:
    return PaperOrderRequest(
        symbol="QQQM",
        side=side,
        order_type="market",
        quantity=Decimal("2") if side == "buy" else Decimal("1"),
        idempotency_key=key,
    )


async def execute_seed_orders() -> None:
    async with async_session_factory() as session:
        await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            order_request("reconcile-buy"),
            quote("100"),
        )
    async with async_session_factory() as session:
        await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            order_request("reconcile-sell", side="sell"),
            quote("110"),
        )


async def reconcile_codes() -> set[str]:
    async with async_session_factory() as session:
        report = await paper_ledger_reconciler.reconcile(session, "demo-account")
    return {issue.code for issue in report.issues}


@pytest.mark.asyncio
async def test_reconciler_accepts_consistent_orders_ledger_and_position() -> None:
    await execute_seed_orders()

    async with async_session_factory() as session:
        report = await paper_ledger_reconciler.reconcile(session)

    assert report.is_consistent is True
    assert report.checked_accounts == 1
    assert report.checked_orders == 2
    assert report.checked_ledger_entries == 6
    assert report.checked_positions == 1
    assert report.issues == ()


@pytest.mark.asyncio
async def test_reconciler_detects_execution_and_order_status_mismatch() -> None:
    await execute_seed_orders()
    async with async_session_factory() as session, session.begin():
        buy_order_id = await session.scalar(
            select(PaperOrder.id).where(PaperOrder.idempotency_key == "reconcile-buy")
        )
        await session.execute(
            update(PaperOrder).where(PaperOrder.id == buy_order_id).values(status="accepted")
        )

    codes = await reconcile_codes()

    assert "UNFILLED_HAS_EXECUTION" in codes


@pytest.mark.asyncio
async def test_reconciler_detects_missing_or_wrong_order_ledger_entries() -> None:
    await execute_seed_orders()
    async with async_session_factory() as session, session.begin():
        sell_order_id = await session.scalar(
            select(PaperOrder.id).where(PaperOrder.idempotency_key == "reconcile-sell")
        )
        await session.execute(
            delete(CashLedgerEntry).where(
                CashLedgerEntry.order_id == sell_order_id,
                CashLedgerEntry.entry_type == "commission",
            )
        )
        await session.execute(
            update(CashLedgerEntry)
            .where(
                CashLedgerEntry.order_id == sell_order_id,
                CashLedgerEntry.entry_type == "trade_settlement",
            )
            .values(amount=Decimal("999"))
        )

    codes = await reconcile_codes()

    assert "COMMISSION_LEDGER_COUNT" in codes
    assert "TRADE_LEDGER_AMOUNT" in codes
    assert "LATEST_BALANCE_MISMATCH" in codes


@pytest.mark.asyncio
async def test_reconciler_detects_duplicate_order_ledger_entry() -> None:
    await execute_seed_orders()
    async with async_session_factory() as session, session.begin():
        original = await session.scalar(
            select(CashLedgerEntry)
            .join(PaperOrder, PaperOrder.id == CashLedgerEntry.order_id)
            .where(
                PaperOrder.idempotency_key == "reconcile-buy",
                CashLedgerEntry.entry_type == "commission",
            )
        )
        assert original is not None
        session.add(
            CashLedgerEntry(
                account_id=original.account_id,
                order_id=original.order_id,
                currency=original.currency,
                entry_type=original.entry_type,
                amount=original.amount,
                balance_after=original.balance_after,
            )
        )

    codes = await reconcile_codes()

    assert "COMMISSION_LEDGER_COUNT" in codes


@pytest.mark.asyncio
async def test_reconciler_detects_execution_math_and_position_mismatch() -> None:
    await execute_seed_orders()
    async with async_session_factory() as session, session.begin():
        buy_order_id = await session.scalar(
            select(PaperOrder.id).where(PaperOrder.idempotency_key == "reconcile-buy")
        )
        await session.execute(
            update(PaperExecution)
            .where(PaperExecution.order_id == buy_order_id)
            .values(gross_amount=Decimal("1"))
        )
        await session.execute(
            update(Position)
            .where(Position.security_symbol == "QQQM")
            .values(quantity=Decimal("9"))
        )

    codes = await reconcile_codes()

    assert "EXECUTION_GROSS_MISMATCH" in codes
    assert "TRADE_LEDGER_AMOUNT" in codes
    assert "POSITION_QUANTITY_MISMATCH" in codes


@pytest.mark.asyncio
async def test_reconciler_reports_unknown_requested_account() -> None:
    async with async_session_factory() as session:
        report = await paper_ledger_reconciler.reconcile(session, "missing-account")

    assert report.is_consistent is False
    assert report.checked_accounts == 0
    assert report.issues[0].code == "ACCOUNT_NOT_FOUND"
