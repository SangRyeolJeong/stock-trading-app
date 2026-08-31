import json
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import DEMO_USER_ID
from app.core.config import get_settings
from app.models.paper import (
    CashLedgerEntry,
    PaperAccount,
    PaperExecution,
    PaperOrder,
    PaperOrderStatusEvent,
    PortfolioSnapshot,
    Position,
    Security,
)
from app.schemas.market import Quote
from app.schemas.paper import (
    CashBalance,
    PaperOrderRequest,
)
from app.schemas.paper import (
    PaperAccount as PaperAccountSchema,
)
from app.schemas.paper import (
    PaperOrder as PaperOrderSchema,
)
from app.schemas.paper import PaperOrderStatusEvent as PaperOrderStatusEventSchema
from app.schemas.paper import (
    Position as PositionSchema,
)
from app.services.paper_order_state import (
    InvalidOrderStateError,
    record_order_creation,
    transition_order,
)

MONEY_QUANTUM = Decimal("0.00000001")
ZERO = Decimal("0")
DEMO_ACCOUNT_ID = "demo-account"
ORDER_FINGERPRINT_VERSION = 1


class PaperTradingError(RuntimeError):
    status_code = 400


class InsufficientCashError(PaperTradingError):
    status_code = 422


class InsufficientPositionError(PaperTradingError):
    status_code = 422


class IdempotencyConflictError(PaperTradingError):
    status_code = 409


class AccountNotFoundError(PaperTradingError):
    status_code = 404


@dataclass(frozen=True)
class SettlementAmounts:
    fill_price: Decimal
    gross_amount: Decimal
    fee: Decimal
    current_cash: Decimal


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _canonical_decimal(value: Decimal) -> str:
    return format(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP), "f")


