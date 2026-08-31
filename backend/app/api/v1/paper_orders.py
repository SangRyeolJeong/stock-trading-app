from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_session
from app.schemas.paper import (
    PaperAccount,
    PaperOrder,
    PaperOrderRequest,
    PaperOrderStatusEvent,
    PortfolioCurrencySummary,
    PortfolioSummary,
    Position,
)
from app.services.market import market_data_service
from app.services.paper_order_state import InvalidOrderStateError
from app.services.paper_trading import PaperTradingError, money, paper_trading_service

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
router = APIRouter(tags=["paper-trading"])


@router.get("/paper/accounts", response_model=list[PaperAccount])
async def list_paper_accounts(session: Session, user: CurrentUser) -> list[PaperAccount]:
    return await paper_trading_service.list_accounts(session, user.id)


@router.get("/paper/orders", response_model=list[PaperOrder])
async def list_paper_orders(
    session: Session,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PaperOrder]:
    pending_orders = await paper_trading_service.list_pending_order_refs(session, user.id)
    for order_id, symbol in pending_orders:
        quote = await market_data_service.get_quote(symbol)
        if quote is not None:
            await paper_trading_service.try_fill_pending_order(session, user.id, order_id, quote)
    return await paper_trading_service.list_orders(session, user.id, limit)


@router.get("/paper/positions", response_model=list[Position])
async def list_paper_positions(
    session: Session,
    user: CurrentUser,
) -> list[Position]:
    return await paper_trading_service.list_positions(session, user.id)


@router.post("/paper/orders", response_model=PaperOrder, status_code=status.HTTP_201_CREATED)
async def create_paper_order(
    order: PaperOrderRequest,
    session: Session,
    user: CurrentUser,
) -> PaperOrder:
    try:
        existing = await paper_trading_service.get_idempotent_order(session, user.id, order)
        if existing is not None:
            return existing
        quote = await market_data_service.get_quote(order.symbol)
        if quote is None:
            raise HTTPException(status_code=404, detail="시세를 찾을 수 없습니다.")
        return await paper_trading_service.execute_immediately(session, user.id, order, quote)
    except PaperTradingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/paper/orders/{order_id}", response_model=PaperOrder)
async def cancel_paper_order(
    order_id: UUID,
    session: Session,
    user: CurrentUser,
) -> PaperOrder:
    try:
        return await paper_trading_service.cancel_order(session, user.id, order_id)
    except (PaperTradingError, InvalidOrderStateError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get(
    "/paper/orders/{order_id}/events",
    response_model=list[PaperOrderStatusEvent],
)
async def list_paper_order_status_events(
    order_id: UUID,
    session: Session,
    user: CurrentUser,
) -> list[PaperOrderStatusEvent]:
    try:
        return await paper_trading_service.list_order_status_events(session, user.id, order_id)
    except PaperTradingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/portfolios/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    session: Session,
    user: CurrentUser,
) -> PortfolioSummary:
    positions = await paper_trading_service.list_positions(session, user.id)
    balances = await paper_trading_service.get_cash_balances(session, user.id)
    realized_pnl_by_currency = await paper_trading_service.get_realized_pnl_by_currency(
        session,
        user.id,
    )
    enriched_positions: list[Position] = []

    for position in positions:
        quote = await market_data_service.get_quote(position.symbol)
        current_price = quote.price if quote else position.average_cost
        market_value = money(current_price * position.quantity)
        unrealized_pnl = money((current_price - position.average_cost) * position.quantity)
        cost_basis = position.average_cost * position.quantity
        return_rate = money(unrealized_pnl / cost_basis * Decimal("100")) if cost_basis else Decimal("0")
        enriched_positions.append(
            position.model_copy(
                update={
                    "current_price": current_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "return_rate": return_rate,
                }
            )
        )

    currencies: list[PortfolioCurrencySummary] = []
    currency_codes = sorted({balance.currency for balance in balances} | {item.currency for item in enriched_positions})
    for currency in currency_codes:
        cash = next((balance.amount for balance in balances if balance.currency == currency), Decimal("0"))
        currency_positions = [item for item in enriched_positions if item.currency == currency]
        positions_value = money(sum((item.market_value or Decimal("0") for item in currency_positions), Decimal("0")))
        unrealized_pnl = money(
            sum((item.unrealized_pnl or Decimal("0") for item in currency_positions), Decimal("0"))
        )
        realized_pnl = realized_pnl_by_currency.get(currency, Decimal("0"))
        currencies.append(
            PortfolioCurrencySummary(
                currency=currency,
                cash=cash,
                positions_value=positions_value,
                total_value=money(cash + positions_value),
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
            )
        )

    return PortfolioSummary(
        account_id=paper_trading_service.account_id_for_user(user.id),
        currencies=currencies,
        positions=enriched_positions,
        as_of=datetime.now(UTC),
    )
