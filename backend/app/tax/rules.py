from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TaxRuleSource:
    title: str
    url: str
    authority: str


@dataclass(frozen=True)
class TaxRules:
    version: str
    effective_date: str
    isa_annual_contribution_limit: Decimal
    isa_total_contribution_limit: Decimal
    isa_general_exemption: Decimal
    isa_low_income_exemption: Decimal
    isa_low_income_salary_threshold: Decimal
    isa_excess_tax_rate: Decimal
    pension_total_contribution_limit: Decimal
    pension_savings_credit_limit: Decimal
    retirement_pension_credit_limit: Decimal
    pension_low_income_salary_threshold: Decimal
    pension_low_income_credit_rate: Decimal
    pension_high_income_credit_rate: Decimal
    overseas_capital_gains_deduction: Decimal
    overseas_capital_gains_tax_rate: Decimal
    sources: tuple[TaxRuleSource, ...]


TAX_RULES_2026 = TaxRules(
    version="KR-2026.07",
    effective_date="2026-07-01",
    isa_annual_contribution_limit=Decimal("20000000"),
    isa_total_contribution_limit=Decimal("100000000"),
    isa_general_exemption=Decimal("2000000"),
    isa_low_income_exemption=Decimal("4000000"),
    isa_low_income_salary_threshold=Decimal("50000000"),
    isa_excess_tax_rate=Decimal("0.099"),
    pension_total_contribution_limit=Decimal("18000000"),
    pension_savings_credit_limit=Decimal("6000000"),
    retirement_pension_credit_limit=Decimal("9000000"),
    pension_low_income_salary_threshold=Decimal("55000000"),
    pension_low_income_credit_rate=Decimal("0.165"),
    pension_high_income_credit_rate=Decimal("0.132"),
    overseas_capital_gains_deduction=Decimal("2500000"),
    overseas_capital_gains_tax_rate=Decimal("0.22"),
    sources=(
        TaxRuleSource(
            title="조세특례제한법 제91조의18 - ISA 과세특례",
            url="https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000928713",
            authority="국가법령정보센터",
        ),
        TaxRuleSource(
            title="ISA 연 2천만원 납입·한도 이월·3년 계약",
            url="https://whatsnew.moef.go.kr/mec/ots/dif/view.do?comBaseCd=DIFGODEPRT&difGovDepart1=DIFGODR001&difSer=c514effc-c831-4eb1-94c7-6eab084dcac8&temp=2021&temp2=HALF001",
            authority="기획재정부",
        ),
        TaxRuleSource(
            title="연금계좌 세액공제 한도 및 공제율",
            url="https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=2238",
            authority="국세청",
        ),
        TaxRuleSource(
            title="연금계좌 일반 납입한도 연 1,800만원",
            url="https://www.law.go.kr/LSW/flDownload.do?bylClsCd=110202&flSeq=157665187&gubun=",
            authority="국가법령정보센터",
        ),
        TaxRuleSource(
            title="국내·국외주식 손익통산 및 기본공제",
            url="https://s.nts.go.kr/jongno/na/ntt/selectNttInfo.do?mi=2201&nttSn=1350890",
            authority="국세청",
        ),
        TaxRuleSource(
            title="소득세법 제104조 - 양도소득세율",
            url="https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1021859939",
            authority="국가법령정보센터",
        ),
        TaxRuleSource(
            title="연금계좌 과세대상과 연금수령 세율",
            url="https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=200000000000010709",
            authority="국세청 국세법령정보시스템",
        ),
    ),
)
