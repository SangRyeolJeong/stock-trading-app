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