def order_request_fingerprint(request: PaperOrderRequest) -> str:
    payload = json.dumps(
        {
            "limit_price": (
                _canonical_decimal(request.limit_price)
                if request.limit_price is not None
                else None
            ),
            "order_type": request.order_type,
            "quantity": _canonical_decimal(request.quantity),
            "side": request.side,
            "symbol": request.symbol,
            "version": ORDER_FINGERPRINT_VERSION,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


class PaperTradingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.initial_balances = {
            "KRW": money(settings.paper_initial_krw),
            "USD": money(settings.paper_initial_usd),
        }
        self.fee_rate = settings.paper_fee_rate

    @staticmethod
    def account_id_for_user(user_id: str) -> str:
        if user_id == DEMO_USER_ID:
            return DEMO_ACCOUNT_ID
        digest = sha256(user_id.encode("utf-8")).hexdigest()[:32]
        return f"paper-{digest}"

    async def ensure_user_account(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> PaperAccount:
        account = await session.scalar(
            select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .order_by(PaperAccount.created_at)
        )
        if account is not None:
            return account

        account_id = self.account_id_for_user(user_id)
        values = {
            "id": account_id,
            "user_id": user_id,
            "name": "MOA 모의투자",
            "base_currency": "KRW",
            "status": "active",
        }
        dialect_name = session.get_bind().dialect.name
        if dialect_name == "postgresql":
            statement = (
                postgresql_insert(PaperAccount)
                .values(**values)
                .on_conflict_do_nothing()
                .returning(PaperAccount.id)
            )
        elif dialect_name == "sqlite":
            statement = (
                sqlite_insert(PaperAccount)
                .values(**values)
                .on_conflict_do_nothing()
                .returning(PaperAccount.id)
            )
        else:
            raise RuntimeError(f"지원하지 않는 원장 데이터베이스입니다: {dialect_name}")

        inserted_account_id = await session.scalar(statement)
        if inserted_account_id is not None:
            for currency, balance in self.initial_balances.items():
                session.add(
                    CashLedgerEntry(
                        account_id=inserted_account_id,
                        currency=currency,
                        entry_type="initial_deposit",
                        amount=balance,
                        balance_after=balance,
                    )
                )
            await session.flush()

        account = await session.scalar(
            select(PaperAccount).where(PaperAccount.user_id == user_id)
        )
        if account is None:
            raise AccountNotFoundError("모의 계좌를 생성하지 못했습니다.")
        return account

    async def _lock_user_account(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> PaperAccount:
        account = await self.ensure_user_account(session, user_id)
        locked_account = await session.scalar(
            select(PaperAccount)
            .where(PaperAccount.id == account.id, PaperAccount.user_id == user_id)
            .with_for_update(of=PaperAccount)
        )
        if locked_account is None:
            raise AccountNotFoundError("모의 계좌를 찾을 수 없습니다.")
        return locked_account

    async def _cash_balance(self, session: AsyncSession, account_id: str, currency: str) -> Decimal:
        value = await session.scalar(
            select(func.coalesce(func.sum(CashLedgerEntry.amount), ZERO)).where(
                CashLedgerEntry.account_id == account_id,
                CashLedgerEntry.currency == currency,
            )
        )
        return money(Decimal(value or ZERO))

    async def _cash_balances(self, session: AsyncSession, account_id: str) -> list[CashBalance]:
        rows = (
            await session.execute(
                select(CashLedgerEntry.currency, func.sum(CashLedgerEntry.amount))
                .where(CashLedgerEntry.account_id == account_id)
                .group_by(CashLedgerEntry.currency)
                .order_by(CashLedgerEntry.currency)
            )
        ).all()
        return [CashBalance(currency=currency, amount=money(Decimal(amount))) for currency, amount in rows]

    @staticmethod
    def _order_query() -> Select[tuple[PaperOrder, PaperExecution | None, Security]]:
        return (
            select(PaperOrder, PaperExecution, Security)
            .outerjoin(PaperExecution, PaperExecution.order_id == PaperOrder.id)
            .join(Security, Security.symbol == PaperOrder.security_symbol)
        )

    @staticmethod
    def _order_schema(
        order: PaperOrder,
        execution: PaperExecution | None,
        security: Security,
    ) -> PaperOrderSchema:
        return PaperOrderSchema(
            id=order.id,
            account_id=order.account_id,
            idempotency_key=order.idempotency_key,
            status=order.status,
            symbol=security.symbol,
            name=security.name,
            currency=security.currency,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            limit_price=order.requested_price,
            filled_price=execution.price if execution else None,
            gross_amount=execution.gross_amount if execution else None,
            fee=execution.fee if execution else None,
            realized_pnl=execution.realized_pnl if execution else None,
            created_at=order.created_at,
        )

    async def _find_idempotent_order(
        self,
        session: AsyncSession,
        account_id: str,
        request: PaperOrderRequest,
        fingerprint: str,
    ) -> PaperOrderSchema | None:
        row = (
            await session.execute(
                self._order_query().where(
                    PaperOrder.account_id == account_id,
                    PaperOrder.idempotency_key == request.idempotency_key,
                )
            )
        ).one_or_none()
        if row is None:
            return None
        order, execution, security = row
        if order.request_fingerprint != fingerprint:
            raise IdempotencyConflictError("같은 멱등성 키가 다른 주문에 이미 사용됐습니다.")
        return self._order_schema(order, execution, security)

    async def get_idempotent_order(
        self,
        session: AsyncSession,
        user_id: str,
        request: PaperOrderRequest,
    ) -> PaperOrderSchema | None:
        fingerprint = order_request_fingerprint(request)
        async with session.begin():
            return await self._find_idempotent_order(
                session,
                self.account_id_for_user(user_id),
                request,
                fingerprint,
            )

    @staticmethod
    def _limit_is_marketable(side: str, limit_price: Decimal, market_price: Decimal) -> bool:
        if side == "buy":
            return limit_price >= market_price
        return limit_price <= market_price

    async def _reserved_resources(
        self,
        session: AsyncSession,
        account_id: str,
        currency: str,
        symbol: str,
        exclude_order_id: UUID | None = None,
    ) -> tuple[Decimal, Decimal]:
        statement = (
            select(PaperOrder, Security)
            .join(Security, Security.symbol == PaperOrder.security_symbol)
            .where(PaperOrder.account_id == account_id, PaperOrder.status == "accepted")
        )
        if exclude_order_id is not None:
            statement = statement.where(PaperOrder.id != exclude_order_id)
        rows = (await session.execute(statement)).all()
        reserved_cash = ZERO
        reserved_quantity = ZERO
        for order, security in rows:
            if order.side == "buy" and security.currency == currency and order.requested_price is not None:
                gross = order.requested_price * order.quantity
                reserved_cash += gross + gross * self.fee_rate
            elif order.side == "sell" and security.symbol == symbol:
                reserved_quantity += order.quantity
        return money(reserved_cash), reserved_quantity

    async def _validate_resources(
        self,
        session: AsyncSession,
        order: PaperOrder,
        currency: str,
        price: Decimal,
        exclude_order_id: UUID | None = None,
    ) -> None:
        reserved_cash, reserved_quantity = await self._reserved_resources(
            session,
            order.account_id,
            currency,
            order.security_symbol,
            exclude_order_id,
        )
        gross_amount = money(price * order.quantity)
        fee = money(gross_amount * self.fee_rate)
        if order.side == "buy":
            current_cash = await self._cash_balance(session, order.account_id, currency)
            available_cash = money(current_cash - reserved_cash)
            if available_cash < gross_amount + fee:
                raise InsufficientCashError(
                    f"주문 가능 현금이 부족합니다. 필요 {gross_amount + fee} {currency}, "
                    f"가용 {available_cash} {currency}"
                )
            return

        position = await session.scalar(
            select(Position)
            .where(
                Position.account_id == order.account_id,
                Position.security_symbol == order.security_symbol,
            )
            .with_for_update()
        )
        held_quantity = position.quantity if position else ZERO
        available_quantity = held_quantity - reserved_quantity
        if available_quantity < order.quantity:
            raise InsufficientPositionError(
                f"보유 수량이 부족합니다. 주문 {order.quantity}주, 가용 {available_quantity}주"
            )

    async def _settle_order(
        self,
        session: AsyncSession,
        order: PaperOrder,
        quote: Quote,
    ) -> PaperExecution:
        fill_price = money(quote.price)
        await self._validate_resources(
            session,
            order,
            quote.currency,
            fill_price,
            exclude_order_id=order.id,
        )
        gross_amount = money(fill_price * order.quantity)
        amounts = SettlementAmounts(
            fill_price=fill_price,
            gross_amount=gross_amount,
            fee=money(gross_amount * self.fee_rate),
            current_cash=await self._cash_balance(session, order.account_id, quote.currency),
        )
        realized_pnl, trade_amount = await self._apply_position_change(
            session,
            order,
            quote,
            amounts,
        )
        execution = await self._record_execution(
            session,
            order,
            amounts,
            realized_pnl,
        )
        balance_after_trade = await self._record_trade_settlement(
            session,
            order,
            quote.currency,
            amounts.current_cash,
            trade_amount,
        )
        final_balance = await self._record_commission(
            session,
            order,
            quote.currency,
            balance_after_trade,
            amounts.fee,
        )
        await session.flush()
        await self._record_portfolio_snapshot(
            session,
            order,
            quote.currency,
            final_balance,
        )
        await session.flush()
        return execution

    async def _apply_position_change(
        self,
        session: AsyncSession,
        order: PaperOrder,
        quote: Quote,
        amounts: SettlementAmounts,
    ) -> tuple[Decimal, Decimal]:
        position = await session.scalar(
            select(Position)
            .where(
                Position.account_id == order.account_id,
                Position.security_symbol == quote.symbol,
            )
            .with_for_update()
        )
        held_quantity = position.quantity if position else ZERO

        realized_pnl = ZERO
        if order.side == "buy":
            new_quantity = held_quantity + order.quantity
            previous_cost = held_quantity * (position.average_cost if position else ZERO)
            new_average_cost = money((previous_cost + amounts.gross_amount) / new_quantity)
            if position is None:
                position = Position(
                    account_id=order.account_id,
                    security_symbol=quote.symbol,
                    quantity=new_quantity,
                    average_cost=new_average_cost,
                    realized_pnl=ZERO,
                )
                session.add(position)
            else:
                position.quantity = new_quantity
                position.average_cost = new_average_cost
            trade_amount = -amounts.gross_amount
        else:
            assert position is not None
            realized_pnl = money(
                (amounts.fill_price - position.average_cost) * order.quantity - amounts.fee
            )
            position.quantity = held_quantity - order.quantity
            position.realized_pnl = money(position.realized_pnl + realized_pnl)
            trade_amount = amounts.gross_amount

        return realized_pnl, trade_amount

    async def _record_execution(
        self,
        session: AsyncSession,
        order: PaperOrder,
        amounts: SettlementAmounts,
        realized_pnl: Decimal,
    ) -> PaperExecution:
        execution = PaperExecution(
            order_id=order.id,
            quantity=order.quantity,
            price=amounts.fill_price,
            gross_amount=amounts.gross_amount,
            fee=amounts.fee,
            realized_pnl=realized_pnl,
        )
        session.add(execution)
        transition_order(
            session,
            order,
            "filled",
            reason="order_filled",
        )
        return execution

    async def _record_trade_settlement(
        self,
        session: AsyncSession,
        order: PaperOrder,
        currency: str,
        current_cash: Decimal,
        trade_amount: Decimal,
    ) -> Decimal:
        balance_after_trade = money(current_cash + trade_amount)
        session.add(
            CashLedgerEntry(
                account_id=order.account_id,
                order_id=order.id,
                currency=currency,
                entry_type="trade_settlement",
                amount=trade_amount,
                balance_after=balance_after_trade,
            )
        )
        return balance_after_trade

    async def _record_commission(
        self,
        session: AsyncSession,
        order: PaperOrder,
        currency: str,
        balance_after_trade: Decimal,
        fee: Decimal,
    ) -> Decimal:
        final_balance = money(balance_after_trade - fee)
        session.add(
            CashLedgerEntry(
                account_id=order.account_id,
                order_id=order.id,
                currency=currency,
                entry_type="commission",
                amount=-fee,
                balance_after=final_balance,
            )
        )
        return final_balance

    async def _record_portfolio_snapshot(
        self,
        session: AsyncSession,
        order: PaperOrder,
        currency: str,
        final_balance: Decimal,
    ) -> None:
        positions_value = await session.scalar(
            select(func.coalesce(func.sum(Position.quantity * Position.average_cost), ZERO))
            .join(Security, Security.symbol == Position.security_symbol)
            .where(Position.account_id == order.account_id, Security.currency == currency)
        )
        positions_value = money(Decimal(positions_value or ZERO))
        session.add(
            PortfolioSnapshot(
                account_id=order.account_id,
                currency=currency,
                cash_value=final_balance,
                positions_value=positions_value,
                total_value=money(final_balance + positions_value),
            )
        )

    async def _create_order(
        self,
        session: AsyncSession,
        account_id: str,
        request: PaperOrderRequest,
        quote: Quote,
        request_fingerprint: str,
    ) -> PaperOrder:
        order = PaperOrder(
            account_id=account_id,
            security_symbol=quote.symbol,
            idempotency_key=request.idempotency_key,
            request_fingerprint=request_fingerprint,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            requested_price=request.limit_price,
            status="accepted",
        )
        session.add(order)
        await session.flush()
        record_order_creation(session, order)
        await session.flush()
        return order

    async def execute_immediately(
        self,
        session: AsyncSession,
        user_id: str,
        request: PaperOrderRequest,
        quote: Quote,
    ) -> PaperOrderSchema:
        fingerprint = order_request_fingerprint(request)
        async with session.begin():
            account = await self._lock_user_account(session, user_id)

            existing = await self._find_idempotent_order(
                session,
                account.id,
                request,
                fingerprint,
            )
            if existing is not None:
                return existing

            security = await session.get(Security, quote.symbol)
            if security is None:
                security = Security(
                    symbol=quote.symbol,
                    name=quote.name,
                    currency=quote.currency,
                    market="KRX" if quote.currency == "KRW" else "NASDAQ",
                )
                session.add(security)
                await session.flush()
            else:
                security.name = quote.name
                security.currency = quote.currency

            should_fill = request.order_type == "market" or (
                request.limit_price is not None
                and self._limit_is_marketable(request.side, request.limit_price, quote.price)
            )
            order = await self._create_order(
                session,
                account.id,
                request,
                quote,
                fingerprint,
            )
            if not should_fill:
                assert request.limit_price is not None
                await self._validate_resources(
                    session,
                    order,
                    quote.currency,
                    request.limit_price,
                    exclude_order_id=order.id,
                )
                await session.refresh(order)
                return self._order_schema(order, None, security)

            execution = await self._settle_order(session, order, quote)
            await session.refresh(order)
            await session.refresh(execution)
            return self._order_schema(order, execution, security)

    async def list_pending_order_refs(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[tuple[UUID, str]]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            rows = (
                await session.execute(
                    select(PaperOrder.id, PaperOrder.security_symbol).where(
                        PaperOrder.account_id == account.id,
                        PaperOrder.status == "accepted",
                    )
                )
            ).all()
            return list(rows)

    async def try_fill_pending_order(
        self,
        session: AsyncSession,
        user_id: str,
        order_id: UUID,
        quote: Quote,
    ) -> bool:
        async with session.begin():
            account = await self._lock_user_account(session, user_id)
            order = await session.scalar(
                select(PaperOrder)
                .where(
                    PaperOrder.id == order_id,
                    PaperOrder.account_id == account.id,
                )
                .with_for_update(of=PaperOrder)
            )
            if (
                order is None
                or order.status != "accepted"
                or order.requested_price is None
                or not self._limit_is_marketable(order.side, order.requested_price, quote.price)
            ):
                return False
            try:
                await self._settle_order(session, order, quote)
            except (InsufficientCashError, InsufficientPositionError):
                transition_order(
                    session,
                    order,
                    "rejected",
                    reason="resources_unavailable_at_fill",
                )
                await session.flush()
            return True

    async def cancel_order(
        self,
        session: AsyncSession,
        user_id: str,
        order_id: UUID,
    ) -> PaperOrderSchema:
        async with session.begin():
            account = await self._lock_user_account(session, user_id)
            order = await session.scalar(
                select(PaperOrder)
                .where(
                    PaperOrder.id == order_id,
                    PaperOrder.account_id == account.id,
                )
                .with_for_update(of=PaperOrder)
            )
            if order is None:
                raise AccountNotFoundError("주문을 찾을 수 없습니다.")
            row = (
                await session.execute(
                    self._order_query().where(PaperOrder.id == order.id)
                )
            ).one()
            order, execution, security = row
            if order.status == "cancelled":
                return self._order_schema(order, execution, security)
            if order.status != "accepted":
                raise InvalidOrderStateError("대기 중인 지정가 주문만 취소할 수 있습니다.")
            transition_order(
                session,
                order,
                "cancelled",
                reason="user_cancelled",
            )
            await session.flush()
            await session.refresh(order)
            return self._order_schema(order, execution, security)

    async def list_accounts(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[PaperAccountSchema]:
        async with session.begin():
            await self.ensure_user_account(session, user_id)
            accounts = (
                await session.scalars(
                    select(PaperAccount)
                    .where(PaperAccount.user_id == user_id)
                    .order_by(PaperAccount.created_at)
                )
            ).all()
            return [
                PaperAccountSchema(
                    id=account.id,
                    name=account.name,
                    base_currency=account.base_currency,
                    cash_balances=await self._cash_balances(session, account.id),
                    created_at=account.created_at,
                )
                for account in accounts
            ]

    async def list_orders(
        self,
        session: AsyncSession,
        user_id: str,
        limit: int = 100,
    ) -> list[PaperOrderSchema]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            rows = (
                await session.execute(
                    self._order_query()
                    .where(PaperOrder.account_id == account.id)
                    .order_by(PaperOrder.created_at.desc())
                    .limit(limit)
                )
            ).all()
            return [self._order_schema(*row) for row in rows]

    async def list_order_status_events(
        self,
        session: AsyncSession,
        user_id: str,
        order_id: UUID,
    ) -> list[PaperOrderStatusEventSchema]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            order = await session.scalar(
                select(PaperOrder).where(
                    PaperOrder.id == order_id,
                    PaperOrder.account_id == account.id,
                )
            )
            if order is None:
                raise AccountNotFoundError("주문을 찾을 수 없습니다.")
            events = list(
                await session.scalars(
                    select(PaperOrderStatusEvent)
                    .where(PaperOrderStatusEvent.order_id == order.id)
                    .order_by(PaperOrderStatusEvent.sequence)
                )
            )
            return [PaperOrderStatusEventSchema.model_validate(event) for event in events]

    async def list_positions(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[PositionSchema]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            rows: Sequence[tuple[Position, Security]] = (
                await session.execute(
                    select(Position, Security)
                    .join(Security, Security.symbol == Position.security_symbol)
                    .where(Position.account_id == account.id, Position.quantity > 0)
                    .order_by(Position.updated_at.desc())
                )
            ).all()
            return [
                PositionSchema(
                    id=position.id,
                    account_id=position.account_id,
                    symbol=security.symbol,
                    name=security.name,
                    currency=security.currency,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    realized_pnl=position.realized_pnl,
                    updated_at=position.updated_at,
                )
                for position, security in rows
            ]

    async def get_cash_balances(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[CashBalance]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            return await self._cash_balances(session, account.id)

    async def get_realized_pnl_by_currency(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> dict[str, Decimal]:
        async with session.begin():
            account = await self.ensure_user_account(session, user_id)
            rows = (
                await session.execute(
                    select(Security.currency, func.coalesce(func.sum(Position.realized_pnl), ZERO))
                    .join(Security, Security.symbol == Position.security_symbol)
                    .where(Position.account_id == account.id)
                    .group_by(Security.currency)
                )
            ).all()
            return {currency: money(Decimal(realized_pnl)) for currency, realized_pnl in rows}


paper_trading_service = PaperTradingService()
