from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(
            "annual_salary_krw >= 0 AND annual_salary_krw <= 1000000000",
            name="annual_salary_range",
        ),
        CheckConstraint(
            "monthly_investment_krw >= 10000 AND monthly_investment_krw <= 100000000",
            name="monthly_investment_range",
        ),
        CheckConstraint(
            "investment_years >= 3 AND investment_years <= 40",
            name="investment_years_range",
        ),
        CheckConstraint(
            "annual_return_rate_pct >= 0 AND annual_return_rate_pct <= 30",
            name="annual_return_rate_range",
        ),
        CheckConstraint(
            "withdrawal_age >= 55 AND withdrawal_age <= 100",
            name="withdrawal_age_range",
        ),
        CheckConstraint(
            "strategy_goal IN ('retirement', 'lump_sum', 'cashflow')",
            name="strategy_goal_allowed",
        ),
        CheckConstraint(
            "risk_profile IN ('conservative', 'balanced', 'growth')",
            name="risk_profile_allowed",
        ),
    )

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(20))
    annual_salary_krw: Mapped[int] = mapped_column(BigInteger)
    monthly_investment_krw: Mapped[int] = mapped_column(BigInteger)
    investment_years: Mapped[int] = mapped_column(Integer)
    annual_return_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    withdrawal_age: Mapped[int] = mapped_column(Integer)
    strategy_goal: Mapped[str] = mapped_column(String(20))
    risk_profile: Mapped[str] = mapped_column(String(20))
    liquidity_preference: Mapped[bool] = mapped_column(Boolean)
    fee_sensitivity: Mapped[bool] = mapped_column(Boolean)
    income_preference: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
