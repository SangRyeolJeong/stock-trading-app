from decimal import ROUND_HALF_UP, Decimal

from app.schemas.tax import (
    TaxAccountResult,
    TaxRuleSource,
    TaxRuleSummary,
    TaxSimulationRequest,
    TaxSimulationResponse,
)
from app.tax.rules import TAX_RULES_2026, TaxRules

WON = Decimal("1")
ZERO = Decimal("0")


def won(value: Decimal) -> Decimal:
    return value.quantize(WON, rounding=ROUND_HALF_UP)


def future_value(contributions: list[Decimal], annual_rate: Decimal) -> Decimal:
    balance = ZERO
    for contribution in contributions:
        balance = balance * (Decimal("1") + annual_rate) + contribution
    return won(balance)


class TaxCalculationService:
    def __init__(self, rules: TaxRules = TAX_RULES_2026) -> None:
        self.rules = rules

    def overseas_capital_gains_tax(self, capital_gain: Decimal) -> Decimal:
        taxable_gain = max(capital_gain - self.rules.overseas_capital_gains_deduction, ZERO)
        return won(taxable_gain * self.rules.overseas_capital_gains_tax_rate)

    def _direct_result(
        self,
        annual_contribution: Decimal,
        years: int,
        annual_rate: Decimal,
    ) -> TaxAccountResult:
        contributions = [annual_contribution] * years
        principal = won(sum(contributions, ZERO))
        gross_value = future_value(contributions, annual_rate)
        investment_tax = self.overseas_capital_gains_tax(gross_value - principal)
        return TaxAccountResult(
            account_type="direct",
            name="해외주식 직투",
            tag="유동성",
            tax_description="연간 손익통산 후 250만원 공제, 초과분 22%",
            contribution_limit_description="납입 한도 없음",
            recommended_product="QQQM 등 해외상장 ETF",
            eligible_contribution=principal,
            overflow_contribution=ZERO,
            gross_value=gross_value,
            contribution_tax_credit=ZERO,
            investment_tax=investment_tax,
            withdrawal_tax=ZERO,
            after_tax_value=won(gross_value - investment_tax),
            tax_savings_vs_direct=ZERO,
            score=0,
            benefits=["달러 자산을 직접 보유", "중도 인출과 매매 제약이 적음"],
            cautions=["매년 실현손익을 통산해 다음 해 5월 신고", "환율과 매매수수료는 별도 고려 필요"],
        )

    def _isa_result(
        self,
        annual_contribution: Decimal,
        years: int,
        annual_rate: Decimal,
        annual_salary: Decimal,
    ) -> TaxAccountResult:
        remaining_limit = self.rules.isa_total_contribution_limit
        isa_contributions: list[Decimal] = []
        overflow_contributions: list[Decimal] = []
        for _ in range(years):
            eligible = min(annual_contribution, self.rules.isa_annual_contribution_limit, remaining_limit)
            overflow = annual_contribution - eligible
            isa_contributions.append(eligible)
            overflow_contributions.append(overflow)
            remaining_limit -= eligible

        eligible_principal = won(sum(isa_contributions, ZERO))
        overflow_principal = won(sum(overflow_contributions, ZERO))
        isa_gross = future_value(isa_contributions, annual_rate)
        overflow_gross = future_value(overflow_contributions, annual_rate)
        exemption = (
            self.rules.isa_low_income_exemption
            if annual_salary <= self.rules.isa_low_income_salary_threshold
            else self.rules.isa_general_exemption
        )
        isa_gain = max(isa_gross - eligible_principal, ZERO)
        isa_tax = won(max(isa_gain - exemption, ZERO) * self.rules.isa_excess_tax_rate)
        overflow_tax = self.overseas_capital_gains_tax(overflow_gross - overflow_principal)
        total_tax = isa_tax + overflow_tax
        isa_type = "서민형" if exemption == self.rules.isa_low_income_exemption else "일반형"
        return TaxAccountResult(
            account_type="isa",
            name="중개형 ISA",
            tag="절세",
            tax_description=f"{isa_type} {int(exemption / Decimal('10000'))}만원 비과세 후 초과분 9.9%",
            contribution_limit_description="연 2,000만원, 누적 1억원 가정",
            recommended_product="국내상장 해외지수 ETF",
            eligible_contribution=eligible_principal,
            overflow_contribution=overflow_principal,
            gross_value=won(isa_gross + overflow_gross),
            contribution_tax_credit=ZERO,
            investment_tax=total_tax,
            withdrawal_tax=ZERO,
            after_tax_value=won(isa_gross + overflow_gross - total_tax),
            tax_savings_vs_direct=ZERO,
            score=0,
            benefits=["계좌 내 손익통산", "비과세 한도 초과분도 낮은 세율로 분리과세"],
            cautions=["해외상장 주식 직접 매수는 불가", "세제 혜택을 위해 3년 이상 유지 필요"],
        )

    def _pension_result(
        self,
        account_type: str,
        annual_contribution: Decimal,
        years: int,
        annual_rate: Decimal,
        annual_salary: Decimal,
        withdrawal_age: int,
    ) -> TaxAccountResult:
        credit_limit = (
            self.rules.pension_savings_credit_limit
            if account_type == "pension"
            else self.rules.retirement_pension_credit_limit
        )
        eligible_annual = min(annual_contribution, self.rules.pension_total_contribution_limit)
        overflow_annual = annual_contribution - eligible_annual
        eligible_contributions = [eligible_annual] * years
        overflow_contributions = [overflow_annual] * years
        eligible_principal = won(sum(eligible_contributions, ZERO))
        overflow_principal = won(sum(overflow_contributions, ZERO))
        credited_principal = won(min(eligible_annual, credit_limit) * years)
        noncredited_principal = eligible_principal - credited_principal
        credit_rate = (
            self.rules.pension_low_income_credit_rate
            if annual_salary <= self.rules.pension_low_income_salary_threshold
            else self.rules.pension_high_income_credit_rate
        )
        contribution_tax_credit = won(credited_principal * credit_rate)
        pension_gross = future_value(eligible_contributions, annual_rate)
        overflow_gross = future_value(overflow_contributions, annual_rate)
        withdrawal_rate = Decimal("0.055") if withdrawal_age < 70 else Decimal("0.044")
        if withdrawal_age >= 80:
            withdrawal_rate = Decimal("0.033")
        pension_taxable_amount = max(pension_gross - noncredited_principal, ZERO)
        withdrawal_tax = won(pension_taxable_amount * withdrawal_rate)
        overflow_tax = self.overseas_capital_gains_tax(overflow_gross - overflow_principal)
        is_pension = account_type == "pension"
        return TaxAccountResult(
            account_type=account_type,
            name="연금저축펀드" if is_pension else "IRP",
            tag="장기투자" if is_pension else "노후",
            tax_description=(
                f"세액공제 {int(credit_rate * 1000) / 10:.1f}%, "
                f"{withdrawal_age}세 연금수령세율 {float(withdrawal_rate * 100):.1f}% 가정"
            ),
            contribution_limit_description=(
                "세액공제 연 600만원" if is_pension else "퇴직연금 포함 세액공제 연 900만원"
            ),
            recommended_product=(
                "국내상장 해외지수 ETF" if is_pension else "ETF + 30% 이상 안전자산"
            ),
            eligible_contribution=eligible_principal,
            overflow_contribution=overflow_principal,
            gross_value=won(pension_gross + overflow_gross),
            contribution_tax_credit=contribution_tax_credit,
            investment_tax=overflow_tax,
            withdrawal_tax=withdrawal_tax,
            after_tax_value=won(
                pension_gross
                + overflow_gross
                - overflow_tax
                - withdrawal_tax
                + contribution_tax_credit
            ),
            tax_savings_vs_direct=ZERO,
            score=0,
            benefits=["납입 단계 세액공제", "운용 중 과세이연"],
            cautions=(
                ["55세 이전 인출 시 세제상 불이익 가능", "연금수령 한도와 기간을 별도 확인"]
                if is_pension
                else ["법정 사유 외 중도인출 제약", "위험자산 투자 한도 70%를 반영한 상품 구성이 필요"]
            ),
        )

    def simulate(self, request: TaxSimulationRequest) -> TaxSimulationResponse:
        annual_contribution = won(request.monthly_contribution_krw * Decimal("12"))
        annual_rate = request.annual_return_rate_pct / Decimal("100")
        direct = self._direct_result(annual_contribution, request.investment_years, annual_rate)
        results = [
            direct,
            self._isa_result(
                annual_contribution,
                request.investment_years,
                annual_rate,
                request.annual_salary_krw,
            ),
            self._pension_result(
                "pension",
                annual_contribution,
                request.investment_years,
                annual_rate,
                request.annual_salary_krw,
                request.withdrawal_age,
            ),
            self._pension_result(
                "irp",
                annual_contribution,
                request.investment_years,
                annual_rate,
                request.annual_salary_krw,
                request.withdrawal_age,
            ),
        ]

        min_value = min(result.after_tax_value for result in results)
        max_value = max(result.after_tax_value for result in results)
        spread = max_value - min_value
        scored_results: list[TaxAccountResult] = []
        for result in results:
            score = 100 if spread == 0 else 70 + int((result.after_tax_value - min_value) / spread * 30)
            scored_results.append(
                result.model_copy(
                    update={
                        "tax_savings_vs_direct": won(result.after_tax_value - direct.after_tax_value),
                        "score": score,
                    }
                )
            )
        best = max(scored_results, key=lambda result: result.after_tax_value)

        rules = self.rules
        return TaxSimulationResponse(
            best_account_type=best.account_type,
            results=scored_results,
            rules=TaxRuleSummary(
                version=rules.version,
                effective_date=rules.effective_date,
                parameters={
                    "isa_annual_limit_krw": str(rules.isa_annual_contribution_limit),
                    "isa_total_limit_krw": str(rules.isa_total_contribution_limit),
                    "pension_savings_credit_limit_krw": str(rules.pension_savings_credit_limit),
                    "retirement_pension_credit_limit_krw": str(rules.retirement_pension_credit_limit),
                    "overseas_capital_gains_deduction_krw": str(rules.overseas_capital_gains_deduction),
                },
                sources=[
                    TaxRuleSource(title=source.title, url=source.url, authority=source.authority)
                    for source in rules.sources
                ],
            ),
            assumptions=[
                "매년 말에 연간 투자금을 납입하고 입력 수익률로 복리 운용합니다.",
                "모든 자산은 마지막 해에 일괄 처분·수령하며 수수료와 환율 변동은 제외합니다.",
                "해외직투 양도소득 기본공제는 마지막 처분연도에 1회 적용합니다.",
                "ISA 서민형 여부는 다른 종합소득이 없는 근로자의 입력 총급여만으로 판정합니다.",
                "ISA는 한 계좌의 누적 납입한도 1억원까지만 적용하고 초과금은 해외직투로 계산합니다.",
                "각 계좌를 독립 비교하므로 IRP의 900만원 세액공제 한도는 다른 연금저축 납입이 없다고 가정합니다.",
                "연금 세액공제 환급액은 재투자하지 않고 최종 세후 가치에 합산합니다.",
                "연금은 연금수령 요건을 충족하고 연간 사적연금 수령액 관련 추가 과세가 없다고 가정합니다.",
            ],
            disclaimer="세법과 개인별 소득·수령 방식에 따라 실제 세액이 달라질 수 있는 비교용 추정치입니다.",
        )


tax_calculation_service = TaxCalculationService()
