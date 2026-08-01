from datetime import date
from decimal import Decimal

import pytest

from app.services.etf_sources import (
    EtfSourceError,
    OfficialSnapshot,
    assess_snapshot,
    parse_kodex_snapshot,
    parse_tiger_snapshot,
)


def test_parse_kodex_snapshot_extracts_dates_count_and_top_us_equities() -> None:
    payload = {
        "info": {"product": {"stkTicker": "379800", "gijunYMD": "20260731"}},
        "pdf": {
            "gijunYMD": "20260801",
            "totalCnt": 505,
            "list": [
                {"itmNo": "USD CASH", "secNm": "USD", "ratio": 0.12},
                {"itmNo": "NVDA US Equity", "secNm": "NVIDIA Corp", "ratio": 7.39},
                {"itmNo": "BRK/B US Equity", "secNm": "Berkshire Hathaway", "ratio": 1.46},
                {"itmNo": "AAPL US Equity", "secNm": "Apple Inc", "ratio": 7.66},
            ],
        },
    }

    snapshot = parse_kodex_snapshot(payload, "379800")

    assert snapshot.facts_as_of == date(2026, 7, 31)
    assert snapshot.holdings_as_of == date(2026, 8, 1)
    assert snapshot.holdings_count == 505
    assert [holding.symbol for holding in snapshot.top_holdings] == ["AAPL", "NVDA", "BRK.B"]
    assert snapshot.top_holdings[0].weight_pct == Decimal("7.66")


def test_parse_kodex_snapshot_rejects_mismatched_symbol() -> None:
    payload = {
        "info": {"product": {"stkTicker": "379810", "gijunYMD": "20260731"}},
        "pdf": {
            "gijunYMD": "20260731",
            "totalCnt": 1,
            "list": [{"itmNo": "AAPL US Equity", "secNm": "Apple", "ratio": 8.1}],
        },
    }

    with pytest.raises(EtfSourceError, match="종목코드가 요청과 다릅니다"):
        parse_kodex_snapshot(payload, "379800")


def test_parse_tiger_snapshot_extracts_official_table() -> None:
    overview = '<input type="text" name="fixDate" value="2026.07.31">'
    holdings = """
        <tr data-tot-cnt="504">
          <td>AAPL US EQUITY</td><td>Apple Inc</td><td>211.49</td>
          <td>100,416,365</td><td>7.65</td><td><span>상승</span>3.66</td>
        </tr>
        <tr data-tot-cnt="504">
          <td>NVDA US EQUITY</td><td>NVIDIA Corp</td><td>348.77</td>
          <td>96,866,319</td><td>7.38</td><td><span>하락</span>-6.57</td>
        </tr>
    """

    snapshot = parse_tiger_snapshot(overview, holdings, "360750")

    assert snapshot.facts_as_of == date(2026, 7, 31)
    assert snapshot.holdings_as_of == date(2026, 7, 31)
    assert snapshot.holdings_count == 504
    assert [holding.symbol for holding in snapshot.top_holdings] == ["AAPL", "NVDA"]
    assert snapshot.top_holdings[1].name == "NVIDIA Corp"


def test_parse_tiger_snapshot_requires_snapshot_date() -> None:
    with pytest.raises(EtfSourceError, match="기준일을 찾지 못했습니다"):
        parse_tiger_snapshot("<div></div>", '<tr data-tot-cnt="1"></tr>', "360750")


def test_assess_snapshot_reports_update_available() -> None:
    snapshot = OfficialSnapshot(
        symbol="360750",
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 31),
        holdings_count=504,
        top_holdings=(),
    )

    result = assess_snapshot(
        snapshot,
        checked_facts_as_of=date(2026, 7, 1),
        checked_holdings_as_of=date(2026, 7, 1),
        as_of=date(2026, 8, 1),
    )

    assert result.status == "update_available"


def test_assess_snapshot_blocks_future_official_date() -> None:
    snapshot = OfficialSnapshot(
        symbol="379800",
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 8, 3),
        holdings_count=505,
        top_holdings=(),
    )

    result = assess_snapshot(
        snapshot,
        checked_facts_as_of=date(2026, 7, 31),
        checked_holdings_as_of=date(2026, 7, 8),
        as_of=date(2026, 8, 1),
    )

    assert result.status == "future"
    assert "자동 반영할 수 없습니다" in result.message
