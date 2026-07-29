"""Store authenticated user investment preferences.

Revision ID: 20260729_0003
Revises: 20260729_0002
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0003"
down_revision: str | None = "20260729_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=20), nullable=False),
        sa.Column("annual_salary_krw", sa.BigInteger(), nullable=False),
        sa.Column("monthly_investment_krw", sa.BigInteger(), nullable=False),
        sa.Column("investment_years", sa.Integer(), nullable=False),
        sa.Column("annual_return_rate_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("withdrawal_age", sa.Integer(), nullable=False),
        sa.Column("strategy_goal", sa.String(length=20), nullable=False),
        sa.Column("risk_profile", sa.String(length=20), nullable=False),
        sa.Column("liquidity_preference", sa.Boolean(), nullable=False),
        sa.Column("fee_sensitivity", sa.Boolean(), nullable=False),
        sa.Column("income_preference", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "annual_salary_krw >= 0 AND annual_salary_krw <= 1000000000",
            name=op.f("ck_user_preferences_annual_salary_range"),
        ),
        sa.CheckConstraint(
            "monthly_investment_krw >= 10000 "
            "AND monthly_investment_krw <= 100000000",
            name=op.f("ck_user_preferences_monthly_investment_range"),
        ),
        sa.CheckConstraint(
            "investment_years >= 3 AND investment_years <= 40",
            name=op.f("ck_user_preferences_investment_years_range"),
        ),
        sa.CheckConstraint(
            "annual_return_rate_pct >= 0 AND annual_return_rate_pct <= 30",
            name=op.f("ck_user_preferences_annual_return_rate_range"),
        ),
        sa.CheckConstraint(
            "withdrawal_age >= 55 AND withdrawal_age <= 100",
            name=op.f("ck_user_preferences_withdrawal_age_range"),
        ),
        sa.CheckConstraint(
            "strategy_goal IN ('retirement', 'lump_sum', 'cashflow')",
            name=op.f("ck_user_preferences_strategy_goal_allowed"),
        ),
        sa.CheckConstraint(
            "risk_profile IN ('conservative', 'balanced', 'growth')",
            name=op.f("ck_user_preferences_risk_profile_allowed"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            name=op.f("pk_user_preferences"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
