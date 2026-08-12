from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.paper import PaperAccount, PaperOrder


def compiled_postgresql(statement: object) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))  # type: ignore[attr-defined]


def test_account_lock_targets_only_paper_accounts() -> None:
    sql = compiled_postgresql(
        select(PaperAccount)
        .where(PaperAccount.id == "demo-account")
        .with_for_update(of=PaperAccount)
    )

    assert "FOR UPDATE OF paper_accounts" in sql


def test_order_lock_targets_only_paper_orders_without_outer_join() -> None:
    sql = compiled_postgresql(
        select(PaperOrder)
        .where(PaperOrder.account_id == "demo-account")
        .with_for_update(of=PaperOrder)
    )

    assert "FOR UPDATE OF paper_orders" in sql
    assert "JOIN paper_executions" not in sql
