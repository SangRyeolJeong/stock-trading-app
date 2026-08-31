from dataclasses import replace
from datetime import date

from app.cli.check_etf_sources import main
from app.services.etf_snapshot_store import load_official_snapshots


def newer_snapshot(symbol: str):
    snapshot = load_official_snapshots()[symbol]
    return replace(
        snapshot,
        facts_as_of=date(2026, 9, 1),
        holdings_as_of=date(2026, 9, 1),
    )


def test_update_writes_a_complete_candidate_snapshot(tmp_path) -> None:
    output = tmp_path / "candidate.json"

    result = main(
        ["--update", "--output", str(output)],
        fetcher=newer_snapshot,
        as_of=date(2026, 9, 2),
    )

    assert result == 0
    updated = load_official_snapshots(output)
    assert all(snapshot.facts_as_of == date(2026, 9, 1) for snapshot in updated.values())


def test_update_is_all_or_nothing_when_one_source_fails(tmp_path) -> None:
    output = tmp_path / "candidate.json"
    output.write_text("keep-me", encoding="utf-8")

    def failing_fetcher(symbol: str):
        if symbol == "360750":
            raise RuntimeError("temporary source failure")
        return newer_snapshot(symbol)

    result = main(
        ["--update", "--output", str(output)],
        fetcher=failing_fetcher,
        as_of=date(2026, 9, 2),
    )

    assert result == 1
    assert output.read_text(encoding="utf-8") == "keep-me"


def test_update_rejects_a_source_date_regression(tmp_path) -> None:
    output = tmp_path / "candidate.json"

    def older_fetcher(symbol: str):
        snapshot = load_official_snapshots()[symbol]
        return replace(
            snapshot,
            facts_as_of=date(2026, 1, 1),
            holdings_as_of=date(2026, 1, 1),
        )

    result = main(
        ["--update", "--output", str(output)],
        fetcher=older_fetcher,
        as_of=date(2026, 9, 2),
    )

    assert result == 1
    assert not output.exists()


def test_check_fails_when_the_repository_has_an_update_available() -> None:
    result = main(
        ["--check", "379800"],
        fetcher=newer_snapshot,
        as_of=date(2026, 9, 2),
    )

    assert result == 1


def test_output_requires_update_mode(tmp_path) -> None:
    result_path = tmp_path / "candidate.json"

    try:
        main(["--output", str(result_path)], fetcher=newer_snapshot)
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("--output without --update must fail argument parsing")
