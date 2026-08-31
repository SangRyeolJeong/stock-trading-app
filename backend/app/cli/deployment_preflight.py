from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.config import Settings


def safe_configuration_summary(settings: Settings) -> dict[str, object]:
    return {
        "environment": settings.app_env,
        "auth_mode": settings.auth_mode,
        "database_driver": settings.database_url.partition("://")[0],
        "cors_origin_count": len(settings.cors_origins),
        "market_provider": settings.market_data_provider,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.openai_model if settings.ai_provider == "openai" else None,
    }


def load_migration_heads(config_path: Path) -> tuple[str, ...]:
    config = Config(str(config_path))
    script = ScriptDirectory.from_config(config)
    return tuple(sorted(script.get_heads()))


def build_preflight_report(
    settings: Settings,
    *,
    database_heads: tuple[str, ...],
    expected_heads: tuple[str, ...],
) -> dict[str, object]:
    migrations_current = database_heads == expected_heads
    return {
        "status": "ready" if migrations_current else "migration_required",
        **safe_configuration_summary(settings),
        "database": "ok",
        "database_migration_heads": list(database_heads),
        "expected_migration_heads": list(expected_heads),
    }


async def inspect_database(settings: Settings) -> tuple[str, ...]:
    connect_args = {
        "timeout": settings.database_connect_timeout_seconds,
        "command_timeout": settings.database_command_timeout_seconds,
        "server_settings": {"application_name": f"{settings.app_name} preflight"},
    }
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args=connect_args,
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            result = await connection.execute(text("SELECT version_num FROM alembic_version"))
            return tuple(sorted(str(row[0]) for row in result.fetchall()))
    finally:
        await engine.dispose()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="비밀값을 출력하지 않고 MOA 운영 설정·DB 마이그레이션을 점검합니다.",
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="환경변수 검증만 수행하고 데이터베이스에는 연결하지 않습니다.",
    )
    parser.add_argument(
        "--alembic-config",
        type=Path,
        default=Path("alembic.ini"),
        help="Alembic 설정 파일 경로입니다.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        settings = Settings()
    except ValidationError:
        print(
            "deployment preflight failed: production configuration is invalid",
            file=sys.stderr,
        )
        return 1

    if settings.app_env != "production":
        print(
            "deployment preflight failed: APP_ENV must be production",
            file=sys.stderr,
        )
        return 1

    if args.config_only:
        print(json.dumps({"status": "config_ready", **safe_configuration_summary(settings)}))
        return 0

    try:
        expected_heads = load_migration_heads(args.alembic_config)
        database_heads = asyncio.run(inspect_database(settings))
    except Exception:  # noqa: BLE001 - never expose connection strings or provider errors
        print(
            "deployment preflight failed: database or migration check failed",
            file=sys.stderr,
        )
        return 1

    report = build_preflight_report(
        settings,
        database_heads=database_heads,
        expected_heads=expected_heads,
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
