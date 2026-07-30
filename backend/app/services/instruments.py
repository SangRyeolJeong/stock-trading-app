import asyncio
import io
import json
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import httpx

from app.core.config import Settings
from app.schemas.market import Instrument, InstrumentSearchResponse

MarketFilter = Literal["all", "domestic", "overseas", "etf"]

DOMESTIC_MASTERS = {
    "KOSPI": (
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        228,
    ),
    "KOSDAQ": (
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
        222,
    ),
}
OVERSEAS_MASTERS = {
    "NAS": ("NASDAQ", "https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip"),
    "NYS": ("NYSE", "https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip"),
    "AMS": ("AMEX", "https://new.real.download.dws.co.kr/common/master/amsmst.cod.zip"),
}


def _instrument(
    symbol: str,
    name: str,
    market: str,
    exchange_code: str,
    currency: Literal["KRW", "USD"],
    asset_type: Literal["stock", "etf", "etn", "index", "other"] = "stock",
    english_name: str | None = None,
) -> Instrument:
    return Instrument(
        symbol=symbol,
        name=name,
        english_name=english_name,
        market=market,
        exchange_code=exchange_code,
        currency=currency,
        asset_type=asset_type,
        country="KR" if currency == "KRW" else "US",
    )


BUILTIN_INSTRUMENTS = [
    _instrument("005930", "삼성전자", "KOSPI", "KRX", "KRW"),
    _instrument("000660", "SK하이닉스", "KOSPI", "KRX", "KRW"),
    _instrument("035420", "NAVER", "KOSPI", "KRX", "KRW"),
    _instrument("035720", "카카오", "KOSPI", "KRX", "KRW"),
    _instrument("005380", "현대차", "KOSPI", "KRX", "KRW"),
    _instrument("000270", "기아", "KOSPI", "KRX", "KRW"),
    _instrument("051910", "LG화학", "KOSPI", "KRX", "KRW"),
    _instrument("006400", "삼성SDI", "KOSPI", "KRX", "KRW"),
    _instrument("207940", "삼성바이오로직스", "KOSPI", "KRX", "KRW"),
    _instrument("068270", "셀트리온", "KOSPI", "KRX", "KRW"),
    _instrument("360750", "TIGER 미국S&P500", "KOSPI", "KRX", "KRW", "etf"),
    _instrument("133690", "TIGER 미국나스닥100", "KOSPI", "KRX", "KRW", "etf"),
    _instrument("QQQM", "인베스코 나스닥 100 ETF", "NASDAQ", "NAS", "USD", "etf", "Invesco NASDAQ 100 ETF"),
    _instrument("QQQ", "인베스코 QQQ", "NASDAQ", "NAS", "USD", "etf", "Invesco QQQ"),
    _instrument("SPY", "SPDR S&P 500 ETF", "AMEX", "AMS", "USD", "etf", "SPDR S&P 500 ETF Trust"),
    _instrument("VOO", "뱅가드 S&P 500 ETF", "AMEX", "AMS", "USD", "etf", "Vanguard S&P 500 ETF"),
    _instrument("AAPL", "애플", "NASDAQ", "NAS", "USD", "stock", "Apple Inc."),
    _instrument("NVDA", "엔비디아", "NASDAQ", "NAS", "USD", "stock", "NVIDIA Corporation"),
    _instrument("MSFT", "마이크로소프트", "NASDAQ", "NAS", "USD", "stock", "Microsoft Corporation"),
    _instrument("TSLA", "테슬라", "NASDAQ", "NAS", "USD", "stock", "Tesla Inc."),
    _instrument("AMZN", "아마존", "NASDAQ", "NAS", "USD", "stock", "Amazon.com Inc."),
    _instrument("META", "메타", "NASDAQ", "NAS", "USD", "stock", "Meta Platforms Inc."),
    _instrument("GOOGL", "알파벳 A", "NASDAQ", "NAS", "USD", "stock", "Alphabet Inc."),
    _instrument("BRK.B", "버크셔 해서웨이 B", "NYSE", "NYS", "USD", "stock", "Berkshire Hathaway Inc."),
    _instrument("JPM", "JP모건 체이스", "NYSE", "NYS", "USD", "stock", "JPMorgan Chase & Co."),
]


def _asset_type_from_domestic(
    code: str,
    name: str,
    suffix: str,
) -> Literal["stock", "etf", "etn", "index", "other"]:
    normalized_name = name.upper()
    if "ETN" in normalized_name:
        return "etn"
    if "ETF" in normalized_name or (len(suffix) > 22 and suffix[22] == "Y"):
        return "etf"
    return {
        "ST": "stock",
        "EF": "etf",
        "FE": "etf",
        "EN": "etn",
    }.get(code, "stock")


def parse_domestic_master(content: bytes, market: str, suffix_size: int) -> list[Instrument]:
    instruments: list[Instrument] = []
    for raw_line in content.decode("cp949", errors="ignore").splitlines():
        # KIS 공식 파서의 suffix_size에는 행 끝의 개행 문자 1바이트가 포함된다.
        record_suffix_size = suffix_size - 1
        if len(raw_line) <= record_suffix_size + 21:
            continue
        prefix, suffix = raw_line[:-record_suffix_size], raw_line[-record_suffix_size:]
        symbol = prefix[:9].strip()
        name = prefix[21:].strip()
        if not symbol or not name or not symbol[:6].isdigit():
            continue
        instruments.append(
            _instrument(
                symbol[:6],
                name,
                market,
                "KRX",
                "KRW",
                _asset_type_from_domestic(suffix[:2], name, suffix),
            )
        )
    return instruments


