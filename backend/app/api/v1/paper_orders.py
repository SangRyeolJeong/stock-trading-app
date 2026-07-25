from fastapi import APIRouter, HTTPException, status

from app.schemas.paper import PaperOrder, PaperOrderRequest
from app.services.market import market_data_service
from app.services.paper_trading import paper_trading_service

router = APIRouter(prefix="/paper/orders", tags=["paper-trading"])


@router.post("", response_model=PaperOrder, status_code=status.HTTP_201_CREATED)
async def create_paper_order(order: PaperOrderRequest) -> PaperOrder:
    quote = await market_data_service.get_quote(order.symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail="시세를 찾을 수 없습니다.")
    return paper_trading_service.execute_immediately(order, quote)
