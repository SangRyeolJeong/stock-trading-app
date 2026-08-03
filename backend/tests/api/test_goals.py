from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def payload() -> dict[str, object]:
    return {
        "current_assets_krw": "10000000",
        "target_amount_krw": "300000000",
        "monthly_contribution_krw": "500000",
        "investment_years": 20,
        "annual_return_rate_pct": "7",
    }


def test_goal_simulation_returns_deterministic_projection() -> None:
    response = client.post("/api/v1/goals/simulate", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["engine_version"] == "GOAL-2026.08"
    assert Decimal(body["projected_value"]) > Decimal("0")
    assert len(body["milestones"]) == 20
    assert len(body["sensitivity"]) == 3
    assert body["assumptions"]


def test_goal_simulation_rejects_zero_target() -> None:
    invalid = payload()
    invalid["target_amount_krw"] = "0"

    response = client.post("/api/v1/goals/simulate", json=invalid)

    assert response.status_code == 422
