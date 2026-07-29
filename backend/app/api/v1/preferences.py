from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_session
from app.schemas.preferences import UserPreferencesPayload, UserPreferencesResponse
from app.services.preferences import user_preferences_service

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
router = APIRouter(prefix="/me/preferences", tags=["user-preferences"])


@router.get("", response_model=UserPreferencesResponse)
async def get_user_preferences(
    session: Session,
    user: CurrentUser,
) -> UserPreferencesResponse:
    preferences = await user_preferences_service.get(session, user.id)
    if preferences is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 사용자 설정이 없습니다.",
        )
    return preferences


@router.put("", response_model=UserPreferencesResponse)
async def put_user_preferences(
    payload: UserPreferencesPayload,
    session: Session,
    user: CurrentUser,
) -> UserPreferencesResponse:
    return await user_preferences_service.upsert(session, user.id, payload)
