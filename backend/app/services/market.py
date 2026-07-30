import asyncio
import random
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, TypeVar
from zoneinfo import ZoneInfo

from app.core.config import Settings, get_settings
from app.core.exceptions import MarketDataError
from app.integrations.kis.client import KisClient
from app.schemas.market import (
    Candle,
    CandleSeries,
    ExchangeRate,
    OrderBook,
    OrderBookLevel,
    Quote,
    SecurityOverview,
)
from app.services.instruments import InstrumentCatalog

T = TypeVar("T")


class MarketDataProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote | None: ...
    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate | None: ...
    async def get_candles(self, symbol: str, limit: int = 120) -> CandleSeries | None: ...
    async def get_orderbook(self, symbol: str) -> OrderBook | None: ...
    async def get_overview(self, symbol: str) -> SecurityOverview | None: ...
    async def subscribe_quotes(self, symbol: str) -> AsyncIterator[dict[str, object]]: ...


def _mock_candles(symbol: str, price: Decimal, currency: str, limit: int) -> CandleSeries:
    rng = random.Random(symbol)
    cursor = datetime.now(UTC).date()
    close = price * Decimal("0.86")
    rows: list[Candle] = []
    while len(rows) < limit:
        if cursor.weekday() < 5:
            change = Decimal(str(rng.uniform(-0.025, 0.027)))
            open_price = close
            close = max(Decimal("0.01"), open_price * (Decimal("1") + change))
            high = max(open_price, close) * Decimal(str(rng.uniform(1.001, 1.014)))
            low = min(open_price, close) * Decimal(str(rng.uniform(0.986, 0.999)))
            rows.append(
                Candle(
                    date=cursor,
                    open=open_price.quantize(Decimal("0.01")),
                    high=high.quantize(Decimal("0.01")),
                    low=low.quantize(Decimal("0.01")),
                    close=close.quantize(Decimal("0.01")),
                    volume=Decimal(rng.randint(200_000, 4_000_000)),
                )
            )
        cursor -= timedelta(days=1)
    rows.reverse()
    return CandleSeries(
        symbol=symbol,
        currency=currency,
        source="mock",
        candles=rows,
        as_of=datetime.now(UTC),
    )


