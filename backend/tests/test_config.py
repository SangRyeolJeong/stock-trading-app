import pytest

from app.core.config import Settings


def test_comma_separated_cors_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5180",
    )

    settings = Settings()

    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://localhost:5180",
    ]


def test_production_requires_supabase_auth() -> None:
    with pytest.raises(ValueError, match="AUTH_MODE=supabase"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_mode="demo",
        )


def test_supabase_auth_requires_project_settings() -> None:
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        Settings(
            _env_file=None,
            auth_mode="supabase",
        )


def test_production_accepts_complete_supabase_auth_settings() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_mode="supabase",
        database_url="postgresql+asyncpg://moa:test@database:5432/moa",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="sb_publishable_example",
        cors_origins=["https://app.example.com"],
    )

    assert settings.auth_mode == "supabase"


def test_openai_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Settings(
            _env_file=None,
            ai_provider="openai",
            openai_api_key=None,
        )


def test_production_rejects_non_postgresql_database() -> None:
    with pytest.raises(ValueError, match="postgresql\\+asyncpg"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_mode="supabase",
            supabase_url="https://example.supabase.co",
            supabase_publishable_key="sb_publishable_example",
            database_url="sqlite+aiosqlite:///./unsafe-production.db",
            cors_origins=["https://app.example.com"],
        )


@pytest.mark.parametrize(
    "cors_origins",
    [
        ["*"],
        ["http://app.example.com"],
        ["https://localhost:5173"],
        ["https://app.example.com/path"],
    ],
)
def test_production_rejects_unsafe_cors_origins(cors_origins: list[str]) -> None:
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_mode="supabase",
            database_url="postgresql+asyncpg://moa:test@database:5432/moa",
            supabase_url="https://example.supabase.co",
            supabase_publishable_key="sb_publishable_example",
            cors_origins=cors_origins,
        )


@pytest.mark.parametrize(
    "supabase_url",
    [
        "http://example.supabase.co",
        "https://localhost:54321",
        "https://example.supabase.co/auth/v1",
    ],
)
def test_production_rejects_insecure_supabase_url(supabase_url: str) -> None:
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_mode="supabase",
            database_url="postgresql+asyncpg://moa:test@database:5432/moa",
            supabase_url=supabase_url,
            supabase_publishable_key="sb_publishable_example",
            cors_origins=["https://app.example.com"],
        )


def test_kis_provider_requires_api_credentials() -> None:
    with pytest.raises(ValueError, match="KIS_APP_KEY"):
        Settings(
            _env_file=None,
            market_data_provider="kis",
        )


@pytest.mark.parametrize(
    ("setting_name", "value"),
    [
        ("database_pool_size", 0),
        ("database_max_overflow", -1),
        ("database_pool_timeout_seconds", 0),
        ("database_pool_recycle_seconds", 10),
        ("database_connect_timeout_seconds", 0),
        ("database_command_timeout_seconds", 301),
    ],
)
def test_database_limits_reject_unsafe_values(setting_name: str, value: object) -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{setting_name: value})
