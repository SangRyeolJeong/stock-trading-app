from decimal import Decimal

from app.schemas.tax import TaxSimulationRequest
from app.services.tax import TaxCalculationService

service = TaxCalculationService()


def request(
    *,
    salary: str = "45000000",
    monthly: str = "500000",
    years: int = 3,
    return_rate: str = "7",
    age: int = 60,
) -> TaxSimulationRequest:
    return TaxSimulationRequest(
        annual_salary_krw=salary,
        monthly_contribution_krw=monthly,
        investment_years=years,
        annual_return_rate_pct=return_rate,
        withdrawal_age=age,
    )


def result_by_type(simulation: object, account_type: str) -> object:
    return next(result for result in simulation.results if result.account_type == account_type)


def test_overseas_capital_gains_deduction_and_tax_rate() -> None:
    assert service.overseas_capital_gains_tax(Decimal("2500000")) == Decimal("0")
    assert service.overseas_capital_gains_tax(Decimal("3500000")) == Decimal("220000")
    assert service.overseas_capital_gains_tax(Decimal("-1000000")) == Decimal("0")


def test_pension_credit_rate_changes_above_salary_threshold() -> None:
    low_income = service.simulate(request(salary="55000000"))
    high_income = service.simulate(request(salary="55000001"))

    low_pension = result_by_type(low_income, "pension")
    high_pension = result_by_type(high_income, "pension")

    assert low_pension.contribution_tax_credit == Decimal("2970000")
    assert high_pension.contribution_tax_credit == Decimal("2376000")


def test_isa_exemption_changes_above_salary_threshold() -> None:
    low_income = service.simulate(request(salary="50000000", monthly="2000000", years=10))
    high_income = service.simulate(request(salary="50000001", monthly="2000000", years=10))

    low_isa = result_by_type(low_income, "isa")
    high_isa = result_by_type(high_income, "isa")

    assert "400만원 비과세" in low_isa.tax_description
    assert "200만원 비과세" in high_isa.tax_description
    assert high_isa.investment_tax > low_isa.investment_tax


def test_isa_applies_annual_and_total_contribution_limits() -> None:
    simulation = service.simulate(request(monthly="2000000", years=10))
    isa = result_by_type(simulation, "isa")

    assert isa.eligible_contribution == Decimal("100000000")
    assert isa.overflow_contribution == Decimal("140000000")


def test_irp_has_larger_credit_limit_than_pension_savings() -> None:
    simulation = service.simulate(request(monthly="1000000"))
    pension = result_by_type(simulation, "pension")
    irp = result_by_type(simulation, "irp")

    assert pension.contribution_tax_credit == Decimal("2970000")
    assert irp.contribution_tax_credit == Decimal("4455000")
    assert irp.after_tax_value > pension.after_tax_value


def test_pension_withdrawal_rate_decreases_with_age() -> None:
    age_60 = service.simulate(request(age=60))
    age_80 = service.simulate(request(age=80))

    assert result_by_type(age_80, "pension").withdrawal_tax < result_by_type(age_60, "pension").withdrawal_tax


def test_simulation_exposes_versioned_rules_and_assumptions() -> None:
    simulation = service.simulate(request())

    assert simulation.rules.version == "KR-2026.07"
    assert simulation.rules.effective_date == "2026-07-01"
    assert len(simulation.rules.sources) >= 4
    assert simulation.best_account_type in {"direct", "isa", "pension", "irp"}
    assert simulation.assumptions
