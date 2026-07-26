import asyncio
import random
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from app.core.config import Settings, get_settings
from app.core.exceptions import MarketDataError
from app.integrations.kis.client import KisClient
from app.schemas.market import ExchangeRate, Quote


class MarketDataProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote | None: ...
    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate | None: ...
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
            "NVDA": Quote(
                symbol="NVDA",
                name="NVIDIA",
                currency="USD",
                price=Decimal("174.92"),
                change=Decimal("4.12"),
                change_rate=Decimal("2.41"),
                market_open=True,
                as_of=now,
            ),
        }

    async def get_quote(self, symbol: str) -> Quote | None:
        quote = self._quotes.get(symbol.upper())
        if quote is None:
            return None
        return quote.model_copy(update={"as_of": datetime.now(UTC)})

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate | None:
        pair = (base_currency.upper(), quote_currency.upper())
        if pair == ("USD", "KRW"):
            rate = Decimal("1385.20")
        elif pair == ("KRW", "USD"):
            rate = Decimal("1") / Decimal("1385.20")
        elif pair[0] == pair[1] and pair[0] in {"KRW", "USD"}:
            rate = Decimal("1")
        else:
            return None
        return ExchangeRate(
            base_currency=pair[0],
            quote_currency=pair[1],
            rate=rate,
            source="mock",
            as_of=datetime.now(UTC),
        )

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


INSTRUMENTS: dict[str, tuple[str, str]] = {
    "005930": ("삼성전자", "KRX"),
    "360750": ("TIGER 미국S&P500", "KRX"),
    "AAPL": ("Apple", "NAS"),
    "NVDA": ("NVIDIA", "NAS"),
    "QQQM": ("Invesco NASDAQ 100 ETF", "NAS"),
}


def _decimal(output: dict[str, Any], key: str) -> Decimal:
    try:
        return Decimal(str(output[key]).replace(",", ""))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise MarketDataError(f"KIS 응답에 유효한 {key} 값이 없습니다.") from exc


def _signed(value: Decimal, sign_code: object) -> Decimal:
    if value < 0:
        return value
    return -value if str(sign_code) in {"4", "5"} else value


def _output(payload: dict[str, Any]) -> dict[str, Any]:
    output = payload.get("output")
    if isinstance(output, list):
        output = output[0] if output else None
    if not isinstance(output, dict):
        raise MarketDataError("KIS 시세 응답에 output이 없습니다.")
    return output


def _is_market_open(exchange: str, now: datetime | None = None) -> bool:
    utc_now = now or datetime.now(UTC)
    timezone = ZoneInfo("Asia/Seoul") if exchange == "KRX" else ZoneInfo("America/New_York")
    local_now = utc_now.astimezone(timezone)
    if local_now.weekday() >= 5:
        return False
    if exchange == "KRX":
        return time(9, 0) <= local_now.time() <= time(15, 30)
    return time(9, 30) <= local_now.time() <= time(16, 0)


class KisMarketDataProvider:
    def __init__(self, settings: Settings, client: KisClient | None = None) -> None:
        self._settings = settings
        self._client = client or KisClient(settings)

    async def get_quote(self, symbol: str) -> Quote | None:
        normalized = symbol.strip().upper()
        if not normalized:
            return None
        default_exchange = (
            "KRX"
            if normalized.isdigit() and len(normalized) == 6
            else self._settings.kis_default_overseas_exchange
        )
        name, exchange = INSTRUMENTS.get(normalized, (normalized, default_exchange))
        now = datetime.now(UTC)

        if exchange == "KRX":
            output = _output(await self._client.get_domestic_quote(normalized))
            change = _signed(_decimal(output, "prdy_vrss"), output.get("prdy_vrss_sign"))
            change_rate = _signed(_decimal(output, "prdy_ctrt"), output.get("prdy_vrss_sign"))
            return Quote(
                symbol=normalized,
                name=name,
                currency="KRW",
                price=_decimal(output, "stck_prpr"),
                change=change,
                change_rate=change_rate,
                market_open=_is_market_open(exchange, now),
                delayed=False,
                as_of=now,
            )

        output = _output(await self._client.get_overseas_quote(normalized, exchange))
        change = _signed(_decimal(output, "diff"), output.get("sign"))
        change_rate = _signed(_decimal(output, "rate"), output.get("sign"))
        return Quote(
            symbol=normalized,
            name=name,
            currency="USD",
            price=_decimal(output, "last"),
            change=change,
            change_rate=change_rate,
            market_open=_is_market_open(exchange, now),
            delayed=False,
            as_of=now,
        )

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate | None:
        pair = (base_currency.upper(), quote_currency.upper())
        if pair[0] not in {"KRW", "USD"} or pair[1] not in {"KRW", "USD"}:
            return None
        if pair[0] == pair[1]:
            rate = Decimal("1")
        else:
            payload = await self._client.get_overseas_quote_detail(
                self._settings.kis_fx_probe_symbol,
                self._settings.kis_fx_probe_exchange,
            )
            usd_krw = _decimal(_output(payload), "t_rate")
            if usd_krw <= 0:
                raise MarketDataError("KIS 환율은 0보다 커야 합니다.")
            rate = usd_krw if pair == ("USD", "KRW") else Decimal("1") / usd_krw
        return ExchangeRate(
            base_currency=pair[0],
            quote_currency=pair[1],
            rate=rate,
            source="kis",
            delayed=False,
            as_of=datetime.now(UTC),
        )

    async def subscribe_quotes(self, symbol: str) -> AsyncIterator[dict[str, object]]:
        while True:
            quote = await self.get_quote(symbol)
            if quote is None:
                return
            yield {
                "symbol": quote.symbol,
                "price": float(quote.price),
                "as_of": quote.as_of.isoformat(),
                "source": "kis-rest",
            }
            await asyncio.sleep(5)


def create_market_data_service(settings: Settings | None = None) -> MarketDataProvider:
    resolved_settings = settings or get_settings()
    if resolved_settings.market_data_provider == "kis":
        return KisMarketDataProvider(resolved_settings)
    return MockMarketDataProvider()


market_data_service = create_market_data_service()
