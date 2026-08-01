from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any, Literal

import httpx

KODEX_API_URL = "https://www.samsungfund.com/api/v1/kodex/product/{product_id}.do"
TIGER_OVERVIEW_URL = (
    "https://investments.miraeasset.com/tigeretf/ko/product/search/detail/pdf.ajax"
)
TIGER_HOLDINGS_URL = (
    "https://investments.miraeasset.com/tigeretf/ko/product/search/detail/pdfListAjax.ajax"
)


@dataclass(frozen=True)
class EtfSourceConfig:
    symbol: str
    provider: Literal["kodex", "tiger"]
    source_id: str


@dataclass(frozen=True)
class OfficialHolding:
    symbol: str
    name: str
    weight_pct: Decimal


@dataclass(frozen=True)
class OfficialSnapshot:
    symbol: str
    facts_as_of: date
    holdings_as_of: date
    holdings_count: int
    top_holdings: tuple[OfficialHolding, ...]


@dataclass(frozen=True)
class SnapshotAssessment:
    status: Literal["current", "update_available", "source_older", "future"]
    message: str


SOURCE_CONFIGS = {
    "379800": EtfSourceConfig("379800", "kodex", "2ETFE4"),
    "379810": EtfSourceConfig("379810", "kodex", "2ETFE3"),
    "360750": EtfSourceConfig("360750", "tiger", "KR7360750004"),
    "133690": EtfSourceConfig("133690", "tiger", "KR7133690008"),
}
SUPPORTED_SOURCE_SYMBOLS = tuple(SOURCE_CONFIGS)


class EtfSourceError(ValueError):
    """Raised when an official source response is missing required ETF data."""


def _compact_date(value: object, field_name: str) -> date:
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except ValueError as exc:
        raise EtfSourceError(f"{field_name} 날짜 형식이 올바르지 않습니다: {value}") from exc


def _display_date(value: object, field_name: str) -> date:
    try:
        return datetime.strptime(str(value), "%Y.%m.%d").date()
    except ValueError as exc:
        raise EtfSourceError(f"{field_name} 날짜 형식이 올바르지 않습니다: {value}") from exc


def _decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as exc:
        raise EtfSourceError(f"{field_name} 숫자 형식이 올바르지 않습니다: {value}") from exc


def _us_equity_symbol(value: object) -> str | None:
    raw = " ".join(str(value).strip().split())
    if not raw.upper().endswith(" US EQUITY"):
        return None
    return raw[: -len(" US EQUITY")].strip().upper().replace("/", ".")


def parse_kodex_snapshot(payload: dict[str, Any], expected_symbol: str) -> OfficialSnapshot:
    try:
        product = payload["info"]["product"]
        pdf = payload["pdf"]
        source_symbol = str(product["stkTicker"])
        holdings_count = int(pdf["totalCnt"])
        raw_holdings = pdf["list"]
    except (KeyError, TypeError, ValueError) as exc:
        raise EtfSourceError("KODEX 응답에 필수 상품·구성종목 정보가 없습니다.") from exc

    if source_symbol != expected_symbol:
        raise EtfSourceError(
            f"KODEX 응답 종목코드가 요청과 다릅니다: {source_symbol} != {expected_symbol}"
        )
    if not isinstance(raw_holdings, list):
        raise EtfSourceError("KODEX 구성종목 목록 형식이 올바르지 않습니다.")

    holdings: list[OfficialHolding] = []
    for item in raw_holdings:
        if not isinstance(item, dict):
            continue
        symbol = _us_equity_symbol(item.get("itmNo"))
        if symbol is None:
            continue
        weight = _decimal(item.get("ratio"), "KODEX 구성종목 비중")
        if weight <= 0:
            continue
        holdings.append(
            OfficialHolding(
                symbol=symbol,
                name=" ".join(str(item.get("secNm", symbol)).split()),
                weight_pct=weight,
            )
        )

    if not holdings:
        raise EtfSourceError("KODEX 응답에서 미국 주식 구성종목을 찾지 못했습니다.")
    holdings.sort(key=lambda item: item.weight_pct, reverse=True)
    return OfficialSnapshot(
        symbol=expected_symbol,
        facts_as_of=_compact_date(product.get("gijunYMD"), "KODEX 상품 기준일"),
        holdings_as_of=_compact_date(pdf.get("gijunYMD"), "KODEX 구성종목 기준일"),
        holdings_count=holdings_count,
        top_holdings=tuple(holdings[:10]),
    )


class _TigerOverviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.snapshot_date: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "input" and attributes.get("name") == "fixDate" and self.snapshot_date is None:
            self.snapshot_date = attributes.get("value")


