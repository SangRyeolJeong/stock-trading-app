from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, update

from app.core.auth import DEMO_USER_ID
from app.db.session import async_session_factory
from app.models.broker import BrokerOrder, BrokerOutboxEvent
from app.services.broker_orders import (
    BrokerOrderCommand,
    BrokerOrderConflictError,
    BrokerOrderResult,
    BrokerOrderService,
    BrokerOutboxWorker,
    BrokerResponseUnknownError,
    BrokerTransientError,
)


class FakeBrokerGateway:
    def __init__(self) -> None:
        self.orders: dict[str, BrokerOrderResult] = {}
        self.submit_calls = 0
        self.cancel_calls = 0
        self.lose_next_submit_response = False
        self.submit_failures = 0
        self.cancel_failures = 0

    async def submit_order(self, command: BrokerOrderCommand) -> BrokerOrderResult:
        self.submit_calls += 1
        if self.submit_failures:
            self.submit_failures -= 1
            raise BrokerTransientError("temporary submit failure")
        result = self.orders.setdefault(
            command.client_order_id,
            BrokerOrderResult(broker_order_id=f"broker-{command.client_order_id}"),
        )
        if self.lose_next_submit_response:
            self.lose_next_submit_response = False
            raise BrokerResponseUnknownError("response lost after acceptance")
        return result

    async def find_order(self, client_order_id: str) -> BrokerOrderResult | None:
        return self.orders.get(client_order_id)

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        self.cancel_calls += 1
        if self.cancel_failures:
            self.cancel_failures -= 1
            raise BrokerTransientError("temporary cancellation failure")
        client_order_id = broker_order_id.removeprefix("broker-")
        result = BrokerOrderResult(broker_order_id=broker_order_id, status="cancelled")
        self.orders[client_order_id] = result
        return result


def command(client_order_id: str = "client-order-0001") -> BrokerOrderCommand:
    return BrokerOrderCommand(
        client_order_id=client_order_id,
        symbol="QQQM",
        side="buy",
        order_type="market",
        quantity=Decimal("1"),
    )


async def create_order(
    service: BrokerOrderService,
    client_order_id: str = "client-order-0001",
) -> BrokerOrder:
    async with async_session_factory() as session:
        return await service.create_order(session, DEMO_USER_ID, command(client_order_id))


async def process_next(worker: BrokerOutboxWorker) -> object:
    async with async_session_factory() as session:
        return await worker.process_next(session)


async def make_events_due() -> None:
    async with async_session_factory() as session, session.begin():
        await session.execute(
            update(BrokerOutboxEvent)
            .where(BrokerOutboxEvent.status == "pending")
            .values(next_attempt_at=datetime.now(UTC) - timedelta(seconds=1))
        )


@pytest.mark.asyncio
async def test_order_and_submit_event_are_committed_atomically_and_idempotently() -> None:
    service = BrokerOrderService()

    first = await create_order(service)
    second = await create_order(service)

    assert first.id == second.id
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(BrokerOrder)) == 1
        assert await session.scalar(select(func.count()).select_from(BrokerOutboxEvent)) == 1

    changed = command()
    changed = BrokerOrderCommand(
        client_order_id=changed.client_order_id,
        symbol=changed.symbol,
        side=changed.side,
        order_type=changed.order_type,
        quantity=Decimal("2"),
    )
    with pytest.raises(BrokerOrderConflictError):
        async with async_session_factory() as session:
            await service.create_order(session, DEMO_USER_ID, changed)


@pytest.mark.asyncio
async def test_failure_before_commit_leaves_neither_order_nor_outbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = BrokerOrderService()

    async def fail_after_order(*_args: object) -> BrokerOutboxEvent:
        raise RuntimeError("injected failure before commit")

    monkeypatch.setattr(service, "_add_outbox_event", fail_after_order)
    with pytest.raises(RuntimeError):
        async with async_session_factory() as session:
            await service.create_order(session, DEMO_USER_ID, command())

    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(BrokerOrder)) == 0
        assert await session.scalar(select(func.count()).select_from(BrokerOutboxEvent)) == 0


