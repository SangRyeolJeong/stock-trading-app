"""MOA API.

FastAPI is the single backend entry point.  It serves deterministic demo data
until Korea Investment credentials are configured, so the frontend can be
developed without brokerage access.
"""

from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class Quote(BaseModel):
    symbol: str
    name: str
    currency: Literal["KRW", "USD"]
    price: Decimal
    change: Decimal
    change_rate: Decimal
    market_open: bool
    delayed: bool = True
    as_of: datetime


class PaperOrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: int = Field(gt=0, le=100_000)
    limit_price: Decimal | None = Field(default=None, gt=0)
    account_id: str = "demo-account"


class PaperOrder(BaseModel):
    id: UUID
    status: Literal["accepted", "filled", "rejected"]
    symbol: str
    side: Literal["buy", "sell"]
    quantity: int
    filled_price: Decimal
    created_at: datetime


class StrategyRequest(BaseModel):
    goal: Literal["retirement", "lump_sum", "cashflow"] = "retirement"
    horizon_years: int = Field(default=30, ge=1, le=50)
    monthly_amount_krw: int = Field(default=500_000, ge=10_000)
    risk_profile: Literal["conservative", "balanced", "growth"] = "growth"


class StrategyResponse(BaseModel):
    title: str
    score: int
    allocation: dict[str, int]
    reasons: list[str]
    disclaimer: str


DEMO_QUOTES: dict[str, Quote] = {
    "QQQM": Quote(symbol="QQQM", name="Invesco NASDAQ 100 ETF", currency="USD", price=Decimal("231.72"), change=Decimal("2.94"), change_rate=Decimal("1.28"), market_open=True, as_of=datetime.now(timezone.utc)),
    "005930": Quote(symbol="005930", name="삼성전자", currency="KRW", price=Decimal("82400"), change=Decimal("500"), change_rate=Decimal("0.61"), market_open=False, as_of=datetime.now(timezone.utc)),
    "360750": Quote(symbol="360750", name="TIGER 미국S&P500", currency="KRW", price=Decimal("22165"), change=Decimal("-75"), change_rate=Decimal("-0.34"), market_open=False, as_of=datetime.now(timezone.utc)),
    "AAPL": Quote(symbol="AAPL", name="Apple", currency="USD", price=Decimal("219.31"), change=Decimal("2.00"), change_rate=Decimal("0.92"), market_open=True, as_of=datetime.now(timezone.utc)),
}

app = FastAPI(
    title="MOA Investment API",
    version="0.1.0",
    description="KIS market data, paper trading, portfolio and tax-strategy API",
)

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moa-api",
        "market_provider": "kis" if os.getenv("KIS_APP_KEY") else "demo",
    }


@app.get("/api/v1/markets/quotes/{symbol}", response_model=Quote)
async def get_quote(symbol: str) -> Quote:
    normalized = symbol.upper()
    quote = DEMO_QUOTES.get(normalized)
    if quote is None:
        raise HTTPException(status_code=404, detail="지원하지 않는 데모 종목입니다.")
    return quote.model_copy(update={"as_of": datetime.now(timezone.utc)})


@app.post("/api/v1/paper/orders", response_model=PaperOrder, status_code=201)
async def create_paper_order(order: PaperOrderRequest) -> PaperOrder:
    quote = DEMO_QUOTES.get(order.symbol.upper())
    if quote is None:
        raise HTTPException(status_code=404, detail="시세를 찾을 수 없습니다.")
    if order.order_type == "limit" and order.limit_price is None:
        raise HTTPException(status_code=422, detail="지정가 주문에는 가격이 필요합니다.")
    fill_price = order.limit_price if order.order_type == "limit" else quote.price
    return PaperOrder(
        id=uuid4(),
        status="filled",
        symbol=quote.symbol,
        side=order.side,
        quantity=order.quantity,
        filled_price=fill_price,
        created_at=datetime.now(timezone.utc),
    )


@app.post("/api/v1/strategies/recommend", response_model=StrategyResponse)
async def recommend_strategy(request: StrategyRequest) -> StrategyResponse:
    # Replace this deterministic ruleset with a versioned knowledge base + LLM
    # explanation layer.  Numerical calculations should remain deterministic.
    pension_weight = 40 if request.goal == "retirement" else 20
    growth_weight = 50 if request.risk_profile == "growth" else 35
    cash_weight = 100 - pension_weight - growth_weight
    return StrategyResponse(
        title="장기 성장 · 계좌 분산 전략",
        score=94 if request.horizon_years >= 20 else 82,
        allocation={
            "해외주식 직투": growth_weight,
            "연금저축 국내상장 ETF": pension_weight,
            "현금성 자산": cash_weight,
        },
        reasons=[
            "투자 기간이 길어 비용 차이가 누적될 수 있습니다.",
            "연금 목적 자금과 자유롭게 쓸 자금을 계좌별로 분리합니다.",
            "세액공제 계산은 규칙 엔진으로 검증하고 AI는 설명만 담당합니다.",
        ],
        disclaimer="예시 분석이며 투자 권유가 아닙니다. 세법과 상품 정보는 실행 전 다시 확인하세요.",
    )


@app.websocket("/api/v1/ws/quotes/{symbol}")
async def quote_stream(websocket: WebSocket, symbol: str) -> None:
    normalized = symbol.upper()
    quote = DEMO_QUOTES.get(normalized)
    if quote is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    price = float(quote.price)
    try:
        while True:
            price = max(0.01, price + random.uniform(-0.18, 0.18))
            await websocket.send_json({
                "symbol": normalized,
                "price": round(price, 2),
                "as_of": datetime.now(timezone.utc).isoformat(),
                "source": "demo",
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
