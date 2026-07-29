from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.session import build_engine_options


def test_postgresql_engine_options_are_bounded() -> None:
    settings = Settings(
        _env_file=None,
        app_name="MOA test API",
        database_url="postgresql+asyncpg://moa:test@database:5432/moa",
        database_pool_size=7,
        database_max_overflow=3,
        database_pool_timeout_seconds=4,
        database_pool_recycle_seconds=600,
        database_connect_timeout_seconds=5,
        database_command_timeout_seconds=12,
    )

    options = build_engine_options(settings)

    assert options == {
        "pool_pre_ping": True,
        "pool_size": 7,
        "max_overflow": 3,
        "pool_timeout": 4,
        "pool_recycle": 600,
        "pool_use_lifo": True,
        "connect_args": {
            "timeout": 5,
            "command_timeout": 12,
            "server_settings": {"application_name": "MOA test API"},
        },
    }


def test_sqlite_tests_keep_null_pool_without_postgresql_connect_args() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///./test.db",
    )

    assert build_engine_options(settings) == {
        "pool_pre_ping": True,
        "poolclass": NullPool,
    }
