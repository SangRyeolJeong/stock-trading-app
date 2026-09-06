from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.core.auth import DEMO_USER_ID
from app.db.session import async_session_factory
from app.models.paper import (
    CashLedgerEntry,
    PaperExecution,
    PaperOrder,
    PaperOrderStatusEvent,
    PortfolioSnapshot,
    Position,
    Security,
)
from app.schemas.market import Quote
from app.schemas.paper import PaperOrderRequest
from app.services.paper_trading import paper_trading_service


class InjectedSettlementFailure(RuntimeError):
    pass


class RetryablePostgreSQLError(RuntimeError):
    sqlstate = "40P01"


def market_order() -> PaperOrderRequest:
    return PaperOrderRequest(
        symbol="QQQM",
        side="buy",
        order_type="market",
        quantity=Decimal("1"),
        idempotency_key="atomic-order-0001",
    )


def quote() -> Quote:
    return Quote(
        symbol="QQQM",
        name="인베스코 나스닥 100 ETF",
        currency="USD",
        price=Decimal("231.72"),
        change=Decimal("0"),
        change_rate=Decimal("0"),
        market_open=True,
        as_of=datetime.now(UTC),
    )


async def persisted_state() -> dict[str, Any]:
    async with async_session_factory() as session:
        positions = (
            await session.execute(
                select(
                    Position.account_id,
                    Position.security_symbol,
                    Position.quantity,
                    Position.average_cost,
                    Position.realized_pnl,
                ).order_by(Position.account_id, Position.security_symbol)
            )
        ).all()
        balances = (
            await session.execute(
                select(CashLedgerEntry.currency, func.sum(CashLedgerEntry.amount))
                .group_by(CashLedgerEntry.currency)
                .order_by(CashLedgerEntry.currency)
            )
        ).all()
        return {
            "orders": await session.scalar(select(func.count()).select_from(PaperOrder)),
            "executions": await session.scalar(select(func.count()).select_from(PaperExecution)),
            "ledger_count": await session.scalar(select(func.count()).select_from(CashLedgerEntry)),
            "ledger_amount": await session.scalar(
                select(func.coalesce(func.sum(CashLedgerEntry.amount), Decimal("0")))
            ),
            "balances": list(balances),
            "positions": list(positions),
            "snapshots": await session.scalar(select(func.count()).select_from(PortfolioSnapshot)),
            "securities": list(await session.scalars(select(Security.symbol).order_by(Security.symbol))),
        }


async def ensure_account() -> None:
    async with async_session_factory() as session, session.begin():
        await paper_trading_service.ensure_user_account(session, DEMO_USER_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stage", "fail_before"),
    [
        ("_create_order", False),
        ("_apply_position_change", False),
        ("_record_execution", False),
        ("_record_trade_settlement", False),
        ("_record_commission", False),
        ("_record_portfolio_snapshot", True),
    ],
    ids=[
        "after-order",
        "after-position",
        "after-execution",
        "after-trade-ledger",
        "after-commission-ledger",
        "before-portfolio-snapshot",
    ],
)
async def test_settlement_failure_rolls_back_every_persisted_change_and_allows_retry(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    fail_before: bool,
) -> None:
    await ensure_account()
    before = await persisted_state()
    original = getattr(paper_trading_service, stage)

    async def inject_failure(*args: Any, **kwargs: Any) -> Any:
        if not fail_before:
            await original(*args, **kwargs)
            session = args[0]
            await session.flush()
        raise InjectedSettlementFailure(stage)

    with monkeypatch.context() as patch:
        patch.setattr(paper_trading_service, stage, inject_failure)
        async with async_session_factory() as session:
            with pytest.raises(InjectedSettlementFailure, match=stage):
                await paper_trading_service.execute_immediately(
                    session,
                    DEMO_USER_ID,
                    market_order(),
                    quote(),
                )

    assert await persisted_state() == before

    async with async_session_factory() as session:
        retried = await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            market_order(),
            quote(),
        )

    assert retried.status == "filled"
    assert retried.idempotency_key == "atomic-order-0001"
    after_retry = await persisted_state()
    assert after_retry["orders"] == 1
    assert after_retry["executions"] == 1
    assert after_retry["ledger_count"] == before["ledger_count"] + 2
    assert after_retry["snapshots"] == 1
    assert after_retry["securities"] == ["QQQM"]


@pytest.mark.asyncio
async def test_expected_resource_failure_rejects_pending_order_and_commits_business_result() -> None:
    request = PaperOrderRequest(
        symbol="QQQM",
        side="buy",
        order_type="limit",
        quantity=Decimal("40"),
        limit_price=Decimal("200"),
        idempotency_key="atomic-pending-0001",
    )
    async with async_session_factory() as session:
        pending = await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            request,
            quote(),
        )

    assert pending.status == "accepted"

    async with async_session_factory() as session, session.begin():
        session.add(
            CashLedgerEntry(
                account_id="demo-account",
                currency="USD",
                entry_type="test_adjustment",
                amount=Decimal("-3000"),
                balance_after=Decimal("7000"),
            )
        )

    reached_quote = quote().model_copy(update={"price": Decimal("199")})
    async with async_session_factory() as session:
        await paper_trading_service.try_fill_pending_order(
            session,
            DEMO_USER_ID,
            pending.id,
            reached_quote,
        )

    async with async_session_factory() as session:
        order = await session.get(PaperOrder, pending.id)
        assert order is not None
        assert order.status == "rejected"
        events = list(
            await session.scalars(
                select(PaperOrderStatusEvent)
                .where(PaperOrderStatusEvent.order_id == pending.id)
                .order_by(PaperOrderStatusEvent.sequence)
            )
        )
        assert [event.new_status for event in events] == ["accepted", "rejected"]
        assert events[-1].reason == "resources_unavailable_at_fill"
        assert await session.scalar(select(func.count()).select_from(PaperExecution)) == 0
        assert await session.scalar(select(func.count()).select_from(Position)) == 0
        assert await session.scalar(select(func.count()).select_from(PortfolioSnapshot)) == 0
        assert await session.scalar(select(func.count()).select_from(CashLedgerEntry)) == 3


@pytest.mark.asyncio
async def test_order_write_retries_a_retryable_transaction_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = paper_trading_service._lock_user_account
    attempts = 0

    async def fail_once(session: Any, user_id: str) -> Any:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OperationalError("lock account", {}, RetryablePostgreSQLError())
        return await original(session, user_id)

    monkeypatch.setattr(paper_trading_service, "_lock_user_account", fail_once)
    monkeypatch.setattr("app.services.transaction_retry.asyncio.sleep", AsyncMock())

    async with async_session_factory() as session:
        result = await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            market_order(),
            quote(),
        )

    assert result.status == "filled"
    assert attempts == 2
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PaperOrder)) == 1
