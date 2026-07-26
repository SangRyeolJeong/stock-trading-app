from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.paper import (
    CashLedgerEntry,
    PaperAccount,
    PaperExecution,
    PaperOrder,
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
from app.schemas.paper import (
    Position as PositionSchema,
)

MONEY_QUANTUM = Decimal("0.00000001")
ZERO = Decimal("0")
DEMO_ACCOUNT_ID = "demo-account"
DEMO_USER_ID = "demo-user"


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


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class PaperTradingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.initial_balances = {
            "KRW": money(settings.paper_initial_krw),
            "USD": money(settings.paper_initial_usd),
        }
        self.fee_rate = settings.paper_fee_rate

    async def ensure_demo_account(self, session: AsyncSession) -> PaperAccount:
        account = await session.get(PaperAccount, DEMO_ACCOUNT_ID)
        if account is not None:
            return account

        account = PaperAccount(
            id=DEMO_ACCOUNT_ID,
            user_id=DEMO_USER_ID,
            name="MOA 모의투자",
            base_currency="KRW",
        )
        session.add(account)
        await session.flush()
        for currency, balance in self.initial_balances.items():
            session.add(
                CashLedgerEntry(
                    account_id=account.id,
                    currency=currency,
                    entry_type="initial_deposit",
                    amount=balance,
                    balance_after=balance,
                )
            )
        await session.flush()
        return account

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
    def _order_query() -> Select[tuple[PaperOrder, PaperExecution, Security]]:
        return (
            select(PaperOrder, PaperExecution, Security)
            .join(PaperExecution, PaperExecution.order_id == PaperOrder.id)
            .join(Security, Security.symbol == PaperOrder.security_symbol)
        )

    @staticmethod
    def _order_schema(order: PaperOrder, execution: PaperExecution, security: Security) -> PaperOrderSchema:
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
            filled_price=execution.price,
            gross_amount=execution.gross_amount,
            fee=execution.fee,
            realized_pnl=execution.realized_pnl,
            created_at=order.created_at,
        )

    async def execute_immediately(
        self,
        session: AsyncSession,
        request: PaperOrderRequest,
        quote: Quote,
    ) -> PaperOrderSchema:
        async with session.begin():
            await self.ensure_demo_account(session)
            account = await session.scalar(
                select(PaperAccount).where(PaperAccount.id == request.account_id).with_for_update()
            )
            if account is None:
                raise AccountNotFoundError("모의 계좌를 찾을 수 없습니다.")

            existing_row = (
                await session.execute(
                    self._order_query().where(
                        PaperOrder.account_id == request.account_id,
                        PaperOrder.idempotency_key == request.idempotency_key,
                    )
                )
            ).one_or_none()
            if existing_row is not None:
                existing, execution, security = existing_row
                if (
                    existing.security_symbol != request.symbol
                    or existing.side != request.side
                    or existing.order_type != request.order_type
                    or existing.quantity != request.quantity
                    or existing.requested_price != request.limit_price
                ):
                    raise IdempotencyConflictError("같은 멱등성 키가 다른 주문에 이미 사용됐습니다.")
                return self._order_schema(existing, execution, security)

            fill_price = money(request.limit_price if request.order_type == "limit" else quote.price)
            gross_amount = money(fill_price * request.quantity)
            fee = money(gross_amount * self.fee_rate)
            current_cash = await self._cash_balance(session, account.id, quote.currency)

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

            position = await session.scalar(
                select(Position)
                .where(
                    Position.account_id == account.id,
                    Position.security_symbol == quote.symbol,
                )
                .with_for_update()
            )
            held_quantity = position.quantity if position else ZERO

            if request.side == "buy" and current_cash < gross_amount + fee:
                raise InsufficientCashError(
                    f"주문 가능 현금이 부족합니다. 필요 {gross_amount + fee} {quote.currency}, "
                    f"보유 {current_cash} {quote.currency}"
                )
            if request.side == "sell" and held_quantity < request.quantity:
                raise InsufficientPositionError(
                    f"보유 수량이 부족합니다. 주문 {request.quantity}주, 보유 {held_quantity}주"
                )

            order = PaperOrder(
                account_id=account.id,
                security_symbol=quote.symbol,
                idempotency_key=request.idempotency_key,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                requested_price=request.limit_price,
                status="filled",
            )
            session.add(order)
            await session.flush()

            realized_pnl = ZERO
            if request.side == "buy":
                new_quantity = held_quantity + request.quantity
                previous_cost = held_quantity * (position.average_cost if position else ZERO)
                new_average_cost = money((previous_cost + gross_amount) / new_quantity)
                if position is None:
                    position = Position(
                        account_id=account.id,
                        security_symbol=quote.symbol,
                        quantity=new_quantity,
                        average_cost=new_average_cost,
                        realized_pnl=ZERO,
                    )
                    session.add(position)
                else:
                    position.quantity = new_quantity
                    position.average_cost = new_average_cost
                trade_amount = -gross_amount
            else:
                assert position is not None
                realized_pnl = money((fill_price - position.average_cost) * request.quantity - fee)
                position.quantity = held_quantity - request.quantity
                position.realized_pnl = money(position.realized_pnl + realized_pnl)
                trade_amount = gross_amount

            execution = PaperExecution(
                order_id=order.id,
                quantity=request.quantity,
                price=fill_price,
                gross_amount=gross_amount,
                fee=fee,
                realized_pnl=realized_pnl,
            )
            session.add(execution)

            balance_after_trade = money(current_cash + trade_amount)
            session.add(
                CashLedgerEntry(
                    account_id=account.id,
                    order_id=order.id,
                    currency=quote.currency,
                    entry_type="trade_settlement",
                    amount=trade_amount,
                    balance_after=balance_after_trade,
                )
            )
            final_balance = money(balance_after_trade - fee)
            session.add(
                CashLedgerEntry(
                    account_id=account.id,
                    order_id=order.id,
                    currency=quote.currency,
                    entry_type="commission",
                    amount=-fee,
                    balance_after=final_balance,
                )
            )
            await session.flush()

            positions_value = await session.scalar(
                select(func.coalesce(func.sum(Position.quantity * Position.average_cost), ZERO))
                .join(Security, Security.symbol == Position.security_symbol)
                .where(Position.account_id == account.id, Security.currency == quote.currency)
            )
            positions_value = money(Decimal(positions_value or ZERO))
            session.add(
                PortfolioSnapshot(
                    account_id=account.id,
                    currency=quote.currency,
                    cash_value=final_balance,
                    positions_value=positions_value,
                    total_value=money(final_balance + positions_value),
                )
            )
            await session.flush()
            await session.refresh(order)
            await session.refresh(execution)
            return self._order_schema(order, execution, security)

    async def list_accounts(self, session: AsyncSession) -> list[PaperAccountSchema]:
        async with session.begin():
            await self.ensure_demo_account(session)
            accounts = (await session.scalars(select(PaperAccount).order_by(PaperAccount.created_at))).all()
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
        account_id: str,
        limit: int = 100,
    ) -> list[PaperOrderSchema]:
        async with session.begin():
            await self.ensure_demo_account(session)
            rows = (
                await session.execute(
                    self._order_query()
                    .where(PaperOrder.account_id == account_id)
                    .order_by(PaperOrder.created_at.desc())
                    .limit(limit)
                )
            ).all()
            return [self._order_schema(*row) for row in rows]

    async def list_positions(self, session: AsyncSession, account_id: str) -> list[PositionSchema]:
        async with session.begin():
            await self.ensure_demo_account(session)
            rows: Sequence[tuple[Position, Security]] = (
                await session.execute(
                    select(Position, Security)
                    .join(Security, Security.symbol == Position.security_symbol)
                    .where(Position.account_id == account_id, Position.quantity > 0)
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

    async def get_cash_balances(self, session: AsyncSession, account_id: str) -> list[CashBalance]:
        async with session.begin():
            await self.ensure_demo_account(session)
            return await self._cash_balances(session, account_id)

    async def get_realized_pnl_by_currency(
        self,
        session: AsyncSession,
        account_id: str,
    ) -> dict[str, Decimal]:
        async with session.begin():
            await self.ensure_demo_account(session)
            rows = (
                await session.execute(
                    select(Security.currency, func.coalesce(func.sum(Position.realized_pnl), ZERO))
                    .join(Security, Security.symbol == Position.security_symbol)
                    .where(Position.account_id == account_id)
                    .group_by(Security.currency)
                )
            ).all()
            return {currency: money(Decimal(realized_pnl)) for currency, realized_pnl in rows}


paper_trading_service = PaperTradingService()
