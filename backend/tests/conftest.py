import asyncio
import os

os.environ["APP_ENV"] = "test"
os.environ["MARKET_DATA_PROVIDER"] = "mock"
if os.environ.get("MOA_TEST_DATABASE") == "postgresql":
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "MOA_TEST_DATABASE=postgresql에는 명시적인 postgresql+asyncpg DATABASE_URL이 필요합니다."
        )
else:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./.pytest-paper.db"
os.environ["PAPER_INITIAL_KRW"] = "10000000"
os.environ["PAPER_INITIAL_USD"] = "10000"
os.environ["PAPER_FEE_RATE"] = "0.001"

import pytest

from app.db.base import Base
from app.db.session import engine
from app.models import paper  # noqa: F401


@pytest.fixture(autouse=True)
def reset_database() -> None:
    if engine.dialect.name != "sqlite":
        return

    async def reset() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(reset())
