import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import DEMO_USER_ID
from app.db.session import async_session_factory
from app.models.paper import (
    CashLedgerEntry,
    PaperAccount,
    PaperExecution,
    PaperOrder,
    PaperOrderStatusEvent,
    Position,
)
from app.schemas.market import Quote
from app.schemas.paper import PaperOrder as PaperOrderSchema
from app.schemas.paper import PaperOrderRequest
from app.services.paper_trading import (
    IdempotencyConflictError,
    InsufficientCashError,
    InsufficientPositionError,
    InvalidOrderStateError,
    PaperTradingService,
    paper_trading_service,
)

LockAccount = Callable[[AsyncSession, str], Awaitable[PaperAccount]]


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


def order_request(
    key: str,
    *,
    side: str = "buy",
    quantity: str = "1",
    order_type: str = "market",
    limit_price: str | None = None,
) -> PaperOrderRequest:
    return PaperOrderRequest.model_validate(
        {
            "symbol": "QQQM",
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "limit_price": limit_price,
            "idempotency_key": key,
        }
    )


async def execute(request: PaperOrderRequest, market_quote: Quote) -> PaperOrderSchema:
    async with async_session_factory() as session:
        existing = await paper_trading_service.get_idempotent_order(
            session,
            DEMO_USER_ID,
            request,
        )
        if existing is not None:
            return existing
        return await paper_trading_service.execute_immediately(
            session,
            DEMO_USER_ID,
            request,
            market_quote,
        )


async def ensure_demo_account() -> None:
    async with async_session_factory() as session, session.begin():
        await paper_trading_service.ensure_user_account(session, DEMO_USER_ID)


def synchronize_next_two_account_locks(monkeypatch: pytest.MonkeyPatch) -> None:
    original: LockAccount = paper_trading_service._lock_user_account
    both_ready = asyncio.Event()
    ready_count = 0

    async def synchronized(session: AsyncSession, user_id: str) -> PaperAccount:
        nonlocal ready_count
        ready_count += 1
        if ready_count == 2:
            both_ready.set()
        await asyncio.wait_for(both_ready.wait(), timeout=5)
        return await original(session, user_id)

    monkeypatch.setattr(paper_trading_service, "_lock_user_account", synchronized)


async def assert_ledger_invariants() -> None:
    async with async_session_factory() as session:
        negative_cash = await session.scalar(
            select(func.count())
            .select_from(
                select(CashLedgerEntry.account_id, CashLedgerEntry.currency)
                .group_by(CashLedgerEntry.account_id, CashLedgerEntry.currency)
                .having(func.sum(CashLedgerEntry.amount) < 0)
                .subquery()
            )
        )
        negative_positions = await session.scalar(
            select(func.count()).select_from(Position).where(Position.quantity < 0)
        )
        order_counts = (
            await session.execute(
                select(
                    func.coalesce(func.sum(case((PaperOrder.status == "filled", 1), else_=0)), 0),
                    func.count(PaperExecution.id),
                    func.count(PaperExecution.id).filter(PaperOrder.status != "filled"),
                ).select_from(PaperOrder).outerjoin(PaperExecution, PaperExecution.order_id == PaperOrder.id)
            )
        ).one()

    assert negative_cash == 0
    assert negative_positions == 0
    assert order_counts[0] == order_counts[1]
    assert order_counts[2] == 0


@pytest.mark.asyncio
async def test_concurrent_buys_cannot_spend_the_same_cash_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await ensure_demo_account()
    synchronize_next_two_account_locks(monkeypatch)

    results = await asyncio.gather(
        execute(order_request("postgres-buy-0001"), quote("6000")),
        execute(order_request("postgres-buy-0002"), quote("6000")),
        return_exceptions=True,
    )

    assert sum(isinstance(result, PaperOrderSchema) for result in results) == 1
    assert sum(isinstance(result, InsufficientCashError) for result in results) == 1
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PaperOrder)) == 1
        usd_cash = await session.scalar(
            select(func.sum(CashLedgerEntry.amount)).where(CashLedgerEntry.currency == "USD")
        )
        assert usd_cash == Decimal("3994.00000000")
    await assert_ledger_invariants()


