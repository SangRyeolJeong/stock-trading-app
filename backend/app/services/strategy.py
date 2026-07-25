from app.schemas.strategy import StrategyRequest, StrategyResponse


class StrategyService:
    def recommend(self, request: StrategyRequest) -> StrategyResponse:
        pension_weight = 40 if request.goal == "retirement" else 20
        growth_weight = 50 if request.risk_profile == "growth" else 35
        cash_weight = 100 - pension_weight - growth_weight
        return StrategyResponse(
            title="장기 성장 · 계좌 분산 전략",
            score=94 if request.horizon_years >= 20 else 82,
            allocation={
                "해외주식 직투": growth_weight,
                "연금저축 국내상장 ETF": pension_weight,
                "현금성 자산": cash_weight,
            },
            reason_codes=[
                "LONG_TERM_GOAL",
                "TAX_CREDIT_ELIGIBLE",
                "LIQUIDITY_REQUIRED",
            ],
            reasons=[
                "투자 기간이 길어 비용 차이가 누적될 수 있습니다.",
                "연금 목적 자금과 자유롭게 쓸 자금을 계좌별로 분리합니다.",
                "세액공제 계산은 규칙 엔진으로 검증하고 AI는 설명만 담당합니다.",
            ],
            disclaimer="예시 분석이며 투자 권유가 아닙니다. 세법과 상품 정보는 실행 전 다시 확인하세요.",
        )


strategy_service = StrategyService()