def parse_overseas_master(content: bytes, market: str, exchange_code: str) -> list[Instrument]:
    instruments: list[Instrument] = []
    for index, raw_line in enumerate(content.decode("cp949", errors="ignore").splitlines()):
        columns = raw_line.split("\t")
        if index == 0 or len(columns) < 10:
            continue
        symbol, korean_name, english_name = columns[4].strip(), columns[6].strip(), columns[7].strip()
        if not symbol or not (korean_name or english_name):
            continue
        security_type = columns[8].strip()
        asset_type: Literal["stock", "etf", "etn", "index", "other"] = {
            "1": "index",
            "2": "stock",
            "3": "etf",
        }.get(security_type, "other")
        instruments.append(
            _instrument(
                symbol.upper(),
                korean_name or english_name,
                market,
                exchange_code,
                "USD",
                asset_type,
                english_name or None,
            )
        )
    return instruments


def _unzip_first(payload: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if not names:
            raise ValueError("종목 마스터 압축 파일이 비어 있습니다.")
        return archive.read(names[0])


class InstrumentCatalog:
    def __init__(self, settings: Settings, cache_path: Path | None = None) -> None:
        self._settings = settings
        self._cache_path = cache_path or Path(__file__).resolve().parents[2] / ".cache" / "kis-instruments.json"
        self._items = {item.symbol: item for item in BUILTIN_INSTRUMENTS}
        self._source: Literal["builtin", "kis-master", "kis-master-cache"] = "builtin"
        self._updated_at = datetime.now(UTC)
        self._loaded = False
        self._lock = asyncio.Lock()

    async def ensure_loaded(self) -> None:
        if self._loaded:
            return
        async with self._lock:
            if self._loaded:
                return
            if self._load_cache():
                self._loaded = True
                return
            if self._settings.app_env == "test" or not self._settings.kis_master_refresh_enabled:
                self._loaded = True
                return
            try:
                downloaded = await self._download()
            except (httpx.HTTPError, OSError, ValueError, zipfile.BadZipFile):
                self._loaded = True
                return
            self._items.update({item.symbol: item for item in downloaded})
            self._source = "kis-master"
            self._updated_at = datetime.now(UTC)
            self._save_cache()
            self._loaded = True

    def resolve(self, symbol: str) -> Instrument | None:
        return self._items.get(symbol.strip().upper())

    async def search(
        self,
        query: str = "",
        market: MarketFilter = "all",
        limit: int = 50,
    ) -> InstrumentSearchResponse:
        await self.ensure_loaded()
        needle = query.strip().casefold()

        def matches(item: Instrument) -> bool:
            if market == "domestic" and item.country != "KR":
                return False
            if market == "overseas" and item.country != "US":
                return False
            if market == "etf" and item.asset_type != "etf":
                return False
            haystack = f"{item.symbol} {item.name} {item.english_name or ''}".casefold()
            return not needle or needle in haystack

        filtered = [item for item in self._items.values() if matches(item)]
        filtered.sort(
            key=lambda item: (
                0 if needle and item.symbol.casefold().startswith(needle) else 1,
                0 if item.symbol in {entry.symbol for entry in BUILTIN_INSTRUMENTS} else 1,
                item.symbol,
            )
        )
        return InstrumentSearchResponse(
            items=filtered[:limit],
            total=len(filtered),
            source=self._source,
            updated_at=self._updated_at,
        )

    def _load_cache(self) -> bool:
        try:
            modified_at = datetime.fromtimestamp(self._cache_path.stat().st_mtime, tz=UTC)
            if datetime.now(UTC) - modified_at > timedelta(days=1):
                return False
            payload = json.loads(self._cache_path.read_text(encoding="utf-8"))
            if payload.get("version") != 3:
                return False
            cached = [Instrument.model_validate(item) for item in payload["items"]]
        except (OSError, ValueError, KeyError, TypeError):
            return False
        self._items.update({item.symbol: item for item in cached})
        self._source = "kis-master-cache"
        self._updated_at = modified_at
        return True

    def _save_cache(self) -> None:
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(
                json.dumps(
                    {
                        "version": 3,
                        "items": [item.model_dump(mode="json") for item in self._items.values()],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except OSError:
            return

    async def _download(self) -> list[Instrument]:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            requests = [
                client.get(url)
                for url, _ in DOMESTIC_MASTERS.values()
            ] + [
                client.get(url)
                for _, url in OVERSEAS_MASTERS.values()
            ]
            responses = await asyncio.gather(*requests)
        for response in responses:
            response.raise_for_status()

        downloaded: list[Instrument] = []
        response_index = 0
        for market, (_, suffix_size) in DOMESTIC_MASTERS.items():
            downloaded.extend(
                parse_domestic_master(_unzip_first(responses[response_index].content), market, suffix_size)
            )
            response_index += 1
        for exchange_code, (market, _) in OVERSEAS_MASTERS.items():
            downloaded.extend(
                parse_overseas_master(
                    _unzip_first(responses[response_index].content),
                    market,
                    exchange_code,
                )
            )
            response_index += 1
        return downloaded
