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
) -> GoalSimulationRequest:
    return GoalSimulationRequest(
        current_assets_krw=current_assets,
        target_amount_krw=target,
        monthly_contribution_krw=monthly,
        investment_years=years,
        annual_return_rate_pct=return_rate,
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
    assert catch_up.projected_value >= goal_request.target_amount_krw


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
