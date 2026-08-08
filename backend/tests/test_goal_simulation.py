from decimal import Decimal

from app.schemas.goal import GoalSimulationRequest
from app.services.goal import GoalSimulationService

service = GoalSimulationService()


def request(
    *,
    current_assets: str = "10000000",
    target: str = "100000000",
    monthly: str = "500000",
    years: int = 10,
    return_rate: str = "0",
    inflation_rate: str = "0",
    target_in_today_money: bool = False,
    contribution_growth_rate: str = "0",
) -> GoalSimulationRequest:
    return GoalSimulationRequest(
        current_assets_krw=current_assets,
        target_amount_krw=target,
        monthly_contribution_krw=monthly,
        investment_years=years,
        annual_return_rate_pct=return_rate,
        annual_inflation_rate_pct=inflation_rate,
        target_amount_in_today_money=target_in_today_money,
        annual_contribution_growth_rate_pct=contribution_growth_rate,
    )


def test_zero_return_exposes_principal_gap_and_required_monthly_amount() -> None:
    result = service.simulate(request())

    assert result.projected_value == Decimal("70000000")
    assert result.total_contributed_principal == Decimal("70000000")
    assert result.investment_gain == Decimal("0")
    assert result.target_gap == Decimal("30000000")
    assert result.target_achievement_rate_pct == Decimal("70.0")
    assert result.required_monthly_contribution == Decimal("750000")
    assert result.additional_monthly_contribution == Decimal("250000")
    assert result.effective_target_amount_krw == Decimal("100000000")
    assert result.projected_value_in_today_money == result.projected_value


def test_positive_return_builds_yearly_milestones_and_sensitivity() -> None:
    goal_request = request(return_rate="7", years=30, target="500000000")
    result = service.simulate(goal_request)

    assert result.projected_value > result.total_contributed_principal
    assert len(result.milestones) == 30
    assert result.milestones[0].year == 1
    assert result.milestones[-1].projected_value == result.projected_value
    assert [scenario.kind for scenario in result.sensitivity] == [
        "lower",
        "base",
        "higher",
    ]
    assert result.sensitivity[0].projected_value < result.sensitivity[1].projected_value
    assert result.sensitivity[1].projected_value < result.sensitivity[2].projected_value

    catch_up = service.simulate(
        request(
            return_rate="7",
            years=30,
            target="500000000",
            monthly=str(result.required_monthly_contribution),
        )
    )
    assert catch_up.projected_value >= result.effective_target_amount_krw


def test_inflation_adjusted_target_and_growing_contributions() -> None:
    goal_request = request(
        current_assets="0",
        target="2500000",
        monthly="100000",
        years=2,
        inflation_rate="5",
        target_in_today_money=True,
        contribution_growth_rate="10",
    )

    result = service.simulate(goal_request)

    assert result.effective_target_amount_krw == Decimal("2756250")
    assert result.projected_value == Decimal("2520000")
    assert result.projected_value_in_today_money == Decimal("2285714")
    assert result.total_contributed_principal == Decimal("2520000")
    assert result.milestones[0].annual_contribution == Decimal("1200000")
    assert result.milestones[1].annual_contribution == Decimal("1320000")
    assert result.required_monthly_contribution == Decimal("109375")

    catch_up = service.simulate(
        request(
            current_assets="0",
            target="2500000",
            monthly=str(result.required_monthly_contribution),
            years=2,
            inflation_rate="5",
            target_in_today_money=True,
            contribution_growth_rate="10",
        )
    )
    assert catch_up.projected_value >= result.effective_target_amount_krw


def test_target_already_covered_requires_no_new_contribution() -> None:
    result = service.simulate(
        request(current_assets="120000000", target="100000000", monthly="0")
    )

    assert result.required_monthly_contribution == Decimal("0")
    assert result.additional_monthly_contribution == Decimal("0")
    assert result.target_gap == Decimal("0")
    assert result.target_surplus == Decimal("20000000")


def test_unreachable_input_reports_required_monthly_above_supported_limit() -> None:
    result = service.simulate(
        request(current_assets="0", target="10000000000000", monthly="0", years=1)
    )

    assert result.required_monthly_contribution > Decimal("100000000")
    assert result.required_monthly_within_supported_limit is False
