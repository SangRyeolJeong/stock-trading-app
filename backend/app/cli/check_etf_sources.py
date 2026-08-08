from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.services.etf_snapshot_store import (
    DEFAULT_SNAPSHOT_PATH,
    load_official_snapshots,
    write_official_snapshots,
)
from app.services.etf_sources import (
    SUPPORTED_SOURCE_SYMBOLS,
    OfficialSnapshot,
    SnapshotAssessment,
    assess_snapshot,
    fetch_official_snapshot,
)


@dataclass(frozen=True)
class SourceCheck:
    snapshot: OfficialSnapshot
    assessment: SnapshotAssessment


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="KODEX·TIGER 공식 자료와 저장소 ETF 스냅샷을 비교·갱신합니다.",
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        default=list(SUPPORTED_SOURCE_SYMBOLS),
        help="점검할 종목코드. 생략하면 지원 종목 전체를 점검합니다.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="새 자료·과거/미래 기준일·조회 오류가 있으면 실패 코드로 종료합니다.",
    )
    mode.add_argument(
        "--update",
        action="store_true",
        help="모든 조회가 정상일 때 스냅샷 JSON을 원자적으로 갱신합니다.",
    )
    parser.add_argument(
        "--snapshot-file",
        type=Path,
        default=DEFAULT_SNAPSHOT_PATH,
        help="읽을 스냅샷 JSON 경로입니다.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="--update 결과 경로입니다. 생략하면 읽은 스냅샷 파일을 갱신합니다.",
    )
    return parser


def collect_source_checks(
    symbols: Sequence[str],
    stored_snapshots: dict[str, OfficialSnapshot],
    *,
    fetcher: Callable[[str], OfficialSnapshot] = fetch_official_snapshot,
    as_of: date | None = None,
) -> tuple[list[SourceCheck], list[str]]:
    checks: list[SourceCheck] = []
    errors: list[str] = []
    reference_date = as_of or date.today()
    for raw_symbol in symbols:
        symbol = raw_symbol.strip().upper()
        stored_snapshot = stored_snapshots.get(symbol)
        if stored_snapshot is None:
            errors.append(f"{symbol}: 저장소 비교 스냅샷이 없습니다.")
            continue
        try:
            snapshot = fetcher(symbol)
            assessment = assess_snapshot(
                snapshot,
                checked_facts_as_of=stored_snapshot.facts_as_of,
                checked_holdings_as_of=stored_snapshot.holdings_as_of,
                as_of=reference_date,
            )
        except Exception as exc:  # noqa: BLE001 - each remote source must be reported independently
            errors.append(f"{symbol}: {exc}")
            continue
        checks.append(SourceCheck(snapshot=snapshot, assessment=assessment))
    return checks, errors


def _print_check(check: SourceCheck) -> None:
    snapshot = check.snapshot
    assessment = check.assessment
    print(
        f"[{assessment.status}] {snapshot.symbol}: "
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


def main(
    argv: Sequence[str] | None = None,
    *,
    fetcher: Callable[[str], OfficialSnapshot] = fetch_official_snapshot,
    as_of: date | None = None,
) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.output is not None and not args.update:
        parser.error("--output은 --update와 함께 사용해야 합니다.")

    try:
        stored_snapshots = load_official_snapshots(args.snapshot_file)
    except Exception as exc:  # noqa: BLE001 - CLI must turn malformed local data into a clear error
        print(f"[error] snapshot: {exc}")
        return 1

    checks, errors = collect_source_checks(
        args.symbols,
        stored_snapshots,
        fetcher=fetcher,
        as_of=as_of,
    )
    for check in checks:
        _print_check(check)
    for error in errors:
        print(f"[error] {error}")

    blocked_checks = [
        check for check in checks if check.assessment.status in {"source_older", "future"}
    ]
    if args.update:
        if errors or blocked_checks:
            print("[aborted] 일부 공식 자료를 신뢰할 수 없어 기존 스냅샷을 유지합니다.")
            return 1
        updated_snapshots = dict(stored_snapshots)
        for check in checks:
            updated_snapshots[check.snapshot.symbol] = check.snapshot
        output_path = args.output or args.snapshot_file
        try:
            write_official_snapshots(updated_snapshots, output_path)
        except Exception as exc:  # noqa: BLE001 - filesystem failures must preserve the old file
            print(f"[error] snapshot write: {exc}")
            return 1
        print(f"[updated] {output_path}: {len(checks)}개 공식 스냅샷을 반영했습니다.")
        return 0

    strict_failure = errors or blocked_checks or any(
        check.assessment.status == "update_available" for check in checks
    )
    return 1 if args.check and strict_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
