import asyncio
from decimal import Decimal

import pytest

from app.core.auth import DEMO_USER_ID
from app.db.session import async_session_factory
from app.services.broker_orders import (
    BrokerOrderCommand,
    BrokerOrderResult,
    BrokerOrderService,
    BrokerOutboxWorker,
)


class BlockingBrokerGateway:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.submit_calls = 0

    async def submit_order(self, command: BrokerOrderCommand) -> BrokerOrderResult:
        self.submit_calls += 1
        self.started.set()
        await asyncio.wait_for(self.release.wait(), timeout=5)
        return BrokerOrderResult(broker_order_id=f"broker-{command.client_order_id}")

    async def find_order(self, client_order_id: str) -> BrokerOrderResult | None:
        return None

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        raise AssertionError(f"예상하지 않은 취소 호출입니다: {broker_order_id}")


@pytest.mark.asyncio
async def test_skip_locked_workers_do_not_submit_same_outbox_event_twice() -> None:
    service = BrokerOrderService()
    async with async_session_factory() as session:
        await service.create_order(
            session,
            DEMO_USER_ID,
            BrokerOrderCommand(
                client_order_id="postgres-outbox-0001",
                symbol="QQQM",
                side="buy",
                order_type="market",
                quantity=Decimal("1"),
            ),
        )

    gateway = BlockingBrokerGateway()
    first_worker = BrokerOutboxWorker(gateway)
    second_worker = BrokerOutboxWorker(gateway)
    async with async_session_factory() as first_session, async_session_factory() as second_session:
        first = asyncio.create_task(first_worker.process_next(first_session))
        await asyncio.wait_for(gateway.started.wait(), timeout=5)
        second_result = await asyncio.wait_for(second_worker.process_next(second_session), timeout=5)
        gateway.release.set()
        first_result = await asyncio.wait_for(first, timeout=5)

    assert first_result is not None
    assert second_result is None
    assert gateway.submit_calls == 1
