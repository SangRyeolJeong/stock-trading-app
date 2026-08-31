import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.db.session import engine

POSTGRES_TESTS_ENABLED = os.environ.get("MOA_TEST_DATABASE") == "postgresql"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if POSTGRES_TESTS_ENABLED:
        return
    skip = pytest.mark.skip(reason="MOA_TEST_DATABASE=postgresql에서만 실행하는 통합 테스트입니다.")
    for item in items:
        if "/tests/postgres/" in str(item.path):
            item.add_marker(skip)


@pytest_asyncio.fixture(autouse=True)
async def clean_migrated_postgres_schema() -> AsyncIterator[None]:
    if not POSTGRES_TESTS_ENABLED:
        yield
        return
    if engine.dialect.name != "postgresql":
        pytest.fail("PostgreSQL 통합 테스트에는 postgresql+asyncpg DATABASE_URL이 필요합니다.")

    async with engine.begin() as connection:
        revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != "20260901_0005":
            pytest.fail(f"Alembic head가 필요합니다. 현재 revision: {revision}")
        await connection.execute(
            text(
                """
                TRUNCATE TABLE
                    user_preferences,
                    portfolio_snapshots,
                    positions,
                    cash_ledger_entries,
                    paper_executions,
                    order_status_events,
                    paper_orders,
                    securities,
                    paper_accounts
                RESTART IDENTITY CASCADE
                """
            )
        )
    yield
    await engine.dispose()
