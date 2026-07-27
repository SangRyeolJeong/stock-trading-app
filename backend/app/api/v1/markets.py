from typing import Literal

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.core.exceptions import MarketDataError
from app.schemas.market import CandleSeries, ExchangeRate, InstrumentSearchResponse, Quote
from app.services.market import instrument_catalog, market_data_service

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


@router.get("/instruments", response_model=InstrumentSearchResponse)
async def search_instruments(
    query: str = Query(default="", max_length=80),
    market: Literal["all", "domestic", "overseas", "etf"] = "all",
    limit: int = Query(default=50, ge=1, le=100),
) -> InstrumentSearchResponse:
    return await instrument_catalog.search(query=query, market=market, limit=limit)


@router.get("/candles/{symbol}", response_model=CandleSeries)
async def get_candles(
    symbol: str,
    interval: Literal["1d"] = "1d",
    limit: int = Query(default=120, ge=10, le=500),
) -> CandleSeries:
    del interval
    try:
        candles = await market_data_service.get_candles(symbol, limit)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if candles is None:
        raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")
    return candles


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