class MockMarketDataProvider:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self._quotes = {
            "QQQM": Quote(
                symbol="QQQM",
                name="인베스코 나스닥 100 ETF",
                currency="USD",
                price=Decimal("231.72"),
                change=Decimal("2.94"),
                change_rate=Decimal("1.28"),
                market_open=True,
                as_of=now,
            ),
            "QQQ": Quote(
                symbol="QQQ",
                name="인베스코 QQQ",
                currency="USD",
                price=Decimal("612.45"),
                change=Decimal("5.18"),
                change_rate=Decimal("0.85"),
                market_open=True,
                as_of=now,
            ),
            "SPY": Quote(
                symbol="SPY",
                name="SPDR S&P 500 ETF",
                currency="USD",
                price=Decimal("729.46"),
                change=Decimal("-10.84"),
                change_rate=Decimal("-1.46"),
                market_open=True,
                as_of=now,
            ),
            "VOO": Quote(
                symbol="VOO",
                name="뱅가드 S&P 500 ETF",
                currency="USD",
                price=Decimal("671.20"),
                change=Decimal("-9.82"),
                change_rate=Decimal("-1.44"),
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
            "133690": Quote(
                symbol="133690",
                name="TIGER 미국나스닥100",
                currency="KRW",
                price=Decimal("164800"),
                change=Decimal("-1250"),
                change_rate=Decimal("-0.75"),
                market_open=False,
                as_of=now,
            ),
            "379800": Quote(
                symbol="379800",
                name="KODEX 미국S&P500",
                currency="KRW",
                price=Decimal("26035"),
                change=Decimal("65"),
                change_rate=Decimal("0.25"),
                market_open=False,
                as_of=now,
            ),
            "379810": Quote(
                symbol="379810",
                name="KODEX 미국나스닥100",
                currency="KRW",
                price=Decimal("28220"),
                change=Decimal("165"),
                change_rate=Decimal("0.59"),
                market_open=False,
                as_of=now,
            ),
            "AAPL": Quote(
                symbol="AAPL",
                name="애플",
                currency="USD",
                price=Decimal("219.31"),
                change=Decimal("2.00"),
                change_rate=Decimal("0.92"),
                market_open=True,
                as_of=now,
            ),
            "NVDA": Quote(
                symbol="NVDA",
                name="엔비디아",
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

    async def get_candles(self, symbol: str, limit: int = 120) -> CandleSeries | None:
        quote = await self.get_quote(symbol)
        if quote is None:
            return None
        return _mock_candles(quote.symbol, quote.price, quote.currency, limit)

    async def get_orderbook(self, symbol: str) -> OrderBook | None:
        quote = await self.get_quote(symbol)
        if quote is None:
            return None
        step = Decimal("10") if quote.currency == "KRW" else Decimal("0.01")
        rng = random.Random(f"orderbook:{quote.symbol}")
        asks = [
            OrderBookLevel(
                price=quote.price + step * level,
                quantity=Decimal(rng.randint(80, 2400)),
            )
            for level in range(1, 6)
        ]
        bids = [
            OrderBookLevel(
                price=max(step, quote.price - step * level),
                quantity=Decimal(rng.randint(80, 2400)),
            )
            for level in range(1, 6)
        ]
        return OrderBook(
            symbol=quote.symbol,
            currency=quote.currency,
            asks=asks,
            bids=bids,
            total_ask_quantity=sum((level.quantity for level in asks), Decimal("0")),
            total_bid_quantity=sum((level.quantity for level in bids), Decimal("0")),
            source="mock",
            delayed=True,
            as_of=datetime.now(UTC),
        )

    async def get_overview(self, symbol: str) -> SecurityOverview | None:
        quote = await self.get_quote(symbol)
        if quote is None:
            return None
        is_domestic = quote.currency == "KRW"
        return SecurityOverview(
            symbol=quote.symbol,
            name=quote.name,
            market="KRX" if is_domestic else "NASDAQ",
            asset_type=(
                "etf"
                if quote.symbol
                in {"QQQM", "QQQ", "SPY", "VOO", "360750", "133690", "379800", "379810"}
                else "stock"
            ),
            currency=quote.currency,
            open=quote.price - quote.change / Decimal("2"),
            high=quote.price * Decimal("1.015"),
            low=quote.price * Decimal("0.985"),
            volume=Decimal("1250000"),
            week_52_high=quote.price * Decimal("1.24"),
            week_52_low=quote.price * Decimal("0.72"),
            per=(
                None
                if quote.symbol
                in {"QQQM", "QQQ", "SPY", "VOO", "360750", "133690", "379800", "379810"}
                else Decimal("24.8")
            ),
            pbr=(
                None
                if quote.symbol
                in {"QQQM", "QQQ", "SPY", "VOO", "360750", "133690", "379800", "379810"}
                else Decimal("3.2")
            ),
            eps=(
                None
                if quote.symbol
                in {"QQQM", "QQQ", "SPY", "VOO", "360750", "133690", "379800", "379810"}
                else quote.price / Decimal("24.8")
            ),
            bps=(
                None
                if quote.symbol
                in {"QQQM", "QQQ", "SPY", "VOO", "360750", "133690", "379800", "379810"}
                else quote.price / Decimal("3.2")
            ),
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


def _object_output(payload: dict[str, Any], key: str) -> dict[str, Any]:
    output = payload.get(key)
    if isinstance(output, list):
        output = output[0] if output else None
    if not isinstance(output, dict):
        raise MarketDataError(f"KIS 시세 응답에 {key}가 없습니다.")
    return output


def _first_decimal(output: dict[str, Any], keys: tuple[str, ...]) -> Decimal:
    for key in keys:
        if key not in output or output[key] in ("", None):
            continue
        try:
            return Decimal(str(output[key]).replace(",", ""))
        except (InvalidOperation, TypeError):
            continue
    raise MarketDataError(f"KIS 응답에 유효한 {'/'.join(keys)} 값이 없습니다.")


def _optional_decimal(output: dict[str, Any], *keys: str) -> Decimal | None:
    for key in keys:
        value = output.get(key)
        if value in ("", None):
            continue
        try:
            parsed = Decimal(str(value).replace(",", ""))
        except (InvalidOperation, TypeError):
            continue
        return parsed if parsed != 0 else None
    return None


def _output_rows(payload: dict[str, Any], key: str = "output2") -> list[dict[str, Any]]:
    output = payload.get(key)
    if not isinstance(output, list):
        raise MarketDataError(f"KIS 시세 응답에 {key}가 없습니다.")
    return [row for row in output if isinstance(row, dict)]


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
    def __init__(
        self,
        settings: Settings,
        client: KisClient | None = None,
        catalog: InstrumentCatalog | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or KisClient(settings)
        self._catalog = catalog or InstrumentCatalog(settings)

    def _identity(self, symbol: str) -> tuple[str, str, str]:
        normalized = symbol.strip().upper()
        instrument = self._catalog.resolve(normalized)
        default_exchange = (
            "KRX"
            if normalized.isdigit() and len(normalized) == 6
            else self._settings.kis_default_overseas_exchange
        )
        if instrument is None:
            return normalized, normalized, default_exchange
        return normalized, instrument.name, instrument.exchange_code

    async def get_quote(self, symbol: str) -> Quote | None:
        normalized, name, exchange = self._identity(symbol)
        if not normalized:
            return None
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

    async def get_candles(self, symbol: str, limit: int = 120) -> CandleSeries | None:
        normalized, _, exchange = self._identity(symbol)
        if not normalized:
            return None
        candles_by_date: dict[date, Candle] = {}
        if exchange == "KRX":
            end_date = datetime.now(ZoneInfo("Asia/Seoul")).date()
            start_date = end_date - timedelta(days=max(limit * 2, 180))
            for _ in range(5):
                payload = await self._client.get_domestic_daily_chart(
                    normalized,
                    start_date=start_date,
                    end_date=end_date,
                )
                rows = _output_rows(payload)
                for row in rows:
                    if not row.get("stck_bsop_date"):
                        continue
                    candle = Candle(
                        date=datetime.strptime(str(row["stck_bsop_date"]), "%Y%m%d").date(),
                        open=_decimal(row, "stck_oprc"),
                        high=_decimal(row, "stck_hgpr"),
                        low=_decimal(row, "stck_lwpr"),
                        close=_decimal(row, "stck_clpr"),
                        volume=_decimal(row, "acml_vol"),
                    )
                    candles_by_date[candle.date] = candle
                if len(rows) < 100 or len(candles_by_date) >= limit:
                    break
                end_date = min(candles_by_date) - timedelta(days=1)
            currency: str = "KRW"
        else:
            before_date = None
            for _ in range(5):
                payload = await self._client.get_overseas_daily_prices(
                    normalized,
                    exchange,
                    before_date=before_date,
                )
                rows = _output_rows(payload)
                for row in rows:
                    if not row.get("xymd"):
                        continue
                    candle = Candle(
                        date=datetime.strptime(str(row["xymd"]), "%Y%m%d").date(),
                        open=_decimal(row, "open"),
                        high=_decimal(row, "high"),
                        low=_decimal(row, "low"),
                        close=_decimal(row, "clos"),
                        volume=_decimal(row, "tvol"),
                    )
                    candles_by_date[candle.date] = candle
                if len(rows) < 100 or len(candles_by_date) >= limit:
                    break
                before_date = min(candles_by_date) - timedelta(days=1)
            currency = "USD"
        candles = list(candles_by_date.values())
        candles.sort(key=lambda candle: candle.date)
        return CandleSeries(
            symbol=normalized,
            currency=currency,
            source="kis",
            candles=candles[-limit:],
            as_of=datetime.now(UTC),
        )

    async def get_orderbook(self, symbol: str) -> OrderBook | None:
        normalized, _, exchange = self._identity(symbol)
        if not normalized:
            return None
        now = datetime.now(UTC)
        if exchange == "KRX":
            output = _object_output(await self._client.get_domestic_orderbook(normalized), "output1")
            asks: list[OrderBookLevel] = []
            bids: list[OrderBookLevel] = []
            for level in range(1, 11):
                ask_price = _decimal(output, f"askp{level}")
                ask_quantity = _decimal(output, f"askp_rsqn{level}")
                bid_price = _decimal(output, f"bidp{level}")
                bid_quantity = _decimal(output, f"bidp_rsqn{level}")
                if ask_price > 0:
                    asks.append(OrderBookLevel(price=ask_price, quantity=max(ask_quantity, Decimal("0"))))
                if bid_price > 0:
                    bids.append(OrderBookLevel(price=bid_price, quantity=max(bid_quantity, Decimal("0"))))
            return OrderBook(
                symbol=normalized,
                currency="KRW",
                asks=asks,
                bids=bids,
                total_ask_quantity=_decimal(output, "total_askp_rsqn"),
                total_bid_quantity=_decimal(output, "total_bidp_rsqn"),
                source="kis",
                delayed=False,
                as_of=now,
            )

        output = _object_output(await self._client.get_overseas_orderbook(normalized, exchange), "output1")
        ask_price = _first_decimal(output, ("pask", "askp", "ask"))
        bid_price = _first_decimal(output, ("pbid", "bidp", "bid"))
        ask_quantity = _first_decimal(output, ("vask", "askp_rsqn1", "ask_qty"))
        bid_quantity = _first_decimal(output, ("vbid", "bidp_rsqn1", "bid_qty"))
        asks = [OrderBookLevel(price=ask_price, quantity=max(ask_quantity, Decimal("0")))] if ask_price > 0 else []
        bids = [OrderBookLevel(price=bid_price, quantity=max(bid_quantity, Decimal("0")))] if bid_price > 0 else []
        return OrderBook(
            symbol=normalized,
            currency="USD",
            asks=asks,
            bids=bids,
            total_ask_quantity=sum((level.quantity for level in asks), Decimal("0")),
            total_bid_quantity=sum((level.quantity for level in bids), Decimal("0")),
            source="kis",
            delayed=False,
            as_of=now,
        )

    async def get_overview(self, symbol: str) -> SecurityOverview | None:
        normalized, name, exchange = self._identity(symbol)
        if not normalized:
            return None
        instrument = self._catalog.resolve(normalized)
        asset_type = instrument.asset_type if instrument else "other"
        market = instrument.market if instrument else exchange
        if exchange == "KRX":
            output = _output(await self._client.get_domestic_quote(normalized))
            return SecurityOverview(
                symbol=normalized,
                name=name,
                market=market,
                asset_type=asset_type,
                currency="KRW",
                open=_optional_decimal(output, "stck_oprc"),
                high=_optional_decimal(output, "stck_hgpr"),
                low=_optional_decimal(output, "stck_lwpr"),
                volume=_optional_decimal(output, "acml_vol"),
                week_52_high=_optional_decimal(output, "w52_hgpr"),
                week_52_low=_optional_decimal(output, "w52_lwpr"),
                per=_optional_decimal(output, "per"),
                pbr=_optional_decimal(output, "pbr"),
                eps=_optional_decimal(output, "eps"),
                bps=_optional_decimal(output, "bps"),
                source="kis",
                as_of=datetime.now(UTC),
            )
        output = _output(await self._client.get_overseas_quote(normalized, exchange))
        return SecurityOverview(
            symbol=normalized,
            name=name,
            market=market,
            asset_type=asset_type,
            currency="USD",
            open=_optional_decimal(output, "open"),
            high=_optional_decimal(output, "high"),
            low=_optional_decimal(output, "low"),
            volume=_optional_decimal(output, "tvol"),
            week_52_high=_optional_decimal(output, "h52p"),
            week_52_low=_optional_decimal(output, "l52p"),
            per=_optional_decimal(output, "perx"),
            pbr=_optional_decimal(output, "pbrx"),
            eps=_optional_decimal(output, "epsx"),
            bps=_optional_decimal(output, "bpsx"),
            source="kis",
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


class CachedMarketDataProvider:
    def __init__(self, provider: MarketDataProvider, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings
        self._cache: dict[str, tuple[float, object]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def _cached(self, key: str, ttl: float, loader: Callable[[], Awaitable[T]]) -> T:
        now = asyncio.get_running_loop().time()
        cached = self._cache.get(key)
        if cached and now - cached[0] < ttl:
            return cached[1]  # type: ignore[return-value]
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            now = asyncio.get_running_loop().time()
            cached = self._cache.get(key)
            if cached and now - cached[0] < ttl:
                return cached[1]  # type: ignore[return-value]
            value = await loader()
            self._cache[key] = (now, value)
            return value

    async def get_quote(self, symbol: str) -> Quote | None:
        normalized = symbol.strip().upper()
        return await self._cached(
            f"quote:{normalized}",
            self._settings.market_quote_cache_seconds,
            lambda: self._provider.get_quote(normalized),
        )

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate | None:
        base, quote = base_currency.upper(), quote_currency.upper()
        return await self._cached(
            f"fx:{base}:{quote}",
            self._settings.market_fx_cache_seconds,
            lambda: self._provider.get_exchange_rate(base, quote),
        )

    async def get_candles(self, symbol: str, limit: int = 120) -> CandleSeries | None:
        normalized = symbol.strip().upper()
        return await self._cached(
            f"candles:{normalized}:{limit}",
            self._settings.market_chart_cache_seconds,
            lambda: self._provider.get_candles(normalized, limit),
        )

    async def get_orderbook(self, symbol: str) -> OrderBook | None:
        normalized = symbol.strip().upper()
        return await self._cached(
            f"orderbook:{normalized}",
            self._settings.market_quote_cache_seconds,
            lambda: self._provider.get_orderbook(normalized),
        )

    async def get_overview(self, symbol: str) -> SecurityOverview | None:
        normalized = symbol.strip().upper()
        return await self._cached(
            f"overview:{normalized}",
            self._settings.market_quote_cache_seconds,
            lambda: self._provider.get_overview(normalized),
        )

    async def subscribe_quotes(self, symbol: str) -> AsyncIterator[dict[str, object]]:
        if isinstance(self._provider, MockMarketDataProvider):
            async for tick in self._provider.subscribe_quotes(symbol):
                yield tick
            return
        while True:
            quote = await self.get_quote(symbol)
            if quote is None:
                return
            yield {
                "symbol": quote.symbol,
                "price": float(quote.price),
                "as_of": quote.as_of.isoformat(),
                "source": "kis-rest-cache",
            }
            await asyncio.sleep(max(3.0, self._settings.market_quote_cache_seconds))


def create_market_data_service(
    settings: Settings | None = None,
    catalog: InstrumentCatalog | None = None,
) -> MarketDataProvider:
    resolved_settings = settings or get_settings()
    if resolved_settings.market_data_provider == "kis":
        provider: MarketDataProvider = KisMarketDataProvider(resolved_settings, catalog=catalog)
    else:
        provider = MockMarketDataProvider()
    return CachedMarketDataProvider(provider, resolved_settings)


settings = get_settings()
instrument_catalog = InstrumentCatalog(settings)
market_data_service = create_market_data_service(settings, instrument_catalog)
