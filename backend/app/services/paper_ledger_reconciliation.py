from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import (
    CashLedgerEntry,
    PaperAccount,
    PaperExecution,
    PaperOrder,
    Position,
    Security,
)
from app.services.paper_trading import ZERO, money


@dataclass(frozen=True, slots=True)
class ReconciliationIssue:
    code: str
    message: str
    account_id: str
    order_id: UUID | None = None
    currency: str | None = None
    symbol: str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    checked_accounts: int
    checked_orders: int
    checked_ledger_entries: int
    checked_positions: int
    issues: tuple[ReconciliationIssue, ...]

    @property
    def is_consistent(self) -> bool:
        return not self.issues


class PaperLedgerReconciler:
    async def reconcile(
        self,
        session: AsyncSession,
        account_id: str | None = None,
    ) -> ReconciliationReport:
        account_statement = select(PaperAccount).order_by(PaperAccount.id)
        if account_id is not None:
            account_statement = account_statement.where(PaperAccount.id == account_id)
        accounts = list(await session.scalars(account_statement))
        if account_id is not None and not accounts:
            return ReconciliationReport(
                checked_accounts=0,
                checked_orders=0,
                checked_ledger_entries=0,
                checked_positions=0,
                issues=(
                    ReconciliationIssue(
                        code="ACCOUNT_NOT_FOUND",
                        message="대상 모의 계좌를 찾을 수 없습니다.",
                        account_id=account_id,
                    ),
                ),
            )

        issues: list[ReconciliationIssue] = []
        checked_orders = 0
        checked_ledger_entries = 0
        checked_positions = 0
        for account in accounts:
            account_issues, counts = await self._reconcile_account(session, account.id)
            issues.extend(account_issues)
            checked_orders += counts[0]
            checked_ledger_entries += counts[1]
            checked_positions += counts[2]

        return ReconciliationReport(
            checked_accounts=len(accounts),
            checked_orders=checked_orders,
            checked_ledger_entries=checked_ledger_entries,
            checked_positions=checked_positions,
            issues=tuple(issues),
        )

    async def _reconcile_account(
        self,
        session: AsyncSession,
        account_id: str,
    ) -> tuple[list[ReconciliationIssue], tuple[int, int, int]]:
        order_rows = (
            await session.execute(
                select(PaperOrder, Security)
                .join(Security, Security.symbol == PaperOrder.security_symbol)
                .where(PaperOrder.account_id == account_id)
                .order_by(PaperOrder.created_at, PaperOrder.id)
            )
        ).all()
        orders = [row[0] for row in order_rows]
        securities = {order.id: security for order, security in order_rows}
        order_ids = [order.id for order in orders]
        executions = (
            list(
                await session.scalars(
                    select(PaperExecution)
                    .where(PaperExecution.order_id.in_(order_ids))
                    .order_by(PaperExecution.executed_at, PaperExecution.id)
                )
            )
            if order_ids
            else []
        )
        ledger_entries = list(
            await session.scalars(
                select(CashLedgerEntry)
                .where(CashLedgerEntry.account_id == account_id)
                .order_by(CashLedgerEntry.created_at, CashLedgerEntry.id)
            )
        )
        positions = list(
            await session.scalars(
                select(Position)
                .where(Position.account_id == account_id)
                .order_by(Position.security_symbol)
            )
        )

        executions_by_order: dict[UUID, list[PaperExecution]] = defaultdict(list)
        for execution in executions:
            executions_by_order[execution.order_id].append(execution)
        ledger_by_order: dict[UUID, list[CashLedgerEntry]] = defaultdict(list)
        for entry in ledger_entries:
            if entry.order_id is not None:
                ledger_by_order[entry.order_id].append(entry)

        issues = self._check_orders(
            account_id,
            orders,
            securities,
            executions_by_order,
            ledger_by_order,
        )
        known_order_ids = set(order_ids)
        for entry in ledger_entries:
            if entry.order_id is not None and entry.order_id not in known_order_ids:
                issues.append(
                    ReconciliationIssue(
                        code="ORDER_LEDGER_ACCOUNT_MISMATCH",
                        message="원장 행이 다른 계좌의 주문을 참조합니다.",
                        account_id=account_id,
                        order_id=entry.order_id,
                        currency=entry.currency,
                    )
                )
        issues.extend(self._check_balances(account_id, ledger_entries))
        issues.extend(
            self._check_positions(
                account_id,
                orders,
                executions_by_order,
                positions,
            )
        )
        return issues, (len(orders), len(ledger_entries), len(positions))

    def _check_orders(
        self,
        account_id: str,
        orders: list[PaperOrder],
        securities: dict[UUID, Security],
        executions_by_order: dict[UUID, list[PaperExecution]],
        ledger_by_order: dict[UUID, list[CashLedgerEntry]],
    ) -> list[ReconciliationIssue]:
        issues: list[ReconciliationIssue] = []
        for order in orders:
            executions = executions_by_order[order.id]
            entries = ledger_by_order[order.id]
            security = securities[order.id]
            context = {
                "account_id": account_id,
                "order_id": order.id,
                "currency": security.currency,
                "symbol": security.symbol,
            }
            if order.status == "filled" and len(executions) != 1:
                issues.append(
                    ReconciliationIssue(
                        code="FILLED_EXECUTION_COUNT",
                        message=f"체결 완료 주문의 체결 행이 {len(executions)}개입니다.",
                        **context,
                    )
                )
            elif order.status != "filled" and executions:
                issues.append(
                    ReconciliationIssue(
                        code="UNFILLED_HAS_EXECUTION",
                        message=f"{order.status} 주문에 체결 행이 남아 있습니다.",
                        **context,
                    )
                )

            if len(executions) != 1:
                if entries:
                    issues.append(
                        ReconciliationIssue(
                            code="UNEXPECTED_ORDER_LEDGER",
                            message="단일 체결이 없는 주문에 주문 연결 원장 행이 있습니다.",
                            **context,
                        )
                    )
                continue

            execution = executions[0]
            if execution.quantity != order.quantity:
                issues.append(
                    ReconciliationIssue(
                        code="EXECUTION_QUANTITY_MISMATCH",
                        message="주문 수량과 체결 수량이 다릅니다.",
                        **context,
                    )
                )
            if execution.gross_amount != money(execution.price * execution.quantity):
                issues.append(
                    ReconciliationIssue(
                        code="EXECUTION_GROSS_MISMATCH",
                        message="체결 금액이 체결가와 체결 수량의 곱과 다릅니다.",
                        **context,
                    )
                )

            trade_entries = [entry for entry in entries if entry.entry_type == "trade_settlement"]
            commission_entries = [entry for entry in entries if entry.entry_type == "commission"]
            unexpected_entries = [
                entry
                for entry in entries
                if entry.entry_type not in {"trade_settlement", "commission"}
            ]
            expected_trade_amount = (
                -execution.gross_amount if order.side == "buy" else execution.gross_amount
            )
            issues.extend(
                self._check_order_ledger_type(
                    context,
                    "TRADE_LEDGER",
                    trade_entries,
                    expected_trade_amount,
                )
            )
            issues.extend(
                self._check_order_ledger_type(
                    context,
                    "COMMISSION_LEDGER",
                    commission_entries,
                    -execution.fee,
                )
            )
            if unexpected_entries:
                issues.append(
                    ReconciliationIssue(
                        code="UNEXPECTED_ORDER_LEDGER_TYPE",
                        message="주문에 알 수 없는 유형의 원장 행이 연결돼 있습니다.",
                        **context,
                    )
                )
            for entry in entries:
                if entry.account_id != account_id or entry.currency != security.currency:
                    issues.append(
                        ReconciliationIssue(
                            code="ORDER_LEDGER_SCOPE_MISMATCH",
                            message="주문 원장의 계좌 또는 통화가 주문과 다릅니다.",
                            **context,
                        )
                    )
                    break
        return issues

    @staticmethod
    def _check_order_ledger_type(
        context: dict[str, object],
        code_prefix: str,
        entries: list[CashLedgerEntry],
        expected_amount: Decimal,
    ) -> list[ReconciliationIssue]:
        if len(entries) != 1:
            return [
                ReconciliationIssue(
                    code=f"{code_prefix}_COUNT",
                    message=f"필요한 원장 행이 {len(entries)}개입니다.",
                    **context,
                )
            ]
        if entries[0].amount != expected_amount:
            return [
                ReconciliationIssue(
                    code=f"{code_prefix}_AMOUNT",
                    message=(
                        f"원장 금액 {entries[0].amount}이 예상 금액 "
                        f"{expected_amount}과 다릅니다."
                    ),
                    **context,
                )
            ]
        return []

    @staticmethod
    def _check_balances(
        account_id: str,
        entries: list[CashLedgerEntry],
    ) -> list[ReconciliationIssue]:
        entries_by_currency: dict[str, list[CashLedgerEntry]] = defaultdict(list)
        for entry in entries:
            entries_by_currency[entry.currency].append(entry)

        issues: list[ReconciliationIssue] = []
        for currency, currency_entries in entries_by_currency.items():
            total = money(sum((entry.amount for entry in currency_entries), ZERO))
            if total < ZERO:
                issues.append(
                    ReconciliationIssue(
                        code="NEGATIVE_CASH_BALANCE",
                        message=f"원장 누적 현금이 음수입니다: {total}.",
                        account_id=account_id,
                        currency=currency,
                    )
                )
            latest_at = max(entry.created_at for entry in currency_entries)
            latest_candidates = [
                entry for entry in currency_entries if entry.created_at == latest_at
            ]
            if not any(entry.balance_after == total for entry in latest_candidates):
                issues.append(
                    ReconciliationIssue(
                        code="LATEST_BALANCE_MISMATCH",
                        message=f"최신 원장 잔액이 원장 누적 합계 {total}과 다릅니다.",
                        account_id=account_id,
                        currency=currency,
                    )
                )
        return issues

    @staticmethod
    def _check_positions(
        account_id: str,
        orders: list[PaperOrder],
        executions_by_order: dict[UUID, list[PaperExecution]],
        positions: list[Position],
    ) -> list[ReconciliationIssue]:
        expected_by_symbol: dict[str, Decimal] = defaultdict(lambda: ZERO)
        for order in orders:
            for execution in executions_by_order[order.id]:
                direction = Decimal("1") if order.side == "buy" else Decimal("-1")
                expected_by_symbol[order.security_symbol] += direction * execution.quantity

        stored_by_symbol = {position.security_symbol: position for position in positions}
        issues: list[ReconciliationIssue] = []
        for symbol in sorted(set(expected_by_symbol) | set(stored_by_symbol)):
            expected = expected_by_symbol[symbol]
            position = stored_by_symbol.get(symbol)
            stored = position.quantity if position is not None else ZERO
            if stored < ZERO:
                issues.append(
                    ReconciliationIssue(
                        code="NEGATIVE_POSITION",
                        message=f"포지션 수량이 음수입니다: {stored}.",
                        account_id=account_id,
                        symbol=symbol,
                    )
                )
            if stored != expected:
                issues.append(
                    ReconciliationIssue(
                        code="POSITION_QUANTITY_MISMATCH",
                        message=f"포지션 수량 {stored}이 체결 누적 수량 {expected}과 다릅니다.",
                        account_id=account_id,
                        symbol=symbol,
                    )
                )
        return issues


paper_ledger_reconciler = PaperLedgerReconciler()
