from __future__ import annotations

import argparse
from datetime import date

from app.services.etf import ETF_PROFILES
from app.services.etf_sources import (
    SUPPORTED_SOURCE_SYMBOLS,
    assess_snapshot,
    fetch_official_snapshot,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="KODEX·TIGER 공식 자료와 저장소 ETF 스냅샷을 비교합니다.",
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        default=list(SUPPORTED_SOURCE_SYMBOLS),
        help="점검할 종목코드. 생략하면 지원 종목 전체를 점검합니다.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="업데이트 가능·미래 기준일·조회 오류가 있으면 실패 코드로 종료합니다.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    failed = False
    for raw_symbol in args.symbols:
        symbol = raw_symbol.strip().upper()
        profile = ETF_PROFILES.get(symbol)
        if profile is None:
            print(f"[error] {symbol}: 저장소 비교 프로필이 없습니다.")
            failed = True
            continue
        try:
            snapshot = fetch_official_snapshot(symbol)
            assessment = assess_snapshot(
                snapshot,
                checked_facts_as_of=profile.facts_as_of,
                checked_holdings_as_of=profile.holdings_as_of,
                as_of=date.today(),
            )
        except Exception as exc:  # noqa: BLE001 - each remote source must be reported independently
            print(f"[error] {symbol}: {exc}")
            failed = True
            continue

        print(
            f"[{assessment.status}] {symbol}: "
            f"facts={snapshot.facts_as_of.isoformat()}, "
            f"holdings={snapshot.holdings_as_of.isoformat()}, "
            f"count={snapshot.holdings_count} — {assessment.message}"
        )
        print(
            "  top10: "
            + ", ".join(
                f"{holding.symbol} {holding.weight_pct}%" for holding in snapshot.top_holdings
            )
        )
        if assessment.status in {"update_available", "future"}:
            failed = True

    return 1 if args.check and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
