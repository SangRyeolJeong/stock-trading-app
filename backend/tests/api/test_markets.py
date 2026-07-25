from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unknown_symbol_returns_not_found() -> None:
    response = client.get("/api/v1/markets/quotes/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "지원하지 않는 데모 종목입니다."
