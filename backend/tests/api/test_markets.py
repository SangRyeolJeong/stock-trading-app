from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services.etf import stale_etf_symbols

client = TestClient(app)


def test_etf_official_snapshots_are_not_stale() -> None:
    assert stale_etf_symbols() == []


def test_etf_snapshot_freshness_uses_source_specific_cadence() -> None:
    assert stale_etf_symbols(as_of=date(2026, 8, 15)) == ["SPY"]
    assert stale_etf_symbols(as_of=date(2026, 8, 18)) == ["379800", "SPY"]


def test_unknown_symbol_returns_not_found() -> None:
    response = client.get("/api/v1/markets/quotes/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "시세를 찾을 수 없습니다."


def test_mock_usd_krw_exchange_rate() -> None:
    response = client.get("/api/v1/markets/exchange-rates/USD/KRW")

    assert response.status_code == 200
    assert response.json()["base_currency"] == "USD"
    assert response.json()["quote_currency"] == "KRW"
    assert response.json()["rate"] == "1385.20"
    assert response.json()["source"] == "mock"


def test_unsupported_exchange_rate_pair_returns_not_found() -> None:
    response = client.get("/api/v1/markets/exchange-rates/EUR/KRW")

    assert response.status_code == 404
    assert response.json()["detail"] == "지원하지 않는 통화쌍입니다."


def test_instrument_search_filters_domestic_and_etf() -> None:
    domestic = client.get(
        "/api/v1/markets/instruments",
        params={"query": "삼성", "market": "domestic"},
    )
    etfs = client.get(
        "/api/v1/markets/instruments",
        params={"query": "QQQM", "market": "etf"},
    )

    assert domestic.status_code == 200
    assert any(item["symbol"] == "005930" for item in domestic.json()["items"])
    assert all(item["country"] == "KR" for item in domestic.json()["items"])
    assert etfs.status_code == 200
    assert etfs.json()["items"][0]["symbol"] == "QQQM"
    assert etfs.json()["items"][0]["asset_type"] == "etf"


def test_income_and_defensive_mock_etfs_are_searchable_and_tradeable() -> None:
    for symbol, expected_name in (
        ("DGRO", "배당성장"),
        ("SGOV", "미국 국채"),
    ):
        search = client.get(
            "/api/v1/markets/instruments",
            params={"query": symbol, "market": "etf"},
        )
        quote = client.get(f"/api/v1/markets/quotes/{symbol}")
        overview = client.get(f"/api/v1/markets/overview/{symbol}")

        assert search.status_code == 200
        assert search.json()["items"][0]["symbol"] == symbol
        assert expected_name in search.json()["items"][0]["name"]
        assert quote.status_code == 200
        assert quote.json()["currency"] == "USD"
        assert overview.status_code == 200
        assert overview.json()["asset_type"] == "etf"


def test_etf_catalog_exposes_versioned_official_snapshots() -> None:
    response = client.get("/api/v1/markets/etfs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_version"] == "ETF-COMPARE-2026.08"
    assert {item["symbol"] for item in payload["items"]} == {
        "QQQM",
        "QQQ",
        "SPY",
        "VOO",
        "379800",
        "379810",
        "360750",
        "133690",
    }
    assert all(item["source_url"].startswith("https://") for item in payload["items"])
    assert all(float(item["top_holdings_coverage_pct"]) > 0 for item in payload["items"])
    kodex = next(item for item in payload["items"] if item["symbol"] == "379800")
    assert kodex["listing_country"] == "KR"
    assert kodex["trading_currency"] == "KRW"


def test_etf_comparison_calculates_overlap_and_fee_difference() -> None:
    response = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "qqqm", "right": "QQQ"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["same_underlying_index"] is True
    assert float(payload["top_holdings_overlap_pct"]) > 95
    assert payload["common_top_holdings_count"] == 10
    assert payload["lower_expense_symbol"] == "QQQM"
    assert payload["comparison_principal_krw"] == "10000000"
    assert payload["annual_fee_difference_krw"] == "3000"
    assert "최솟값" in payload["formula"]


def test_etf_comparison_warns_about_cross_index_overlap() -> None:
    response = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "QQQM", "right": "SPY"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["same_underlying_index"] is False
    assert 0 < float(payload["top_holdings_overlap_pct"]) < 100
    assert payload["common_top_holdings_count"] >= 7


def test_etf_comparison_supports_korean_and_us_listings() -> None:
    response = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "379800", "right": "VOO"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["same_underlying_index"] is True
    assert payload["left"]["trading_currency"] == "KRW"
    assert payload["right"]["trading_currency"] == "USD"
    assert payload["lower_expense_symbol"] == "379800"
    assert payload["annual_fee_difference_krw"] == "2380"
    assert "세금·환전·거래시간" in payload["interpretation"]


def test_etf_comparison_supports_same_index_korean_issuers() -> None:
    response = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "360750", "right": "379800"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["same_underlying_index"] is True
    assert payload["left"]["listing_country"] == "KR"
    assert payload["right"]["listing_country"] == "KR"
    assert payload["common_top_holdings_count"] >= 8
    assert payload["lower_expense_symbol"] == "379800"
    assert payload["annual_fee_difference_krw"] == "60"


def test_domestic_kodex_mock_quotes_are_tradeable() -> None:
    for symbol in ("379800", "379810", "133690"):
        response = client.get(f"/api/v1/markets/quotes/{symbol}")

        assert response.status_code == 200
        assert response.json()["currency"] == "KRW"


def test_etf_comparison_rejects_same_or_unsupported_symbols() -> None:
    same = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "QQQM", "right": "QQQM"},
    )
    unsupported = client.get(
        "/api/v1/markets/etfs/compare",
        params={"left": "QQQM", "right": "UNKNOWN"},
    )

    assert same.status_code == 400
    assert same.json()["detail"] == "서로 다른 ETF 두 개를 선택해야 합니다."
    assert unsupported.status_code == 404
    assert unsupported.json()["detail"] == "비교 데이터가 없는 ETF입니다."


