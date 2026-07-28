from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def recommend(**overrides: object) -> dict:
    payload = {
        "goal": "retirement",
        "horizon_years": 30,
        "monthly_amount_krw": 500_000,
        "risk_profile": "growth",
        "liquidity_preference": True,
        "fee_sensitivity": True,
        "income_preference": False,
        "tax_efficiency_priority": True,
    }
    payload.update(overrides)
    response = client.post("/api/v1/strategies/recommend", json=payload)
    assert response.status_code == 200
    return response.json()


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


def test_recommendation_is_structured_and_allocations_balance() -> None:
    result = recommend(monthly_amount_krw=517_000)

    assert result["engine_version"] == "STRATEGY-2026.07"
    assert result["strategy_id"] == "retirement-growth-long"
    assert sum(item["weight_pct"] for item in result["allocations"]) == 100
    assert sum(item["monthly_amount_krw"] for item in result["allocations"]) == 517_000
    assert result["allocation"] == {item["label"]: item["weight_pct"] for item in result["allocations"]}
    assert result["reason_codes"] == [item["code"] for item in result["rationale"]]
    assert len(result["action_steps"]) == 3


def test_conservative_profile_keeps_equity_within_cap() -> None:
    result = recommend(risk_profile="conservative", horizon_years=30, liquidity_preference=False)

    assert result["risk_summary"]["equity_weight_pct"] <= 50
    assert result["risk_summary"]["level"] == "conservative"


def test_short_lump_sum_goal_increases_defensive_allocation() -> None:
    short = recommend(goal="lump_sum", horizon_years=5, risk_profile="balanced")
    long = recommend(goal="lump_sum", horizon_years=20, risk_profile="balanced")

    assert short["risk_summary"]["defensive_weight_pct"] > long["risk_summary"]["defensive_weight_pct"]
    assert "HORIZON_SHORT" in short["reason_codes"]


def test_liquidity_preference_reserves_more_cash() -> None:
    liquid = recommend(liquidity_preference=True)
    invested = recommend(liquidity_preference=False)

    assert liquid["risk_summary"]["liquidity_weight_pct"] >= 15
    assert liquid["risk_summary"]["liquidity_weight_pct"] > invested["risk_summary"]["liquidity_weight_pct"]


def test_income_preference_changes_allocation_deterministically() -> None:
    baseline = recommend(goal="lump_sum", horizon_years=10, income_preference=False)
    income = recommend(goal="lump_sum", horizon_years=10, income_preference=True)
    repeated = recommend(goal="lump_sum", horizon_years=10, income_preference=True)

    baseline_income = next(item for item in baseline["allocations"] if item["asset_class"] == "income")
    preferred_income = next(item for item in income["allocations"] if item["asset_class"] == "income")
    assert preferred_income["weight_pct"] > baseline_income["weight_pct"]
    assert income == repeated
