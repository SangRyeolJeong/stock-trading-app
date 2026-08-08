from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from app.services.etf_sources import (
    SUPPORTED_SOURCE_SYMBOLS,
    EtfSourceError,
    OfficialHolding,
    OfficialSnapshot,
)

SNAPSHOT_SCHEMA_VERSION = 1
DEFAULT_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "etf_official_snapshots.json"
)


def _date_value(value: object, field_name: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise EtfSourceError(f"{field_name} 날짜 형식이 올바르지 않습니다: {value}") from exc


def _holding(value: object, symbol: str) -> OfficialHolding:
    if not isinstance(value, dict):
        raise EtfSourceError(f"{symbol} 구성종목 형식이 올바르지 않습니다.")
    holding_symbol = str(value.get("symbol", "")).strip().upper()
    name = " ".join(str(value.get("name", "")).split())
    try:
        weight_pct = Decimal(str(value.get("weight_pct", "")))
    except InvalidOperation as exc:
        raise EtfSourceError(f"{symbol} 구성종목 비중이 올바르지 않습니다.") from exc
    if (
        not holding_symbol
        or not name
        or not weight_pct.is_finite()
        or weight_pct <= 0
        or weight_pct > 100
    ):
        raise EtfSourceError(f"{symbol} 구성종목 값이 올바르지 않습니다.")
    return OfficialHolding(symbol=holding_symbol, name=name, weight_pct=weight_pct)


def _snapshot(symbol: str, value: object) -> OfficialSnapshot:
    if not isinstance(value, dict):
        raise EtfSourceError(f"{symbol} 스냅샷 형식이 올바르지 않습니다.")
    source_symbol = str(value.get("symbol", "")).strip().upper()
    if source_symbol != symbol:
        raise EtfSourceError(f"스냅샷 종목코드가 키와 다릅니다: {source_symbol} != {symbol}")
    raw_holdings = value.get("top_holdings")
    if not isinstance(raw_holdings, list) or not raw_holdings or len(raw_holdings) > 10:
        raise EtfSourceError(f"{symbol} 상위 구성종목은 1~10개여야 합니다.")
    holdings = tuple(_holding(item, symbol) for item in raw_holdings)
    if len({item.symbol for item in holdings}) != len(holdings):
        raise EtfSourceError(f"{symbol} 상위 구성종목에 중복 종목코드가 있습니다.")
    try:
        holdings_count = int(value.get("holdings_count", 0))
    except (TypeError, ValueError) as exc:
        raise EtfSourceError(f"{symbol} 전체 구성종목 수가 올바르지 않습니다.") from exc
    if holdings_count < len(holdings):
        raise EtfSourceError(f"{symbol} 전체 구성종목 수가 상위 목록보다 작습니다.")
    return OfficialSnapshot(
        symbol=symbol,
        facts_as_of=_date_value(value.get("facts_as_of"), f"{symbol} 상품 기준일"),
        holdings_as_of=_date_value(value.get("holdings_as_of"), f"{symbol} 구성종목 기준일"),
        holdings_count=holdings_count,
        top_holdings=holdings,
    )


def parse_snapshot_document(value: object) -> dict[str, OfficialSnapshot]:
    if not isinstance(value, dict) or value.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise EtfSourceError("ETF 스냅샷 스키마 버전이 올바르지 않습니다.")
    raw_snapshots = value.get("snapshots")
    if not isinstance(raw_snapshots, dict):
        raise EtfSourceError("ETF 스냅샷 목록 형식이 올바르지 않습니다.")
    expected_symbols = set(SUPPORTED_SOURCE_SYMBOLS)
    if any(not isinstance(symbol, str) for symbol in raw_snapshots):
        raise EtfSourceError("ETF 스냅샷 종목코드는 문자열이어야 합니다.")
    actual_symbols = set(raw_snapshots)
    if actual_symbols != expected_symbols:
        missing = ", ".join(sorted(expected_symbols - actual_symbols)) or "없음"
        extra = ", ".join(sorted(actual_symbols - expected_symbols)) or "없음"
        raise EtfSourceError(f"ETF 스냅샷 종목 구성이 다릅니다. 누락: {missing}, 추가: {extra}")
    return {
        symbol: _snapshot(symbol, raw_snapshots[symbol])
        for symbol in SUPPORTED_SOURCE_SYMBOLS
    }


def load_official_snapshots(
    path: Path = DEFAULT_SNAPSHOT_PATH,
) -> dict[str, OfficialSnapshot]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EtfSourceError(f"ETF 스냅샷 파일을 읽지 못했습니다: {path}") from exc
    return parse_snapshot_document(document)


def snapshot_document(snapshots: dict[str, OfficialSnapshot]) -> dict[str, Any]:
    document = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshots": {
            symbol: {
                "facts_as_of": snapshot.facts_as_of.isoformat(),
                "holdings_as_of": snapshot.holdings_as_of.isoformat(),
                "holdings_count": snapshot.holdings_count,
                "symbol": snapshot.symbol,
                "top_holdings": [
                    {
                        "name": holding.name,
                        "symbol": holding.symbol,
                        "weight_pct": str(holding.weight_pct),
                    }
                    for holding in snapshot.top_holdings
                ],
            }
            for symbol, snapshot in sorted(snapshots.items())
        },
    }
    parse_snapshot_document(document)
    return document


def write_official_snapshots(
    snapshots: dict[str, OfficialSnapshot],
    path: Path = DEFAULT_SNAPSHOT_PATH,
) -> None:
    serialized = json.dumps(
        snapshot_document(snapshots),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
