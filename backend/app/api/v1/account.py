from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_session
from app.schemas.account import AccountDeletionRequest, AccountDeletionResponse
from app.services.account_deletion import (
    AccountDeletionBlockedError,
    account_deletion_service,
)

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
router = APIRouter(prefix="/me", tags=["account"])


@router.delete("", response_model=AccountDeletionResponse)
async def delete_current_user_data(
    payload: AccountDeletionRequest,
    session: Session,
    user: CurrentUser,
) -> AccountDeletionResponse:
    try:
        return await account_deletion_service.delete_user_data(session, user.id)
    except AccountDeletionBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
