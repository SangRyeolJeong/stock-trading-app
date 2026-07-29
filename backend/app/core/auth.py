from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.core.config import get_settings

DEMO_USER_ID = "demo-user"


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    email: str | None = None


bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


@lru_cache
def _supabase_client(url: str, publishable_key: str) -> Client:
    return create_client(url, publishable_key)


async def get_current_user(credentials: BearerCredentials) -> AuthenticatedUser:
    settings = get_settings()
    if settings.auth_mode == "demo":
        return AuthenticatedUser(id=DEMO_USER_ID)

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert settings.supabase_url is not None
    assert settings.supabase_publishable_key is not None
    client = _supabase_client(settings.supabase_url, settings.supabase_publishable_key)
    try:
        response = await run_in_threadpool(client.auth.get_user, credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = response.user if response is not None else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthenticatedUser(id=str(user.id), email=user.email)
