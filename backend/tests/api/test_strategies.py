from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_negative_monthly_amount_is_rejected() -> None:
    response = client.post(
        "/api/v1/strategies/recommend",
        json={
            "goal": "retirement",
            "horizon_years": 30,
            "monthly_amount_krw": -100_000,
            "risk_profile": "growth",
        },
    )

    assert response.status_code == 422
