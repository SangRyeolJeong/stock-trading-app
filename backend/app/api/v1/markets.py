from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.exceptions import MarketDataError
from app.schemas.market import ExchangeRate, Quote
from app.services.market import market_data_service

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/quotes/{symbol}", response_model=Quote)
async def get_quote(symbol: str) -> Quote:
    try:
        quote = await market_data_service.get_quote(symbol)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if quote is None:
        raise HTTPException(status_code=404, detail="시세를 찾을 수 없습니다.")
    return quote


@router.get("/exchange-rates/{base_currency}/{quote_currency}", response_model=ExchangeRate)
async def get_exchange_rate(base_currency: str, quote_currency: str) -> ExchangeRate:
    try:
        exchange_rate = await market_data_service.get_exchange_rate(base_currency, quote_currency)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if exchange_rate is None:
        raise HTTPException(status_code=404, detail="지원하지 않는 통화쌍입니다.")
    return exchange_rate


@router.websocket("/ws/quotes/{symbol}")
async def quote_stream(websocket: WebSocket, symbol: str) -> None:
    try:
        quote = await market_data_service.get_quote(symbol)
    except MarketDataError:
        await websocket.close(code=1011)
        return
    if quote is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    try:
        try:
            async for tick in market_data_service.subscribe_quotes(quote.symbol):
                await websocket.send_json(tick)
        except MarketDataError:
            await websocket.close(code=1011)
    except WebSocketDisconnect:
        return