class _TigerHoldingsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.total_count: int | None = None
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "tr":
            self._row = []
            raw_count = attributes.get("data-tot-cnt")
            if raw_count and self.total_count is None:
                try:
                    self.total_count = int(raw_count)
                except ValueError as exc:
                    raise EtfSourceError(f"TIGER 구성종목 수가 올바르지 않습니다: {raw_count}") from exc
        elif tag == "td" and self._row is not None:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._cell_parts is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell_parts).split()))
            self._cell_parts = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
            self._cell_parts = None


def parse_tiger_snapshot(
    overview_html: str,
    holdings_html: str,
    expected_symbol: str,
) -> OfficialSnapshot:
    overview_parser = _TigerOverviewParser()
    overview_parser.feed(overview_html)
    if overview_parser.snapshot_date is None:
        raise EtfSourceError("TIGER 응답에서 구성종목 기준일을 찾지 못했습니다.")

    holdings_parser = _TigerHoldingsParser()
    holdings_parser.feed(holdings_html)
    if holdings_parser.total_count is None:
        raise EtfSourceError("TIGER 응답에서 전체 구성종목 수를 찾지 못했습니다.")

    holdings: list[OfficialHolding] = []
    for row in holdings_parser.rows:
        if len(row) < 5:
            continue
        symbol = _us_equity_symbol(row[0])
        if symbol is None:
            continue
        weight = _decimal(row[4], "TIGER 구성종목 비중")
        if weight <= 0:
            continue
        holdings.append(OfficialHolding(symbol=symbol, name=row[1], weight_pct=weight))

    if not holdings:
        raise EtfSourceError("TIGER 응답에서 미국 주식 구성종목을 찾지 못했습니다.")
    holdings.sort(key=lambda item: item.weight_pct, reverse=True)
    snapshot_date = _display_date(overview_parser.snapshot_date, "TIGER 구성종목 기준일")
    return OfficialSnapshot(
        symbol=expected_symbol,
        facts_as_of=snapshot_date,
        holdings_as_of=snapshot_date,
        holdings_count=holdings_parser.total_count,
        top_holdings=tuple(holdings[:10]),
    )


def assess_snapshot(
    snapshot: OfficialSnapshot,
    *,
    checked_facts_as_of: date,
    checked_holdings_as_of: date,
    as_of: date | None = None,
) -> SnapshotAssessment:
    reference_date = as_of or date.today()
    if max(snapshot.facts_as_of, snapshot.holdings_as_of) > reference_date:
        return SnapshotAssessment(
            status="future",
            message="공식 응답 기준일이 현재보다 미래여서 자동 반영할 수 없습니다.",
        )
    if (
        snapshot.facts_as_of > checked_facts_as_of
        or snapshot.holdings_as_of > checked_holdings_as_of
    ):
        return SnapshotAssessment(
            status="update_available",
            message="저장소 스냅샷보다 새로운 공식 자료가 있습니다.",
        )
    if (
        snapshot.facts_as_of < checked_facts_as_of
        or snapshot.holdings_as_of < checked_holdings_as_of
    ):
        return SnapshotAssessment(
            status="source_older",
            message="공식 응답이 저장소 스냅샷보다 오래되었습니다.",
        )
    return SnapshotAssessment(status="current", message="저장소 스냅샷이 공식 자료와 같습니다.")


def fetch_official_snapshot(
    symbol: str,
    *,
    client: httpx.Client | None = None,
) -> OfficialSnapshot:
    normalized_symbol = symbol.strip().upper()
    try:
        config = SOURCE_CONFIGS[normalized_symbol]
    except KeyError as exc:
        raise EtfSourceError(f"자동 점검을 지원하지 않는 ETF입니다: {symbol}") from exc

    owns_client = client is None
    active_client = client or httpx.Client(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "MOA ETF source checker/1.0"},
    )
    try:
        if config.provider == "kodex":
            response = active_client.get(KODEX_API_URL.format(product_id=config.source_id))
            response.raise_for_status()
            return parse_kodex_snapshot(response.json(), normalized_symbol)

        overview_response = active_client.post(TIGER_OVERVIEW_URL, data={"ksdFund": config.source_id})
        overview_response.raise_for_status()
        overview_parser = _TigerOverviewParser()
        overview_parser.feed(overview_response.text)
        if overview_parser.snapshot_date is None:
            raise EtfSourceError("TIGER 응답에서 구성종목 기준일을 찾지 못했습니다.")
        holdings_response = active_client.post(
            TIGER_HOLDINGS_URL,
            data={
                "ksdFund": config.source_id,
                "fixDate": overview_parser.snapshot_date,
                "prfPrd": "Week01",
                "order": "SRD",
                "pageIndex": "1",
                "firstIndex": "0",
                "listCnt": "20",
            },
        )
        holdings_response.raise_for_status()
        return parse_tiger_snapshot(
            overview_response.text,
            holdings_response.text,
            normalized_symbol,
        )
    finally:
        if owns_client:
            active_client.close()
