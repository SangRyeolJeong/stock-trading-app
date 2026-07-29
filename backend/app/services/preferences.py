from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preferences import UserPreferences
from app.schemas.preferences import UserPreferencesPayload, UserPreferencesResponse


class UserPreferencesService:
    @staticmethod
    async def get(
        session: AsyncSession,
        user_id: str,
    ) -> UserPreferencesResponse | None:
        preferences = await session.scalar(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        if preferences is None:
            return None
        return UserPreferencesResponse.model_validate(preferences)

    async def upsert(
        self,
        session: AsyncSession,
        user_id: str,
        payload: UserPreferencesPayload,
    ) -> UserPreferencesResponse:
        values = {
            "user_id": user_id,
            **payload.model_dump(),
        }
        update_values = {
            **payload.model_dump(),
            "updated_at": func.now(),
        }
        dialect_name = session.get_bind().dialect.name
        if dialect_name == "postgresql":
            statement = postgresql_insert(UserPreferences).values(**values)
            statement = statement.on_conflict_do_update(
                index_elements=[UserPreferences.user_id],
                set_=update_values,
            )
        elif dialect_name == "sqlite":
            statement = sqlite_insert(UserPreferences).values(**values)
            statement = statement.on_conflict_do_update(
                index_elements=[UserPreferences.user_id],
                set_=update_values,
            )
        else:
            raise RuntimeError(
                f"지원하지 않는 사용자 설정 데이터베이스입니다: {dialect_name}"
            )

        async with session.begin():
            await session.execute(statement)
            preferences = await session.scalar(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            if preferences is None:
                raise RuntimeError("사용자 설정을 저장하지 못했습니다.")
            return UserPreferencesResponse.model_validate(preferences)


user_preferences_service = UserPreferencesService()
