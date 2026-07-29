from decimal import Decimal
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "MOA API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5180",
        ]
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moa"
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_pool_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    database_pool_recycle_seconds: int = Field(default=1800, ge=30, le=86400)
    database_connect_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    database_command_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    auth_mode: Literal["demo", "supabase"] = "demo"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    market_data_provider: Literal["mock", "kis"] = "mock"
    paper_initial_krw: Decimal = Decimal("10000000")
    paper_initial_usd: Decimal = Decimal("10000")
    paper_fee_rate: Decimal = Decimal("0.001")

    kis_environment: Literal["paper", "production"] = "paper"
    kis_app_key: str | None = None
    kis_app_secret: str | None = None
    kis_account_number: str | None = None
    kis_account_product_code: str = "01"
    kis_default_overseas_exchange: str = "NAS"
    kis_fx_probe_symbol: str = "AAPL"
    kis_fx_probe_exchange: str = "NAS"
    kis_master_refresh_enabled: bool = True
    market_quote_cache_seconds: float = 3.0
    market_chart_cache_seconds: float = 300.0
    market_fx_cache_seconds: float = 60.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_auth_settings(self) -> "Settings":
        if self.app_env == "production" and self.auth_mode != "supabase":
            raise ValueError("운영 환경에서는 AUTH_MODE=supabase가 필요합니다.")
        if self.app_env == "production" and not self.database_url.startswith(
            "postgresql+asyncpg://"
        ):
            raise ValueError(
                "운영 환경에서는 postgresql+asyncpg DATABASE_URL이 필요합니다."
            )
        if self.auth_mode == "supabase" and (
            not self.supabase_url or not self.supabase_publishable_key
        ):
            raise ValueError(
                "Supabase 인증에는 SUPABASE_URL과 SUPABASE_PUBLISHABLE_KEY가 필요합니다."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
