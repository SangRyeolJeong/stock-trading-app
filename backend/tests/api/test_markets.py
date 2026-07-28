from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
