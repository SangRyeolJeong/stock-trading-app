from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session

router = APIRouter(tags=["system"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "moa-api",
        "environment": settings.app_env,
        "market_provider": settings.market_data_provider,
    }


@router.get("/ready")
async def readiness_check(session: Session) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="데이터베이스에 연결할 수 없습니다.",
        ) from exc
    return {
        "status": "ready",
        "database": "ok",
    }
