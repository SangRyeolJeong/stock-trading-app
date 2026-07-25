import asyncio
import random
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from app.schemas.market import Quote


class MarketDataProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote | None: ...
    async def subscribe_quotes(self, symbol: str) -> AsyncIterator[dict[str, object]]: ...


class MockMarketDataProvider:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self._quotes = {
            "QQQM": Quote(
                symbol="QQQM",
                name="Invesco NASDAQ 100 ETF",
                currency="USD",
                price=Decimal("231.72"),
                change=Decimal("2.94"),
                change_rate=Decimal("1.28"),
                market_open=True,
                as_of=now,
            ),
            "005930": Quote(
                symbol="005930",
                name="삼성전자",
                currency="KRW",
                price=Decimal("82400"),
                change=Decimal("500"),
                change_rate=Decimal("0.61"),
                market_open=False,
                as_of=now,
            ),
            "360750": Quote(
                symbol="360750",
                name="TIGER 미국S&P500",
                currency="KRW",
                price=Decimal("22165"),
                change=Decimal("-75"),
                change_rate=Decimal("-0.34"),
                market_open=False,
                as_of=now,
            ),
            "AAPL": Quote(
                symbol="AAPL",
                name="Apple",
                currency="USD",
                price=Decimal("219.31"),
                change=Decimal("2.00"),
                change_rate=Decimal("0.92"),
                market_open=True,
                as_of=now,
            ),
        }

    async def get_quote(self, symbol: str) -> Quote | None:
        quote = self._quotes.get(symbol.upper())
        if quote is None:
            return None
        return quote.model_copy(update={"as_of": datetime.now(UTC)})

    async def subscribe_quotes(self, symbol: str) -> AsyncIterator[dict[str, object]]:
        quote = self._quotes[symbol]
        price = float(quote.price)
        while True:
            price = max(0.01, price + random.uniform(-0.18, 0.18))
            yield {
                "symbol": symbol,
                "price": round(price, 2),
                "as_of": datetime.now(UTC).isoformat(),
                "source": "demo",
            }
            await asyncio.sleep(1)


market_data_service: MarketDataProvider = MockMarketDataProvider()
