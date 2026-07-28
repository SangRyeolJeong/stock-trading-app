import asyncio
import os

os.environ["APP_ENV"] = "test"
os.environ["MARKET_DATA_PROVIDER"] = "mock"
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
    async def reset() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(reset())
