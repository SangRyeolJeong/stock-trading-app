from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.schemas.goal import (
    GoalMilestone,
    GoalSensitivityScenario,
    GoalSimulationRequest,
    GoalSimulationResponse,
)

ENGINE_VERSION = "GOAL-2026.08"
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
    def _future_value_factor(years: int, annual_rate: Decimal) -> Decimal:
        factor = ZERO
        for _ in range(years):
            factor = factor * (ONE + annual_rate) + ONE
        return factor

    @classmethod
    def _project_value(
        cls,
        *,
        current_assets: Decimal,
        annual_contribution: Decimal,
        years: int,
        annual_rate: Decimal,
    ) -> Decimal:
        balance = current_assets
        for _ in range(years):
            balance = balance * (ONE + annual_rate) + annual_contribution
        return won(balance)

    @classmethod
    def _required_monthly_contribution(
        cls,
        *,
        current_assets: Decimal,
        target_amount: Decimal,
        years: int,
        annual_rate: Decimal,
    ) -> Decimal:
        current_assets_at_goal = current_assets * (ONE + annual_rate) ** years
        remaining_target = max(target_amount - current_assets_at_goal, ZERO)
        if remaining_target == ZERO:
            return ZERO
        factor = cls._future_value_factor(years, annual_rate)
        required_annual = remaining_target / factor
        return (required_annual / TWELVE).quantize(WON, rounding=ROUND_CEILING)

    @classmethod
    def _milestones(
        cls,
        request: GoalSimulationRequest,
        annual_rate: Decimal,
        annual_contribution: Decimal,
    ) -> list[GoalMilestone]:
        balance = request.current_assets_krw
        milestones: list[GoalMilestone] = []
        for year in range(1, request.investment_years + 1):
            balance = balance * (ONE + annual_rate) + annual_contribution
            projected_value = won(balance)
            milestones.append(
                GoalMilestone(
                    year=year,
                    contributed_principal=won(
                        request.current_assets_krw + annual_contribution * year
                    ),
                    projected_value=projected_value,
                    target_achievement_rate_pct=achievement_rate(
                        projected_value,
                        request.target_amount_krw,
                    ),
                )
            )
        return milestones

    @classmethod
    def _sensitivity(
        cls,
        request: GoalSimulationRequest,
        annual_contribution: Decimal,
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
                annual_contribution=annual_contribution,
                years=request.investment_years,
                annual_rate=rate_pct / Decimal("100"),
            )
            scenarios.append(
                GoalSensitivityScenario(
                    kind=kind,
                    annual_return_rate_pct=rate_pct,
                    projected_value=projected_value,
                    target_achievement_rate_pct=achievement_rate(
                        projected_value,
                        request.target_amount_krw,
                    ),
                )
            )
        return scenarios

    def simulate(self, request: GoalSimulationRequest) -> GoalSimulationResponse:
        annual_rate = request.annual_return_rate_pct / Decimal("100")
        annual_contribution = won(request.monthly_contribution_krw * TWELVE)
        projected_value = self._project_value(
            current_assets=request.current_assets_krw,
            annual_contribution=annual_contribution,
            years=request.investment_years,
            annual_rate=annual_rate,
        )
        total_principal = won(
            request.current_assets_krw
            + annual_contribution * request.investment_years
        )
        required_monthly = self._required_monthly_contribution(
            current_assets=request.current_assets_krw,
            target_amount=request.target_amount_krw,
            years=request.investment_years,
            annual_rate=annual_rate,
        )
        return GoalSimulationResponse(
            engine_version=ENGINE_VERSION,
            projected_value=projected_value,
            total_contributed_principal=total_principal,
            investment_gain=won(projected_value - total_principal),
            target_gap=won(max(request.target_amount_krw - projected_value, ZERO)),
            target_surplus=won(max(projected_value - request.target_amount_krw, ZERO)),
            target_achievement_rate_pct=achievement_rate(
                projected_value,
                request.target_amount_krw,
            ),
            required_monthly_contribution=required_monthly,
            additional_monthly_contribution=won(
                max(required_monthly - request.monthly_contribution_krw, ZERO)
            ),
            required_monthly_within_supported_limit=(
                required_monthly <= MAX_MONTHLY_CONTRIBUTION
            ),
            milestones=self._milestones(request, annual_rate, annual_contribution),
            sensitivity=self._sensitivity(request, annual_contribution),
            assumptions=[
                "현재 자산은 첫해부터 운용하고 월 투자금의 12배를 매년 말 납입합니다.",
                "입력한 연 수익률이 투자기간 동안 매년 동일하게 적용된다고 가정합니다.",
                "수익률 민감도는 입력값보다 2%p 낮거나 높은 경우를 비교하며 예측값이 아닙니다.",
                "세금, 수수료, 물가, 환율과 실제 수익률 변동은 반영하지 않습니다.",
            ],
            formula=(
                "예상 자산 = 현재 자산 × (1 + 연수익률)^기간 + "
                "연간 납입액 × 연말 납입 미래가치계수"
            ),
            disclaimer=(
                "목표 계획을 점검하기 위한 단순 복리 시뮬레이션이며 실제 수익이나 "
                "목표 달성을 보장하지 않습니다."
            ),
        )


goal_simulation_service = GoalSimulationService()
