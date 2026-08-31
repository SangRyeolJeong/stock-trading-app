from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.strategy import StrategyExplanationResponse
from app.services.strategy_explanation import (
    StrategyExplanationUnavailable,
    strategy_explanation_service,
)

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


def test_ai_explanation_recalculates_strategy_on_server(monkeypatch) -> None:
    explanation = StrategyExplanationResponse(
        engine_version="STRATEGY-2026.07",
        strategy_id="retirement-growth-long",
        provider="openai",
        model="gpt-5.6",
        overview="규칙 결과를 쉽게 설명합니다.",
        highlights=[
            {
                "title": "은퇴 목적",
                "explanation": "연금계좌 중심 실행 순서를 설명합니다.",
                "evidence_codes": ["GOAL_RETIREMENT"],
            },
            {
                "title": "장기 계획",
                "explanation": "장기 점검 원칙을 설명합니다.",
                "evidence_codes": ["HORIZON_LONG"],
            },
        ],
        caution="원금 손실 가능성을 확인하세요.",
        disclaimer="AI는 규칙 결과만 설명합니다.",
    )
    explain = AsyncMock(return_value=explanation)
    monkeypatch.setattr(strategy_explanation_service, "explain", explain)

    response = client.post(
        "/api/v1/strategies/explain",
        json={
            "goal": "retirement",
            "horizon_years": 30,
            "monthly_amount_krw": 500_000,
            "risk_profile": "growth",
            "liquidity_preference": True,
            "fee_sensitivity": True,
            "income_preference": False,
            "tax_efficiency_priority": True,
        },
    )

    assert response.status_code == 200
    called_request, called_recommendation, called_user_id = explain.await_args.args
    assert called_request.monthly_amount_krw == 500_000
    assert called_recommendation.engine_version == "STRATEGY-2026.07"
    assert called_user_id == "demo-user"


def test_ai_explanation_reports_disabled_provider(monkeypatch) -> None:
    explain = AsyncMock(
        side_effect=StrategyExplanationUnavailable("AI 전략 설명이 설정되지 않았습니다.")
    )
    monkeypatch.setattr(strategy_explanation_service, "explain", explain)

    response = client.post(
        "/api/v1/strategies/explain",
        json={
            "goal": "retirement",
            "horizon_years": 30,
            "monthly_amount_krw": 500_000,
            "risk_profile": "growth",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "AI 전략 설명이 설정되지 않았습니다."
