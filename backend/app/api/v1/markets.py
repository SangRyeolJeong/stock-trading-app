from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.schemas.market import Quote
from app.services.market import market_data_service

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/quotes/{symbol}", response_model=Quote)
async def get_quote(symbol: str) -> Quote:
    quote = await market_data_service.get_quote(symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail="지원하지 않는 데모 종목입니다.")
    return quote


@router.websocket("/ws/quotes/{symbol}")
async def quote_stream(websocket: WebSocket, symbol: str) -> None:
    quote = await market_data_service.get_quote(symbol)
    if quote is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    try:
        async for tick in market_data_service.subscribe_quotes(quote.symbol):
            await websocket.send_json(tick)
    except WebSocketDisconnect:
        return