def test_mock_candles_are_sorted_and_have_requested_limit() -> None:
    response = client.get("/api/v1/markets/candles/QQQM", params={"limit": 22})

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "QQQM"
    assert payload["source"] == "mock"
    assert len(payload["candles"]) == 22
    assert payload["candles"] == sorted(payload["candles"], key=lambda candle: candle["date"])


def test_mock_orderbook_has_best_prices_first_and_balanced_totals() -> None:
    response = client.get("/api/v1/markets/orderbooks/QQQM")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "QQQM"
    assert payload["currency"] == "USD"
    assert payload["source"] == "mock"
    assert len(payload["asks"]) == len(payload["bids"]) == 5
    assert payload["asks"] == sorted(payload["asks"], key=lambda level: float(level["price"]))
    assert payload["bids"] == sorted(payload["bids"], key=lambda level: float(level["price"]), reverse=True)
    assert float(payload["total_ask_quantity"]) == sum(float(level["quantity"]) for level in payload["asks"])
    assert float(payload["total_bid_quantity"]) == sum(float(level["quantity"]) for level in payload["bids"])


def test_unknown_orderbook_symbol_returns_not_found() -> None:
    response = client.get("/api/v1/markets/orderbooks/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "호가 데이터를 찾을 수 없습니다."


def test_mock_security_overview_exposes_valuation_and_range() -> None:
    response = client.get("/api/v1/markets/overview/AAPL")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["currency"] == "USD"
    assert payload["asset_type"] == "stock"
    assert payload["source"] == "mock"
    assert float(payload["week_52_high"]) > float(payload["week_52_low"])
    assert float(payload["per"]) > 0


def test_unknown_security_overview_returns_not_found() -> None:
    response = client.get("/api/v1/markets/overview/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "기업정보를 찾을 수 없습니다."
