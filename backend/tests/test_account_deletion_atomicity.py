import pytest
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models.paper import PaperAccount
from app.models.preferences import UserPreferences
from app.schemas.preferences import UserPreferencesPayload
from app.services.account_deletion import AccountDeletionService
from app.services.paper_trading import PaperTradingService
from app.services.preferences import UserPreferencesService


def payload() -> UserPreferencesPayload:
    return UserPreferencesPayload(
        display_name="삭제 롤백",
        annual_salary_krw=45_000_000,
        monthly_investment_krw=500_000,
        investment_years=20,
        annual_return_rate_pct=7,
        withdrawal_age=60,
        strategy_goal="retirement",
        risk_profile="balanced",
        liquidity_preference=True,
        fee_sensitivity=True,
        income_preference=False,
    )


@pytest.mark.asyncio
async def test_failure_during_account_deletion_rolls_back_every_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = "delete-rollback-user"
    paper = PaperTradingService()
    preferences = UserPreferencesService()
    service = AccountDeletionService()
    async with async_session_factory() as session:
        async with session.begin():
            await paper.ensure_user_account(session, user_id)
        await preferences.upsert(session, user_id, payload())

    async def fail_after_preferences(*_args: object) -> None:
        raise RuntimeError("injected deletion failure")

    monkeypatch.setattr(service, "_delete_account_children", fail_after_preferences)
    with pytest.raises(RuntimeError):
        async with async_session_factory() as session:
            await service.delete_user_data(session, user_id)

    async with async_session_factory() as session:
        assert await session.scalar(
            select(func.count()).select_from(PaperAccount).where(PaperAccount.user_id == user_id)
        ) == 1
        assert await session.scalar(
            select(func.count()).select_from(UserPreferences).where(UserPreferences.user_id == user_id)
        ) == 1
