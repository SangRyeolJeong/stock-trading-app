from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from app.db.session import async_session_factory
from app.services.paper_ledger_reconciliation import (
    ReconciliationIssue,
    ReconciliationReport,
    paper_ledger_reconciler,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="모의 주문·체결·현금 원장·포지션 불변식을 읽기 전용으로 대사합니다.",
    )
    parser.add_argument(
        "--account-id",
        help="특정 모의 계좌만 점검합니다. 생략하면 모든 계좌를 점검합니다.",
    )
    return parser


async def reconcile(account_id: str | None = None) -> ReconciliationReport:
    async with async_session_factory() as session:
        return await paper_ledger_reconciler.reconcile(session, account_id)


def _issue_line(issue: ReconciliationIssue) -> str:
    scope = [f"account={issue.account_id}"]
    if issue.order_id is not None:
        scope.append(f"order={issue.order_id}")
    if issue.currency is not None:
        scope.append(f"currency={issue.currency}")
    if issue.symbol is not None:
        scope.append(f"symbol={issue.symbol}")
    return f"[{issue.code}] {' '.join(scope)} — {issue.message}"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = asyncio.run(reconcile(args.account_id))
    except Exception:  # noqa: BLE001 - DB 주소나 내부 쿼리 정보를 출력하지 않는다
        print("paper ledger reconciliation failed: database check could not complete")
        return 2

    print(
        "paper ledger reconciliation: "
        f"{'ok' if report.is_consistent else 'inconsistent'} "
        f"(accounts={report.checked_accounts}, orders={report.checked_orders}, "
        f"ledger_entries={report.checked_ledger_entries}, "
        f"positions={report.checked_positions}, issues={len(report.issues)})"
    )
    for issue in report.issues:
        print(_issue_line(issue))
    return 0 if report.is_consistent else 1


if __name__ == "__main__":
    raise SystemExit(main())
