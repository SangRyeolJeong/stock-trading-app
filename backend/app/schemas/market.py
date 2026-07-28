from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


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


class ExchangeRate(BaseModel):
    base_currency: Literal["KRW", "USD"]
    quote_currency: Literal["KRW", "USD"]
    rate: Decimal
    source: Literal["mock", "kis"]
    delayed: bool = True
    as_of: datetime


class Instrument(BaseModel):
    symbol: str
    name: str
    english_name: str | None = None
    market: str
    exchange_code: str
    currency: Literal["KRW", "USD"]
    asset_type: Literal["stock", "etf", "etn", "index", "other"]
    country: Literal["KR", "US"]


class InstrumentSearchResponse(BaseModel):
    items: list[Instrument]
    total: int
    source: Literal["builtin", "kis-master", "kis-master-cache"]
    updated_at: datetime


class Candle(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class CandleSeries(BaseModel):
    symbol: str
    currency: Literal["KRW", "USD"]
    interval: Literal["1d"] = "1d"
    source: Literal["mock", "kis"]
    candles: list[Candle]
    as_of: datetime


class OrderBookLevel(BaseModel):
    price: Decimal
    quantity: Decimal


class OrderBook(BaseModel):
    symbol: str
    currency: Literal["KRW", "USD"]
    asks: list[OrderBookLevel]
    bids: list[OrderBookLevel]
    total_ask_quantity: Decimal
    total_bid_quantity: Decimal
    source: Literal["mock", "kis"]
    delayed: bool = True
    as_of: datetime


class SecurityOverview(BaseModel):
    symbol: str
    name: str
    market: str
    asset_type: Literal["stock", "etf", "etn", "index", "other"]
    currency: Literal["KRW", "USD"]
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    volume: Decimal | None = None
    week_52_high: Decimal | None = None
    week_52_low: Decimal | None = None
    per: Decimal | None = None
    pbr: Decimal | None = None
    eps: Decimal | None = None
    bps: Decimal | None = None
    source: Literal["mock", "kis"]
    as_of: datetime
