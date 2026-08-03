from decimal import Decimal

from app.schemas.tax import PensionStartComparisonRequest, TaxSimulationRequest
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


def pension_start_request(
    *,
    salary: str = "45000000",
    current_age: int = 30,
    withdrawal_age: int = 60,
    monthly: str = "500000",
    return_rate: str = "7",
    delay_years: int = 5,
) -> PensionStartComparisonRequest:
    return PensionStartComparisonRequest(
        annual_salary_krw=salary,
        current_age=current_age,
        withdrawal_age=withdrawal_age,
        monthly_contribution_krw=monthly,
        annual_return_rate_pct=return_rate,
        delay_years=delay_years,
    )


def test_pension_start_comparison_quantifies_the_cost_of_waiting() -> None:
    comparison = service.compare_pension_start(pension_start_request())

    assert comparison.start_now.contribution_years == 30
    assert comparison.delayed_start.contribution_years == 25
    assert comparison.start_now.total_principal == Decimal("180000000")
    assert comparison.delayed_start.total_principal == Decimal("150000000")
    assert comparison.start_now.contribution_tax_credit == Decimal("29700000")
    assert comparison.delayed_start.contribution_tax_credit == Decimal("24750000")
    assert comparison.projected_value_gap > Decimal("0")
    assert comparison.delayed_required_monthly_contribution > Decimal("500000")
    assert comparison.delayed_required_within_pension_limit is True

    catch_up = service.compare_pension_start(
        pension_start_request(
            current_age=35,
            monthly=str(comparison.delayed_required_monthly_contribution),
        )
    )
    assert (
        catch_up.start_now.projected_value_with_tax_credit
        >= comparison.start_now.projected_value_with_tax_credit
    )


def test_pension_start_comparison_caps_eligible_annual_contribution() -> None:
    comparison = service.compare_pension_start(
        pension_start_request(monthly="2000000")
    )

    assert comparison.start_now.annual_eligible_contribution == Decimal("18000000")
    assert comparison.start_now.total_principal == Decimal("540000000")


def test_pension_start_comparison_uses_salary_credit_rate() -> None:
    low_income = service.compare_pension_start(pension_start_request(salary="55000000"))
    high_income = service.compare_pension_start(pension_start_request(salary="55000001"))

    assert low_income.start_now.contribution_tax_credit == Decimal("29700000")
    assert high_income.start_now.contribution_tax_credit == Decimal("23760000")
