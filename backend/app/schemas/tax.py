from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

AccountType = Literal["direct", "isa", "pension", "irp"]


class TaxSimulationRequest(BaseModel):
    annual_salary_krw: Decimal = Field(ge=0, le=Decimal("10000000000"))
    monthly_contribution_krw: Decimal = Field(gt=0, le=Decimal("100000000"))
    investment_years: int = Field(ge=3, le=40)
    annual_return_rate_pct: Decimal = Field(ge=Decimal("-100"), le=Decimal("30"))
    withdrawal_age: int = Field(default=60, ge=55, le=100)


class TaxRuleSource(BaseModel):
    title: str
    url: str
    authority: str


class TaxRuleSummary(BaseModel):
    version: str
    effective_date: str
    parameters: dict[str, str]
    sources: list[TaxRuleSource]


class TaxAccountResult(BaseModel):
    account_type: AccountType
    name: str
    tag: str
    tax_description: str
    contribution_limit_description: str
    recommended_product: str
    eligible_contribution: Decimal
    overflow_contribution: Decimal
    gross_value: Decimal
    contribution_tax_credit: Decimal
    investment_tax: Decimal
    withdrawal_tax: Decimal
    after_tax_value: Decimal
    tax_savings_vs_direct: Decimal
    score: int
    benefits: list[str]
    cautions: list[str]


class TaxSimulationResponse(BaseModel):
    best_account_type: AccountType
    results: list[TaxAccountResult]
    rules: TaxRuleSummary
    assumptions: list[str]
    disclaimer: str
