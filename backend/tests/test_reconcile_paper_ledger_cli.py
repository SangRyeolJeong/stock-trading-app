from uuid import UUID

from app.cli import reconcile_paper_ledger
from app.services.paper_ledger_reconciliation import (
    ReconciliationIssue,
    ReconciliationReport,
)


def report(*issues: ReconciliationIssue) -> ReconciliationReport:
    return ReconciliationReport(
        checked_accounts=1,
        checked_orders=2,
        checked_ledger_entries=6,
        checked_positions=1,
        issues=issues,
    )


def test_cli_returns_success_for_consistent_ledger(monkeypatch, capsys) -> None:
    async def consistent(account_id: str | None = None) -> ReconciliationReport:
        assert account_id == "demo-account"
        return report()

    monkeypatch.setattr(reconcile_paper_ledger, "reconcile", consistent)

    result = reconcile_paper_ledger.main(["--account-id", "demo-account"])

    assert result == 0
    assert "reconciliation: ok" in capsys.readouterr().out


def test_cli_prints_scoped_issues_and_returns_failure(monkeypatch, capsys) -> None:
    issue = ReconciliationIssue(
        code="TRADE_LEDGER_AMOUNT",
        message="원장 금액이 예상 금액과 다릅니다.",
        account_id="demo-account",
        order_id=UUID("00000000-0000-0000-0000-000000000001"),
        currency="USD",
        symbol="QQQM",
    )

    async def inconsistent(account_id: str | None = None) -> ReconciliationReport:
        return report(issue)

    monkeypatch.setattr(reconcile_paper_ledger, "reconcile", inconsistent)

    result = reconcile_paper_ledger.main([])
    output = capsys.readouterr().out

    assert result == 1
    assert "reconciliation: inconsistent" in output
    assert "[TRADE_LEDGER_AMOUNT]" in output
    assert "account=demo-account" in output
    assert "currency=USD" in output
    assert "symbol=QQQM" in output


def test_cli_hides_database_error_details(monkeypatch, capsys) -> None:
    async def failed(account_id: str | None = None) -> ReconciliationReport:
        raise RuntimeError("postgresql://secret-user:secret-password@database/moa")

    monkeypatch.setattr(reconcile_paper_ledger, "reconcile", failed)

    result = reconcile_paper_ledger.main([])
    output = capsys.readouterr().out

    assert result == 2
    assert "database check could not complete" in output
    assert "secret-password" not in output
