import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import auth
from app.core.config import Settings


def supabase_settings() -> Settings:
    return Settings(
        _env_file=None,
        auth_mode="supabase",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="sb_publishable_example",
    )


def test_demo_auth_returns_demo_user_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(_env_file=None, auth_mode="demo"),
    )

    user = asyncio.run(auth.get_current_user(None))

    assert user.id == "demo-user"


def test_supabase_auth_requires_bearer_credentials(monkeypatch) -> None:
    monkeypatch.setattr(auth, "get_settings", supabase_settings)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(auth.get_current_user(None))

    assert exc_info.value.status_code == 401


def test_supabase_auth_uses_verified_user_response(monkeypatch) -> None:
    class FakeAuthClient:
        def get_user(self, token: str) -> SimpleNamespace:
            assert token == "verified-token"
            return SimpleNamespace(
                user=SimpleNamespace(
                    id="4b669084-3419-42b7-b260-646f792d1171",
                    email="investor@example.com",
                )
            )

    fake_client = SimpleNamespace(auth=FakeAuthClient())
    monkeypatch.setattr(auth, "get_settings", supabase_settings)
    monkeypatch.setattr(auth, "_supabase_client", lambda _url, _key: fake_client)

    user = asyncio.run(
        auth.get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="verified-token",
            )
        )
    )

    assert user.id == "4b669084-3419-42b7-b260-646f792d1171"
    assert user.email == "investor@example.com"
