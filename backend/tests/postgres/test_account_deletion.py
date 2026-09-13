from decimal import Decimal

import pytest
from sqlalchemy import func, select, update

from app.db.session import async_session_factory
from app.models.broker import BrokerOrder, BrokerOutboxEvent
from app.models.paper import CashLedgerEntry, PaperAccount
from app.models.preferences import UserPreferences
from app.schemas.preferences import UserPreferencesPayload
from app.services.account_deletion import AccountDeletionService
from app.services.broker_orders import BrokerOrderCommand, BrokerOrderService
from app.services.preferences import UserPreferencesService


@pytest.mark.asyncio
async def test_postgres_account_deletion_respects_foreign_keys_and_is_atomic() -> None:
    user_id = "postgres-delete-user"
    broker = BrokerOrderService()
    preferences = UserPreferencesService()
    deletion = AccountDeletionService()
    async with async_session_factory() as session:
        order = await broker.create_order(
            session,
            user_id,
            BrokerOrderCommand(
                client_order_id="postgres-delete-0001",
                symbol="QQQM",
                side="buy",
                order_type="market",
                quantity=Decimal("1"),
            ),
        )
        await preferences.upsert(
            session,
            user_id,
            UserPreferencesPayload(
                display_name="삭제 사용자",
                annual_salary_krw=45_000_000,
                monthly_investment_krw=500_000,
                investment_years=20,
                annual_return_rate_pct=7,
                withdrawal_age=60,
                strategy_goal="retirement",
                risk_profile="balanced",
                liquidity_preference=True,
                fee_sensitivity=True,
                income_preference=False,
            ),
        )
        async with session.begin():
            await session.execute(
                update(BrokerOrder)
                .where(BrokerOrder.id == order.id)
                .values(status="cancelled", broker_order_id="cancelled-postgres-order")
            )
            await session.execute(
                update(BrokerOutboxEvent)
                .where(BrokerOutboxEvent.order_id == order.id)
                .values(status="processed")
            )

    async with async_session_factory() as session:
        result = await deletion.delete_user_data(session, user_id)

    assert result.paper_accounts_deleted == 1
    assert result.broker_orders_deleted == 1
    async with async_session_factory() as session:
        for model in (
            PaperAccount,
            CashLedgerEntry,
            BrokerOrder,
            BrokerOutboxEvent,
            UserPreferences,
        ):
            assert await session.scalar(select(func.count()).select_from(model)) == 0
