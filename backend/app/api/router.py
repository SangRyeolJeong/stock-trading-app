from fastapi import APIRouter

from app.api.v1 import health, markets, paper_orders, strategies
from app.core.config import get_settings

settings = get_settings()
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(markets.router, prefix=settings.api_v1_prefix)
api_router.include_router(paper_orders.router, prefix=settings.api_v1_prefix)
api_router.include_router(strategies.router, prefix=settings.api_v1_prefix)