@pytest.mark.asyncio
async def test_worker_submits_once_and_ignores_processed_event() -> None:
    service = BrokerOrderService()
    gateway = FakeBrokerGateway()
    worker = BrokerOutboxWorker(gateway)
    order = await create_order(service)

    assert await process_next(worker) is not None
    assert await process_next(worker) is None

    async with async_session_factory() as session:
        stored = await session.get(BrokerOrder, order.id)
        event = await session.scalar(select(BrokerOutboxEvent))
    assert stored is not None and stored.status == "submitted"
    assert stored.broker_order_id == "broker-client-order-0001"
    assert event is not None and event.status == "processed"
    assert gateway.submit_calls == 1


@pytest.mark.asyncio
async def test_lost_submit_response_is_resolved_by_client_order_id_reconciliation() -> None:
    service = BrokerOrderService()
    gateway = FakeBrokerGateway()
    gateway.lose_next_submit_response = True
    worker = BrokerOutboxWorker(gateway)
    order = await create_order(service)

    await process_next(worker)

    async with async_session_factory() as session:
        stored = await session.get(BrokerOrder, order.id)
        event = await session.scalar(select(BrokerOutboxEvent))
    assert stored is not None and stored.status == "submitted"
    assert event is not None and event.status == "processed"
    assert gateway.submit_calls == 1


@pytest.mark.asyncio
async def test_repeated_submit_failure_requires_reconciliation_after_limit() -> None:
    service = BrokerOrderService()
    gateway = FakeBrokerGateway()
    gateway.submit_failures = 3
    worker = BrokerOutboxWorker(gateway, max_attempts=3)
    order = await create_order(service)

    for _ in range(3):
        await process_next(worker)
        await make_events_due()

    async with async_session_factory() as session:
        stored = await session.get(BrokerOrder, order.id)
        event = await session.scalar(select(BrokerOutboxEvent))
    assert stored is not None and stored.status == "reconciliation_required"
    assert event is not None and event.status == "failed"
    assert event.attempt_count == 3

    gateway.orders["client-order-0001"] = BrokerOrderResult(
        broker_order_id="broker-client-order-0001"
    )
    async with async_session_factory() as session:
        assert await worker.reconcile_order(session, order.id) is True
    async with async_session_factory() as session:
        reconciled = await session.get(BrokerOrder, order.id)
        reconciled_event = await session.scalar(select(BrokerOutboxEvent))
    assert reconciled is not None and reconciled.status == "submitted"
    assert reconciled_event is not None and reconciled_event.status == "processed"


@pytest.mark.asyncio
async def test_cancel_failure_is_best_effort_and_later_reconciled() -> None:
    service = BrokerOrderService()
    gateway = FakeBrokerGateway()
    worker = BrokerOutboxWorker(gateway)
    order = await create_order(service)
    await process_next(worker)

    async with async_session_factory() as session:
        pending_cancel = await service.request_cancel(session, DEMO_USER_ID, order.id)
    async with async_session_factory() as session:
        repeated_cancel = await service.request_cancel(session, DEMO_USER_ID, order.id)
    assert pending_cancel.status == "cancel_pending"
    assert repeated_cancel.status == "cancel_pending"
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(BrokerOutboxEvent)) == 2

    gateway.cancel_failures = 1
    await process_next(worker)
    await make_events_due()
    await process_next(worker)

    async with async_session_factory() as session:
        stored = await session.get(BrokerOrder, order.id)
        events = list(await session.scalars(select(BrokerOutboxEvent)))
    assert stored is not None and stored.status == "cancelled"
    assert len(events) == 2
    assert all(event.status == "processed" for event in events)
    assert gateway.cancel_calls == 2
