from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.schemas.goal import (
    GoalMilestone,
    GoalSensitivityScenario,
    GoalSimulationRequest,
    GoalSimulationResponse,
)

ENGINE_VERSION = "GOAL-2026.08.2"
WON = Decimal("1")
PERCENT = Decimal("0.1")
ZERO = Decimal("0")
ONE = Decimal("1")
TWELVE = Decimal("12")
MAX_MONTHLY_CONTRIBUTION = Decimal("100000000")


def won(value: Decimal) -> Decimal:
    return value.quantize(WON, rounding=ROUND_HALF_UP)


def achievement_rate(value: Decimal, target: Decimal) -> Decimal:
    return (value / target * Decimal("100")).quantize(
        PERCENT,
        rounding=ROUND_HALF_UP,
    )


class GoalSimulationService:
    @staticmethod
    def _future_value_factor(
        years: int,
        annual_rate: Decimal,
        contribution_growth_rate: Decimal,
    ) -> Decimal:
        factor = ZERO
        contribution_multiplier = ONE
        for _ in range(years):
            factor = factor * (ONE + annual_rate) + contribution_multiplier
            contribution_multiplier *= ONE + contribution_growth_rate
        return factor

    @classmethod
    def _project_value(
        cls,
        *,
        current_assets: Decimal,
        initial_annual_contribution: Decimal,
        years: int,
        annual_rate: Decimal,
        contribution_growth_rate: Decimal,
    ) -> Decimal:
        balance = current_assets
        annual_contribution = initial_annual_contribution
        for _ in range(years):
            balance = balance * (ONE + annual_rate) + annual_contribution
            annual_contribution *= ONE + contribution_growth_rate
        return won(balance)

    @classmethod
    def _required_monthly_contribution(
        cls,
        *,
        current_assets: Decimal,
        target_amount: Decimal,
        years: int,
        annual_rate: Decimal,
        contribution_growth_rate: Decimal,
    ) -> Decimal:
        current_assets_at_goal = current_assets * (ONE + annual_rate) ** years
        remaining_target = max(target_amount - current_assets_at_goal, ZERO)
        if remaining_target == ZERO:
            return ZERO
        factor = cls._future_value_factor(
            years,
            annual_rate,
            contribution_growth_rate,
        )
        required_annual = remaining_target / factor
        return (required_annual / TWELVE).quantize(WON, rounding=ROUND_CEILING)

    @classmethod
    def _milestones(
        cls,
        request: GoalSimulationRequest,
        annual_rate: Decimal,
        initial_annual_contribution: Decimal,
        contribution_growth_rate: Decimal,
        effective_target: Decimal,
    ) -> list[GoalMilestone]:
        balance = request.current_assets_krw
        contributed_principal = request.current_assets_krw
        annual_contribution = initial_annual_contribution
        milestones: list[GoalMilestone] = []
        for year in range(1, request.investment_years + 1):
            balance = balance * (ONE + annual_rate) + annual_contribution
            contributed_principal += annual_contribution
            projected_value = won(balance)
            milestones.append(
                GoalMilestone(
                    year=year,
                    contributed_principal=won(contributed_principal),
                    annual_contribution=won(annual_contribution),
                    projected_value=projected_value,
                    target_achievement_rate_pct=achievement_rate(
                        projected_value,
                        effective_target,
                    ),
                )
            )
            annual_contribution *= ONE + contribution_growth_rate
        return milestones

    @classmethod
    def _sensitivity(
        cls,
        request: GoalSimulationRequest,
        initial_annual_contribution: Decimal,
        contribution_growth_rate: Decimal,
        effective_target: Decimal,
    ) -> list[GoalSensitivityScenario]:
        base_rate_pct = request.annual_return_rate_pct
        rates = [
            ("lower", max(base_rate_pct - Decimal("2"), Decimal("-100"))),
            ("base", base_rate_pct),
            ("higher", min(base_rate_pct + Decimal("2"), Decimal("30"))),
        ]
        scenarios: list[GoalSensitivityScenario] = []
        for kind, rate_pct in rates:
            projected_value = cls._project_value(
                current_assets=request.current_assets_krw,
                initial_annual_contribution=initial_annual_contribution,
                years=request.investment_years,
                annual_rate=rate_pct / Decimal("100"),
                contribution_growth_rate=contribution_growth_rate,
            )
            scenarios.append(
                GoalSensitivityScenario(
                    kind=kind,
                    annual_return_rate_pct=rate_pct,
                    projected_value=projected_value,
                    target_achievement_rate_pct=achievement_rate(
                        projected_value,
                        effective_target,
                    ),
                )
            )
        return scenarios

    def simulate(self, request: GoalSimulationRequest) -> GoalSimulationResponse:
        annual_rate = request.annual_return_rate_pct / Decimal("100")
        inflation_rate = request.annual_inflation_rate_pct / Decimal("100")
        contribution_growth_rate = (
            request.annual_contribution_growth_rate_pct / Decimal("100")
        )
        initial_annual_contribution = won(request.monthly_contribution_krw * TWELVE)
        inflation_factor = (ONE + inflation_rate) ** request.investment_years
        effective_target = won(
            request.target_amount_krw * inflation_factor
            if request.target_amount_in_today_money
            else request.target_amount_krw
        )
        projected_value = self._project_value(
            current_assets=request.current_assets_krw,
            initial_annual_contribution=initial_annual_contribution,
            years=request.investment_years,
            annual_rate=annual_rate,
            contribution_growth_rate=contribution_growth_rate,
        )
        contribution_factor = self._future_value_factor(
            request.investment_years,
            ZERO,
            contribution_growth_rate,
        )
        total_principal = won(
            request.current_assets_krw
            + initial_annual_contribution * contribution_factor
        )
        required_monthly = self._required_monthly_contribution(
            current_assets=request.current_assets_krw,
            target_amount=effective_target,
            years=request.investment_years,
            annual_rate=annual_rate,
            contribution_growth_rate=contribution_growth_rate,
        )
        return GoalSimulationResponse(
            engine_version=ENGINE_VERSION,
            projected_value=projected_value,
            projected_value_in_today_money=won(projected_value / inflation_factor),
            effective_target_amount_krw=effective_target,
            total_contributed_principal=total_principal,
            investment_gain=won(projected_value - total_principal),
            target_gap=won(max(effective_target - projected_value, ZERO)),
            target_surplus=won(max(projected_value - effective_target, ZERO)),
            target_achievement_rate_pct=achievement_rate(
                projected_value,
                effective_target,
            ),
            required_monthly_contribution=required_monthly,
            additional_monthly_contribution=won(
                max(required_monthly - request.monthly_contribution_krw, ZERO)
            ),
            required_monthly_within_supported_limit=(
                required_monthly <= MAX_MONTHLY_CONTRIBUTION
            ),
            milestones=self._milestones(
                request,
                annual_rate,
                initial_annual_contribution,
                contribution_growth_rate,
                effective_target,
            ),
            sensitivity=self._sensitivity(
                request,
                initial_annual_contribution,
                contribution_growth_rate,
                effective_target,
            ),
            assumptions=[
                "현재 자산은 첫해부터 운용하고 월 투자금의 12배를 매년 말 납입합니다.",
                "입력한 연 수익률이 투자기간 동안 매년 동일하게 적용된다고 가정합니다.",
                (
                    "월 투자금은 첫해 금액이며 이후 매년 입력한 증액률만큼 증가합니다."
                    if contribution_growth_rate > ZERO
                    else "월 투자금은 투자기간 동안 매년 동일하다고 가정합니다."
                ),
                (
                    "목표 금액은 현재가치 기준이며 입력 물가상승률로 만기 명목 목표를 계산합니다."
                    if request.target_amount_in_today_money
                    else "목표 금액은 만기 시점의 명목 금액 기준입니다."
                ),
                "수익률 민감도는 입력값보다 2%p 낮거나 높은 경우를 비교하며 예측값이 아닙니다.",
                "세금, 수수료, 환율과 실제 수익률·물가 변동은 반영하지 않습니다.",
            ],
            formula=(
                "연도별 예상 자산 = 전년 자산 × (1 + 연수익률) + 해당 연도 납입액; "
                "해당 연도 납입액 = 첫해 납입액 × (1 + 연증액률)^(연도-1)"
            ),
            disclaimer=(
                "물가와 납입 증가를 일정한 비율로 단순화한 복리 시뮬레이션이며 실제 "
                "수익, 구매력이나 목표 달성을 보장하지 않습니다."
            ),
        )


goal_simulation_service = GoalSimulationService()
