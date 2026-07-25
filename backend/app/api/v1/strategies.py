from fastapi import APIRouter

from app.schemas.strategy import StrategyRequest, StrategyResponse
from app.services.strategy import strategy_service

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("/recommend", response_model=StrategyResponse)
async def recommend_strategy(request: StrategyRequest) -> StrategyResponse:
    return strategy_service.recommend(request)
