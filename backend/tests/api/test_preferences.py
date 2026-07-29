from collections.abc import Callable

from fastapi.testclient import TestClient

from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app

client = TestClient(app)


def use_user(user_id: str) -> Callable[[], None]:
    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(id=user_id)

    app.dependency_overrides[get_current_user] = override_current_user

    def restore() -> None:
        app.dependency_overrides.pop(get_current_user, None)

    return restore


def preferences_payload(display_name: str) -> dict[str, object]:
    return {
        "display_name": display_name,
        "annual_salary_krw": 45_000_000,
        "monthly_investment_krw": 500_000,
        "investment_years": 30,
        "annual_return_rate_pct": 7,
        "withdrawal_age": 60,
        "strategy_goal": "retirement",
        "risk_profile": "growth",
        "liquidity_preference": True,
        "fee_sensitivity": True,
        "income_preference": False,
    }


def test_missing_preferences_return_not_found() -> None:
    restore = use_user("preferences-missing-user")
    try:
        response = client.get("/api/v1/me/preferences")
    finally:
        restore()

    assert response.status_code == 404


def test_preferences_are_saved_and_updated_for_current_user() -> None:
    restore = use_user("preferences-user")
    try:
        created = client.put(
            "/api/v1/me/preferences",
            json=preferences_payload("  김모아  "),
        )
        updated_payload = preferences_payload("이모아")
        updated_payload["risk_profile"] = "balanced"
        updated = client.put("/api/v1/me/preferences", json=updated_payload)
        fetched = client.get("/api/v1/me/preferences")
    finally:
        restore()

    assert created.status_code == 200
    assert created.json()["display_name"] == "김모아"
    assert updated.status_code == 200
    assert fetched.json()["display_name"] == "이모아"
    assert fetched.json()["risk_profile"] == "balanced"
    assert "updated_at" in fetched.json()


def test_preferences_are_isolated_between_users() -> None:
    restore = use_user("preferences-user-a")
    try:
        response_a = client.put(
            "/api/v1/me/preferences",
            json=preferences_payload("사용자 A"),
        )
        assert response_a.status_code == 200

        restore()
        restore = use_user("preferences-user-b")
        response_b = client.get("/api/v1/me/preferences")
        assert response_b.status_code == 404

        restore()
        restore = use_user("preferences-user-a")
        fetched_a = client.get("/api/v1/me/preferences")
    finally:
        restore()

    assert fetched_a.json()["display_name"] == "사용자 A"


def test_preferences_reject_unknown_or_out_of_range_values() -> None:
    restore = use_user("preferences-invalid-user")
    try:
        payload = preferences_payload("테스트")
        payload["account_id"] = "another-user"
        extra_field = client.put("/api/v1/me/preferences", json=payload)

        payload = preferences_payload("테스트")
        payload["monthly_investment_krw"] = 0
        out_of_range = client.put("/api/v1/me/preferences", json=payload)
    finally:
        restore()

    assert extra_field.status_code == 422
    assert out_of_range.status_code == 422
