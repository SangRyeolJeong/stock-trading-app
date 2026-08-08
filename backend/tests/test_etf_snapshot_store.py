import json
from dataclasses import replace
from datetime import date

import pytest

from app.services.etf_snapshot_store import (
    DEFAULT_SNAPSHOT_PATH,
    load_official_snapshots,
    parse_snapshot_document,
    write_official_snapshots,
)
from app.services.etf_sources import SUPPORTED_SOURCE_SYMBOLS, EtfSourceError


def test_default_snapshot_file_contains_every_supported_domestic_source() -> None:
    snapshots = load_official_snapshots()

    assert set(snapshots) == set(SUPPORTED_SOURCE_SYMBOLS)
    assert snapshots["379800"].facts_as_of == date(2026, 7, 31)
    assert snapshots["360750"].top_holdings[0].symbol == "AAPL"


def test_snapshot_file_round_trips_deterministically(tmp_path) -> None:
    snapshots = load_official_snapshots()
    output = tmp_path / "snapshots.json"

    write_official_snapshots(snapshots, output)
    first_content = output.read_text(encoding="utf-8")
    write_official_snapshots(load_official_snapshots(output), output)

    assert output.read_text(encoding="utf-8") == first_content
    assert load_official_snapshots(output) == snapshots
    assert output.read_bytes() == DEFAULT_SNAPSHOT_PATH.read_bytes()
    assert first_content.endswith("\n")


def test_snapshot_document_rejects_missing_and_duplicate_holdings() -> None:
    document = json.loads(DEFAULT_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    document["snapshots"].pop("379800")
    with pytest.raises(EtfSourceError, match="누락: 379800"):
        parse_snapshot_document(document)

    document = json.loads(DEFAULT_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    document["snapshots"]["379800"]["top_holdings"][1] = (
        document["snapshots"]["379800"]["top_holdings"][0]
    )
    with pytest.raises(EtfSourceError, match="중복 종목코드"):
        parse_snapshot_document(document)


def test_invalid_write_preserves_existing_file(tmp_path) -> None:
    output = tmp_path / "snapshots.json"
    output.write_text("keep-me", encoding="utf-8")
    snapshots = load_official_snapshots()
    snapshots["379800"] = replace(snapshots["379800"], top_holdings=())

    with pytest.raises(EtfSourceError, match="1~10개"):
        write_official_snapshots(snapshots, output)

    assert output.read_text(encoding="utf-8") == "keep-me"
