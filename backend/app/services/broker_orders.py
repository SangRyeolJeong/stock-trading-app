from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker import BrokerOrder, BrokerOutboxEvent
from app.services.paper_trading import PaperTradingService


@dataclass(frozen=True, slots=True)
class BrokerOrderCommand:
    client_order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: Decimal
    limit_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class BrokerOrderResult:
    broker_order_id: str
    status: Literal["submitted", "cancelled"] = "submitted"


class BrokerGateway(Protocol):
    async def submit_order(self, command: BrokerOrderCommand) -> BrokerOrderResult: ...

    async def find_order(self, client_order_id: str) -> BrokerOrderResult | None: ...

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult: ...


class BrokerOrderError(RuntimeError):
    pass


class BrokerOrderConflictError(BrokerOrderError):
    pass


class BrokerInvalidStateError(BrokerOrderError):
    pass


class BrokerTransientError(BrokerOrderError):
    pass


class BrokerResponseUnknownError(BrokerOrderError):
    pass


class BrokerOrderService:
    def __init__(self) -> None:
        self.paper_accounts = PaperTradingService()

    @staticmethod
    def _matches(order: BrokerOrder, command: BrokerOrderCommand) -> bool:
        return (
            order.symbol == command.symbol.strip().upper()
            and order.side == command.side
            and order.order_type == command.order_type
            and order.quantity == command.quantity
            and order.limit_price == command.limit_price
        )

    async def _add_outbox_event(
        self,
        session: AsyncSession,
        order_id: UUID,
        event_type: str,
    ) -> BrokerOutboxEvent:
        event = BrokerOutboxEvent(order_id=order_id, event_type=event_type)
        session.add(event)
        await session.flush()
        return event

    async def create_order(
        self,
        session: AsyncSession,
        user_id: str,
        command: BrokerOrderCommand,
    ) -> BrokerOrder:
        async with session.begin():
            account = await self.paper_accounts.ensure_user_account(session, user_id)
            existing = await session.scalar(
                select(BrokerOrder).where(
                    BrokerOrder.account_id == account.id,
                    BrokerOrder.client_order_id == command.client_order_id,
                )
            )
            if existing is not None:
                if not self._matches(existing, command):
                    raise BrokerOrderConflictError(
                        "같은 client order ID가 다른 주문에 이미 사용됐습니다."
                    )
                return existing

            order = BrokerOrder(
                account_id=account.id,
                client_order_id=command.client_order_id,
                symbol=command.symbol.strip().upper(),
                side=command.side,
                order_type=command.order_type,
                quantity=command.quantity,
                limit_price=command.limit_price,
                status="pending_submission",
            )
            session.add(order)
            await session.flush()
            await self._add_outbox_event(session, order.id, "submit_order")
            await session.refresh(order)
            return order

    async def request_cancel(
        self,
        session: AsyncSession,
        user_id: str,
        order_id: UUID,
    ) -> BrokerOrder:
        async with session.begin():
            account_id = self.paper_accounts.account_id_for_user(user_id)
            order = await session.scalar(
                select(BrokerOrder)
                .where(BrokerOrder.id == order_id, BrokerOrder.account_id == account_id)
                .with_for_update()
            )
            if order is None:
                raise BrokerInvalidStateError("브로커 주문을 찾을 수 없습니다.")
            if order.status in {"cancel_pending", "cancelled"}:
                return order
            if order.status != "submitted" or order.broker_order_id is None:
                raise BrokerInvalidStateError("제출이 확인된 주문만 취소할 수 있습니다.")
            order.status = "cancel_pending"
            await self._add_outbox_event(session, order.id, "cancel_order")
            await session.flush()
            return order


class BrokerOutboxWorker:
    def __init__(self, gateway: BrokerGateway, *, max_attempts: int = 3) -> None:
        self.gateway = gateway
        self.max_attempts = max_attempts

    async def process_next(self, session: AsyncSession) -> UUID | None:
        async with session.begin():
            event = await session.scalar(
                select(BrokerOutboxEvent)
                .where(
                    BrokerOutboxEvent.status == "pending",
                    BrokerOutboxEvent.next_attempt_at <= func.now(),
                )
                .order_by(BrokerOutboxEvent.created_at, BrokerOutboxEvent.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if event is None:
                return None
            order = await session.scalar(
                select(BrokerOrder)
                .where(BrokerOrder.id == event.order_id)
                .with_for_update()
            )
            assert order is not None
            event.attempt_count += 1
            if event.event_type == "submit_order":
                await self._submit(event, order)
            else:
                await self._cancel(event, order)
            await session.flush()
            return event.id

    async def reconcile_order(self, session: AsyncSession, order_id: UUID) -> bool:
        async with session.begin():
            order = await session.scalar(
                select(BrokerOrder)
                .where(BrokerOrder.id == order_id)
                .with_for_update()
            )
            if order is None:
                return False
            event = await session.scalar(
                select(BrokerOutboxEvent)
                .where(
                    BrokerOutboxEvent.order_id == order.id,
                    BrokerOutboxEvent.status.in_({"pending", "failed"}),
                )
                .order_by(BrokerOutboxEvent.created_at.desc(), BrokerOutboxEvent.id.desc())
                .with_for_update()
                .limit(1)
            )
            if event is None:
                return order.status in {"submitted", "cancelled"}
            result = await self.gateway.find_order(order.client_order_id)
            if result is None or (event.event_type == "cancel_order" and result.status != "cancelled"):
                return False
            order.broker_order_id = result.broker_order_id
            order.status = result.status
            order.last_error = None
            self._complete(event)
            await session.flush()
            return True

    @staticmethod
    def _command(order: BrokerOrder) -> BrokerOrderCommand:
        return BrokerOrderCommand(
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            limit_price=order.limit_price,
        )

    async def _submit(self, event: BrokerOutboxEvent, order: BrokerOrder) -> None:
        try:
            result = await self.gateway.submit_order(self._command(order))
        except BrokerResponseUnknownError:
            result = await self.gateway.find_order(order.client_order_id)
            if result is None:
                self._schedule_retry(event, order, "submission_result_unknown")
                return
        except BrokerTransientError:
            self._schedule_retry(event, order, "broker_temporarily_unavailable")
            return
        self._complete(event)
        order.broker_order_id = result.broker_order_id
        order.status = result.status
        order.last_error = None

    async def _cancel(self, event: BrokerOutboxEvent, order: BrokerOrder) -> None:
        assert order.broker_order_id is not None
        try:
            result = await self.gateway.cancel_order(order.broker_order_id)
        except (BrokerResponseUnknownError, BrokerTransientError):
            known = await self.gateway.find_order(order.client_order_id)
            if known is None or known.status != "cancelled":
                self._schedule_retry(event, order, "cancellation_not_confirmed")
                return
            result = known
        self._complete(event)
        order.status = result.status
        order.last_error = None

    @staticmethod
    def _complete(event: BrokerOutboxEvent) -> None:
        event.status = "processed"
        event.processed_at = datetime.now(UTC)
        event.last_error = None

    def _schedule_retry(
        self,
        event: BrokerOutboxEvent,
        order: BrokerOrder,
        reason: str,
    ) -> None:
        event.last_error = reason
        order.last_error = reason
        if event.attempt_count >= self.max_attempts:
            event.status = "failed"
            order.status = "reconciliation_required"
            return
        event.next_attempt_at = datetime.now(UTC) + timedelta(
            seconds=2 ** (event.attempt_count - 1)
        )


broker_order_service = BrokerOrderService()
