import json
from pathlib import Path

from app.cli.deployment_preflight import (
    build_preflight_report,
    load_migration_heads,
    safe_configuration_summary,
)
from app.core.config import Settings


def production_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="production",
        auth_mode="supabase",
        database_url="postgresql+asyncpg://moa:do-not-print@database:5432/moa",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="sb_publishable_do_not_print",
        cors_origins=["https://app.example.com"],
    )


def test_safe_configuration_summary_never_contains_credentials() -> None:
    settings = production_settings().model_copy(
        update={"ai_provider": "openai", "openai_api_key": "do-not-print-openai"}
    )
    serialized = json.dumps(safe_configuration_summary(settings))

    assert "do-not-print" not in serialized
    assert "sb_publishable_do_not_print" not in serialized
    assert "do-not-print-openai" not in serialized
    assert "example.supabase.co" not in serialized
    assert "postgresql+asyncpg" in serialized
    assert '"ai_provider": "openai"' in serialized


def test_preflight_requires_database_to_match_all_migration_heads() -> None:
    current = build_preflight_report(
        production_settings(),
        database_heads=("20260729_0003",),
        expected_heads=("20260729_0003",),
    )
    behind = build_preflight_report(
        production_settings(),
        database_heads=("20260729_0002",),
        expected_heads=("20260729_0003",),
    )

    assert current["status"] == "ready"
    assert behind["status"] == "migration_required"


def test_alembic_configuration_exposes_the_repository_head() -> None:
    assert load_migration_heads(Path("alembic.ini")) == ("20260901_0005",)
