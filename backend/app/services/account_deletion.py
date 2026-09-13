from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker import BrokerOrder, BrokerOutboxEvent
from app.models.paper import (
    CashLedgerEntry,
    PaperAccount,
    PaperExecution,
    PaperOrder,
    PaperOrderStatusEvent,
    PortfolioSnapshot,
    Position,
)
from app.models.preferences import UserPreferences
from app.schemas.account import AccountDeletionResponse


class AccountDeletionBlockedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DeletionScope:
    account_ids: tuple[str, ...]
    paper_order_ids: tuple[object, ...]
    broker_order_ids: tuple[object, ...]


class AccountDeletionService:
    async def delete_user_data(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> AccountDeletionResponse:
        async with session.begin():
            accounts = list(
                await session.scalars(
                    select(PaperAccount)
                    .where(PaperAccount.user_id == user_id)
                    .with_for_update(of=PaperAccount)
                )
            )
            account_ids = tuple(account.id for account in accounts)
            scope = await self._scope(session, account_ids)
            await self._assert_no_unresolved_broker_orders(session, scope)

            preferences_deleted = await self._delete_preferences(session, user_id)
            if not account_ids:
                return AccountDeletionResponse(
                    deleted=True,
                    preferences_deleted=preferences_deleted,
                    paper_accounts_deleted=0,
                    paper_orders_deleted=0,
                    broker_orders_deleted=0,
                )

            await self._delete_account_children(session, scope)
            await session.execute(delete(PaperAccount).where(PaperAccount.id.in_(account_ids)))
            return AccountDeletionResponse(
                deleted=True,
                preferences_deleted=preferences_deleted,
                paper_accounts_deleted=len(account_ids),
                paper_orders_deleted=len(scope.paper_order_ids),
                broker_orders_deleted=len(scope.broker_order_ids),
            )

    @staticmethod
    async def _scope(session: AsyncSession, account_ids: tuple[str, ...]) -> DeletionScope:
        if not account_ids:
            return DeletionScope((), (), ())
        paper_order_ids = tuple(
            await session.scalars(select(PaperOrder.id).where(PaperOrder.account_id.in_(account_ids)))
        )
        broker_order_ids = tuple(
            await session.scalars(select(BrokerOrder.id).where(BrokerOrder.account_id.in_(account_ids)))
        )
        return DeletionScope(account_ids, paper_order_ids, broker_order_ids)

    @staticmethod
    async def _assert_no_unresolved_broker_orders(
        session: AsyncSession,
        scope: DeletionScope,
    ) -> None:
        if not scope.account_ids:
            return
        unresolved = await session.scalar(
            select(func.count())
            .select_from(BrokerOrder)
            .where(
                BrokerOrder.account_id.in_(scope.account_ids),
                BrokerOrder.status != "cancelled",
            )
        )
        if unresolved:
            raise AccountDeletionBlockedError(
                "미확정 브로커 주문을 먼저 취소하거나 대사해야 계정을 삭제할 수 있습니다."
            )

    @staticmethod
    async def _delete_preferences(session: AsyncSession, user_id: str) -> int:
        result = await session.execute(
            delete(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.rowcount or 0

    @staticmethod
    async def _delete_account_children(
        session: AsyncSession,
        scope: DeletionScope,
    ) -> None:
        if scope.broker_order_ids:
            await session.execute(
                delete(BrokerOutboxEvent).where(
                    BrokerOutboxEvent.order_id.in_(scope.broker_order_ids)
                )
            )
            await session.execute(
                delete(BrokerOrder).where(BrokerOrder.id.in_(scope.broker_order_ids))
            )
        if scope.paper_order_ids:
            await session.execute(
                delete(PaperOrderStatusEvent).where(
                    PaperOrderStatusEvent.order_id.in_(scope.paper_order_ids)
                )
            )
            await session.execute(
                delete(PaperExecution).where(PaperExecution.order_id.in_(scope.paper_order_ids))
            )
        await session.execute(
            delete(CashLedgerEntry).where(CashLedgerEntry.account_id.in_(scope.account_ids))
        )
        if scope.paper_order_ids:
            await session.execute(
                delete(PaperOrder).where(PaperOrder.id.in_(scope.paper_order_ids))
            )
        await session.execute(delete(Position).where(Position.account_id.in_(scope.account_ids)))
        await session.execute(
            delete(PortfolioSnapshot).where(PortfolioSnapshot.account_id.in_(scope.account_ids))
        )


account_deletion_service = AccountDeletionService()
