from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def payload() -> dict[str, object]:
    return {
        "annual_salary_krw": "45000000",
        "monthly_contribution_krw": "500000",
        "investment_years": 30,
        "annual_return_rate_pct": "7",
        "withdrawal_age": 60,
    }


def test_tax_simulation_returns_four_account_comparisons() -> None:
    response = client.post("/api/v1/tax/simulate", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert {result["account_type"] for result in body["results"]} == {
        "direct",
        "isa",
        "pension",
        "irp",
    }
    assert body["rules"]["version"] == "KR-2026.07"
    assert body["best_account_type"] in {"direct", "isa", "pension", "irp"}


def test_tax_simulation_rejects_period_shorter_than_isa_minimum() -> None:
    invalid = payload()
    invalid["investment_years"] = 2

    response = client.post("/api/v1/tax/simulate", json=invalid)

    assert response.status_code == 422


def pension_start_payload() -> dict[str, object]:
    return {
        "annual_salary_krw": "45000000",
        "current_age": 30,
        "withdrawal_age": 60,
        "monthly_contribution_krw": "500000",
        "annual_return_rate_pct": "7",
        "delay_years": 5,
    }


def test_pension_start_comparison_returns_versioned_scenarios() -> None:
    response = client.post("/api/v1/tax/pension-start", json=pension_start_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["start_now"]["start_age"] == 30
    assert body["delayed_start"]["start_age"] == 35
    assert Decimal(body["projected_value_gap"]) > Decimal("0")
    assert body["rules"]["version"] == "KR-2026.07"
    assert body["assumptions"]


def test_pension_start_comparison_rejects_delay_past_withdrawal_age() -> None:
    invalid = pension_start_payload()
    invalid["current_age"] = 57

    response = client.post("/api/v1/tax/pension-start", json=invalid)

    assert response.status_code == 422
