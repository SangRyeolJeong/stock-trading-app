from dataclasses import dataclass

from app.schemas.strategy import (
    StrategyActionStep,
    StrategyAllocation,
    StrategyReason,
    StrategyRequest,
    StrategyResponse,
    StrategyRiskSummary,
)

ENGINE_VERSION = "STRATEGY-2026.07"


@dataclass
class AllocationWeights:
    growth: int
    income: int
    defensive: int
    cash: int

    def shift(self, source: str, target: str, amount: int) -> None:
        movable = min(getattr(self, source), amount)
        setattr(self, source, getattr(self, source) - movable)
        setattr(self, target, getattr(self, target) + movable)

    @property
    def total(self) -> int:
        return self.growth + self.income + self.defensive + self.cash


BASE_WEIGHTS = {
    "conservative": AllocationWeights(growth=30, income=15, defensive=35, cash=20),
    "balanced": AllocationWeights(growth=55, income=15, defensive=20, cash=10),
    "growth": AllocationWeights(growth=75, income=10, defensive=10, cash=5),
}

EQUITY_CAPS = {
    "conservative": 50,
    "balanced": 75,
    "growth": 90,
}


class StrategyService:
    def recommend(self, request: StrategyRequest) -> StrategyResponse:
        weights = self._calculate_weights(request)
        allocations = self._build_allocations(request, weights)
        rationale = self._build_rationale(request)
        risk_summary = self._build_risk_summary(request, weights)

        return StrategyResponse(
            engine_version=ENGINE_VERSION,
            strategy_id=self._strategy_id(request),
            title=self._title(request),
            summary=self._summary(request, risk_summary),
            score=self._score(request),
            allocation={item.label: item.weight_pct for item in allocations},
            allocations=allocations,
            reason_codes=[reason.code for reason in rationale],
            reasons=[reason.description for reason in rationale],
            rationale=rationale,
            risk_summary=risk_summary,
            action_steps=self._action_steps(request),
            warnings=self._warnings(request),
            assumptions=[
                "월 투자금은 매월 같은 시점에 정액 납입한다고 가정합니다.",
                "자산 비중은 최소 연 1회 점검하고 목표 비중에서 5%p 이상 벗어나면 재조정합니다.",
                "상품 예시는 자산군 이해를 돕기 위한 것으로 실제 매수 전 비용과 위험을 비교해야 합니다.",
            ],
            disclaimer="예시 분석이며 투자 권유가 아닙니다. 세법과 상품 정보는 실행 전 다시 확인하세요.",
        )

    def _calculate_weights(self, request: StrategyRequest) -> AllocationWeights:
        base = BASE_WEIGHTS[request.risk_profile]
        weights = AllocationWeights(**vars(base))

        if request.goal == "cashflow":
            weights.shift("growth", "income", 15)
        elif request.goal == "lump_sum" and request.horizon_years <= 10:
            weights.shift("growth", "defensive", 5)
            weights.shift("growth", "cash", 5)

        if request.horizon_years <= 5:
            weights.shift("growth", "defensive", 10)
            weights.shift("growth", "cash", 5)
        elif request.horizon_years >= 20:
            weights.shift("defensive", "growth", 5)

        if request.income_preference and request.goal != "cashflow":
            weights.shift("growth", "income", 10)

        minimum_cash = 15 if request.liquidity_preference else 5
        if weights.cash < minimum_cash:
            weights.shift("growth", "cash", minimum_cash - weights.cash)

        equity_weight = weights.growth + weights.income
        equity_excess = max(0, equity_weight - EQUITY_CAPS[request.risk_profile])
        if equity_excess:
            weights.shift("growth", "defensive", equity_excess)

        if weights.total != 100:
            raise ValueError("Strategy allocation must total 100%.")
        return weights

    def _build_allocations(
        self,
        request: StrategyRequest,
        weights: AllocationWeights,
    ) -> list[StrategyAllocation]:
        account_plan = {
            "retirement": {
                "growth": ("pension", "연금계좌 글로벌 성장 ETF"),
                "income": ("isa", "ISA 배당성장 ETF"),
                "defensive": ("irp", "IRP 채권·혼합형 자산"),
            },
            "lump_sum": {
                "growth": ("isa", "ISA 글로벌 지수 ETF"),
                "income": ("isa", "ISA 배당성장 ETF"),
                "defensive": ("isa", "ISA 단기채 ETF"),
            },
            "cashflow": {
                "growth": ("isa", "ISA 글로벌 지수 ETF"),
                "income": ("direct", "배당성장 ETF"),
                "defensive": ("isa", "ISA 채권 ETF"),
            },
        }[request.goal]
        labels = {
            "growth": "글로벌 성장주",
            "income": "배당·인컴 자산",
            "defensive": "채권·방어 자산",
            "cash": "현금성 자산",
        }
        roles = {
            "growth": "장기 자본 성장",
            "income": "배당과 변동성 완충",
            "defensive": "하락 위험과 목표 시점 방어",
            "cash": "비상자금과 매수 대기자금",
        }
        allocation_specs = [
            ("growth", weights.growth, *account_plan["growth"]),
            ("income", weights.income, *account_plan["income"]),
            ("defensive", weights.defensive, *account_plan["defensive"]),
            ("cash", weights.cash, "cash", "CMA·MMF 등 현금성 상품"),
        ]

        result: list[StrategyAllocation] = []
        allocated_amount = 0
        for index, (asset_class, weight, account_type, product) in enumerate(allocation_specs):
            if index == len(allocation_specs) - 1:
                monthly_amount = request.monthly_amount_krw - allocated_amount
            else:
                monthly_amount = request.monthly_amount_krw * weight // 100
                allocated_amount += monthly_amount
            result.append(
                StrategyAllocation(
                    asset_class=asset_class,
                    label=labels[asset_class],
                    weight_pct=weight,
                    monthly_amount_krw=monthly_amount,
                    account_type=account_type,
                    product_example=product,
                    role=roles[asset_class],
                )
            )
        return result

    def _build_rationale(self, request: StrategyRequest) -> list[StrategyReason]:
        goal_reason = {
            "retirement": StrategyReason(
                code="GOAL_RETIREMENT",
                title="은퇴 목적 계좌 분리",
                description="은퇴자금은 연금계좌를 중심으로 배치하고 유동성 자금은 ISA와 현금으로 분리합니다.",
            ),
            "lump_sum": StrategyReason(
                code="GOAL_LUMP_SUM",
                title="목표 시점 방어",
                description="목돈 사용 시점이 가까워질수록 채권과 현금 비중을 높일 수 있는 구조입니다.",
            ),
            "cashflow": StrategyReason(
                code="GOAL_CASHFLOW",
                title="현금흐름 강화",
                description="성장 자산 일부를 배당·인컴 자산으로 옮겨 정기적인 분배 재원을 확보합니다.",
            ),
        }[request.goal]
        horizon_code = (
            "HORIZON_SHORT"
            if request.horizon_years <= 5
            else "HORIZON_LONG"
            if request.horizon_years >= 20
            else "HORIZON_MEDIUM"
        )
        horizon_reason = StrategyReason(
            code=horizon_code,
            title=f"{request.horizon_years}년 투자기간 반영",
            description=(
                "짧은 투자기간의 원금 변동 위험을 낮추기 위해 방어 자산 비중을 높였습니다."
                if request.horizon_years <= 5
                else "장기 복리 효과를 활용하되 목표 시점에 맞춰 정기적으로 비중을 점검합니다."
                if request.horizon_years >= 20
                else "성장 가능성과 목표 시점의 자금 안정성을 함께 반영했습니다."
            ),
        )
        risk_reason = StrategyReason(
            code=f"RISK_{request.risk_profile.upper()}",
            title={"conservative": "안정형 위험 한도", "balanced": "균형형 위험 한도", "growth": "성장형 위험 한도"}[
                request.risk_profile
            ],
            description={
                "conservative": "주식성 자산을 50% 이하로 제한해 손실 가능성을 낮췄습니다.",
                "balanced": "주식과 방어 자산을 함께 보유해 성장성과 안정성의 균형을 맞췄습니다.",
                "growth": "장기 수익 잠재력을 위해 주식 비중을 높이되 현금 완충 자산을 유지합니다.",
            }[request.risk_profile],
        )
        reasons = [goal_reason, horizon_reason, risk_reason]
        if request.liquidity_preference:
            reasons.append(
                StrategyReason(
                    code="LIQUIDITY_BUFFER",
                    title="유동성 15% 이상 확보",
                    description="예상치 못한 지출이나 하락장 추가 매수에 대응할 현금성 자산을 확보했습니다.",
                )
            )
        if request.fee_sensitivity:
            reasons.append(
                StrategyReason(
                    code="LOW_COST_CORE",
                    title="저비용 상품 우선",
                    description="핵심 자산은 분산된 지수형 ETF를 우선해 장기 누적 비용을 낮춥니다.",
                )
            )
        return reasons

    def _build_risk_summary(
        self,
        request: StrategyRequest,
        weights: AllocationWeights,
    ) -> StrategyRiskSummary:
        notes = {
            "conservative": "시장 하락기에도 변동을 줄이는 구성이지만 원금 손실 가능성은 있습니다.",
            "balanced": "중간 수준의 가격 변동을 감수하며 성장과 방어를 함께 추구합니다.",
            "growth": "큰 가격 변동과 일시적 손실을 감수하는 장기 투자자에게 맞춘 구성입니다.",
        }
        return StrategyRiskSummary(
            level=request.risk_profile,
            equity_weight_pct=weights.growth + weights.income,
            defensive_weight_pct=weights.defensive,
            liquidity_weight_pct=weights.cash,
            volatility_note=notes[request.risk_profile],
        )

    def _score(self, request: StrategyRequest) -> int:
        score = 76
        if request.risk_profile == "growth":
            score += 10 if request.horizon_years >= 15 else -8 if request.horizon_years <= 5 else 3
        elif request.risk_profile == "balanced":
            score += 8
        else:
            score += 9 if request.horizon_years <= 10 else 4

        if request.goal == "retirement" and request.horizon_years >= 20:
            score += 7
        elif request.goal == "lump_sum" and 5 <= request.horizon_years <= 15:
            score += 6
        elif request.goal == "cashflow" and request.income_preference:
            score += 6
        else:
            score += 2

        score += int(request.liquidity_preference) + int(request.fee_sensitivity)
        return min(98, max(60, score))

    def _strategy_id(self, request: StrategyRequest) -> str:
        horizon_bucket = "short" if request.horizon_years <= 5 else "long" if request.horizon_years >= 20 else "medium"
        return f"{request.goal}-{request.risk_profile}-{horizon_bucket}"

    def _title(self, request: StrategyRequest) -> str:
        goal_title = {
            "retirement": "연금계좌 중심 장기 성장",
            "lump_sum": "목표시점 맞춤 자산배분",
            "cashflow": "배당·인컴 현금흐름",
        }
        risk_title = {"conservative": "안정형", "balanced": "균형형", "growth": "성장형"}
        return f"{goal_title[request.goal]} · {risk_title[request.risk_profile]}"

    def _summary(self, request: StrategyRequest, risk: StrategyRiskSummary) -> str:
        return (
            f"매월 {request.monthly_amount_krw:,}원을 {request.horizon_years}년 동안 투자하며, "
            f"주식성 자산 {risk.equity_weight_pct}%와 방어·현금 자산 "
            f"{risk.defensive_weight_pct + risk.liquidity_weight_pct}%로 구성합니다."
        )

    def _action_steps(self, request: StrategyRequest) -> list[StrategyActionStep]:
        account_step = {
            "retirement": "연금저축·IRP의 납입 가능액과 세액공제 한도를 먼저 확인합니다.",
            "lump_sum": "ISA 가입 가능 여부와 목표 자금의 정확한 사용 시점을 확인합니다.",
            "cashflow": "분배 주기와 배당 변동 이력을 확인하고 생활비와 투자금을 분리합니다.",
        }[request.goal]
        return [
            StrategyActionStep(order=1, title="계좌 준비", description=account_step),
            StrategyActionStep(
                order=2,
                title="월 자동매수 설정",
                description=f"월 {request.monthly_amount_krw:,}원을 추천 비중대로 나눠 자동매수합니다.",
            ),
            StrategyActionStep(
                order=3,
                title="정기 리밸런싱",
                description="반기마다 점검하고 목표 비중에서 5%p 이상 벗어난 자산만 조정합니다.",
            ),
        ]

    def _warnings(self, request: StrategyRequest) -> list[str]:
        warnings = []
        if request.risk_profile == "growth" and request.horizon_years <= 5:
            warnings.append("투자기간이 짧은 성장형 전략은 목표 시점에 큰 손실이 남아 있을 수 있습니다.")
        if request.goal == "retirement":
            warnings.append("연금계좌는 중도인출 시 세제상 불이익이나 인출 제한이 발생할 수 있습니다.")
        if request.goal == "cashflow":
            warnings.append("배당금은 확정 수익이 아니며 기업과 시장 상황에 따라 감소할 수 있습니다.")
        if request.tax_efficiency_priority:
            warnings.append("계좌별 납입 한도와 공제율은 개인 소득 및 최신 세법에 따라 달라질 수 있습니다.")
        return warnings


strategy_service = StrategyService()