@pytest.mark.asyncio
async def test_concurrent_sells_cannot_use_the_same_position_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await execute(order_request("postgres-seed-buy"), quote())
    synchronize_next_two_account_locks(monkeypatch)

    results = await asyncio.gather(
        execute(order_request("postgres-sell-0001", side="sell"), quote("110")),
        execute(order_request("postgres-sell-0002", side="sell"), quote("110")),
        return_exceptions=True,
    )

    assert sum(isinstance(result, PaperOrderSchema) for result in results) == 1
    assert sum(isinstance(result, InsufficientPositionError) for result in results) == 1
    async with async_session_factory() as session:
        position = await session.scalar(select(Position))
        assert position is not None
        assert position.quantity == Decimal("0E-8")
        assert await session.scalar(select(func.count()).select_from(PaperExecution)) == 2
    await assert_ledger_invariants()


@pytest.mark.asyncio
async def test_same_idempotency_key_concurrently_returns_one_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await ensure_demo_account()
    synchronize_next_two_account_locks(monkeypatch)
    request = order_request("postgres-idempotency-0001")

    first, second = await asyncio.gather(execute(request, quote()), execute(request, quote()))

    assert first.id == second.id
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PaperOrder)) == 1
        assert await session.scalar(select(func.count()).select_from(PaperExecution)) == 1
        trade_entries = await session.scalar(
            select(func.count()).select_from(CashLedgerEntry).where(CashLedgerEntry.order_id == first.id)
        )
        assert trade_entries == 2
    await assert_ledger_invariants()


@pytest.mark.asyncio
async def test_same_idempotency_key_with_different_requests_concurrently_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await ensure_demo_account()
    synchronize_next_two_account_locks(monkeypatch)

    results = await asyncio.gather(
        execute(order_request("postgres-idempotency-conflict", quantity="1"), quote()),
        execute(order_request("postgres-idempotency-conflict", quantity="2"), quote()),
        return_exceptions=True,
    )

    assert sum(isinstance(result, PaperOrderSchema) for result in results) == 1
    assert sum(isinstance(result, IdempotencyConflictError) for result in results) == 1
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PaperOrder)) == 1
        assert await session.scalar(select(func.count()).select_from(PaperExecution)) == 1
    await assert_ledger_invariants()


@pytest.mark.asyncio
async def test_pending_fill_and_cancel_cannot_both_win(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = await execute(
        order_request(
            "postgres-pending-0001",
            order_type="limit",
            limit_price="90",
        ),
        quote("100"),
    )
    synchronize_next_two_account_locks(monkeypatch)

    async def fill() -> bool:
        async with async_session_factory() as session:
            return await paper_trading_service.try_fill_pending_order(
                session,
                DEMO_USER_ID,
                pending.id,
                quote("89"),
            )

    async def cancel() -> PaperOrderSchema:
        async with async_session_factory() as session:
            return await paper_trading_service.cancel_order(session, DEMO_USER_ID, pending.id)

    fill_result, cancel_result = await asyncio.gather(fill(), cancel(), return_exceptions=True)

    async with async_session_factory() as session:
        stored = await session.get(PaperOrder, pending.id)
        execution_count = await session.scalar(
            select(func.count()).select_from(PaperExecution).where(PaperExecution.order_id == pending.id)
        )
        events = list(
            await session.scalars(
                select(PaperOrderStatusEvent)
                .where(PaperOrderStatusEvent.order_id == pending.id)
                .order_by(PaperOrderStatusEvent.sequence)
            )
        )
    assert stored is not None
    assert [event.new_status for event in events] == ["accepted", stored.status]
    if stored.status == "filled":
        assert fill_result is True
        assert isinstance(cancel_result, InvalidOrderStateError)
        assert execution_count == 1
    else:
        assert stored.status == "cancelled"
        assert fill_result is False
        assert isinstance(cancel_result, PaperOrderSchema)
        assert execution_count == 0
    await assert_ledger_invariants()


@pytest.mark.asyncio
async def test_concurrent_first_account_creation_has_one_initial_deposit_per_currency() -> None:
    user_id = "postgres-first-account-user"

    async def create_account() -> PaperAccount:
        async with async_session_factory() as session, session.begin():
            return await paper_trading_service.ensure_user_account(session, user_id)

    first, second = await asyncio.gather(create_account(), create_account())

    assert first.id == second.id == PaperTradingService.account_id_for_user(user_id)
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PaperAccount)) == 1
        entries = (
            await session.execute(
                select(CashLedgerEntry.currency, CashLedgerEntry.amount)
                .where(CashLedgerEntry.entry_type == "initial_deposit")
                .order_by(CashLedgerEntry.currency)
            )
        ).all()
    assert entries == [("KRW", Decimal("10000000.00000000")), ("USD", Decimal("10000.00000000"))]
    await assert_ledger_invariants()
