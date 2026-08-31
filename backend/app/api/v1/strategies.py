from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.strategy import (
    StrategyExplanationResponse,
    StrategyRequest,
    StrategyResponse,
)
from app.services.strategy import strategy_service
from app.services.strategy_explanation import (
    StrategyExplanationFailed,
    StrategyExplanationUnavailable,
    strategy_explanation_service,
)

router = APIRouter(prefix="/strategies", tags=["strategies"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


@router.post("/recommend", response_model=StrategyResponse)
async def recommend_strategy(request: StrategyRequest) -> StrategyResponse:
    return strategy_service.recommend(request)


@router.post("/explain", response_model=StrategyExplanationResponse)
async def explain_strategy(
    request: StrategyRequest,
    user: CurrentUser,
) -> StrategyExplanationResponse:
    recommendation = strategy_service.recommend(request)
    try:
        return await strategy_explanation_service.explain(request, recommendation, user.id)
    except StrategyExplanationUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StrategyExplanationFailed as exc:
        raise HTTPException(
            status_code=502,
            detail="AI 전략 설명을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
