from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings


def build_engine_options(settings: Settings) -> dict[str, object]:
    options: dict[str, object] = {"pool_pre_ping": True}
    if settings.database_url.startswith("sqlite"):
        options["poolclass"] = NullPool
        return options

    options.update(
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_recycle=settings.database_pool_recycle_seconds,
        pool_use_lifo=True,
    )
    if settings.database_url.startswith("postgresql+asyncpg://"):
        options["connect_args"] = {
            "timeout": settings.database_connect_timeout_seconds,
            "command_timeout": settings.database_command_timeout_seconds,
            "server_settings": {"application_name": settings.app_name},
        }
    return options

settings = get_settings()
engine = create_async_engine(settings.database_url, **build_engine_options(settings))
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
