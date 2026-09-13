from collections.abc import Callable
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import async_session_factory
from app.main import app
from app.services.broker_orders import BrokerOrderCommand, BrokerOrderService

client = TestClient(app)


def use_user(user_id: str) -> Callable[[], None]:
    async def override_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(id=user_id)

    app.dependency_overrides[get_current_user] = override_current_user

    def restore() -> None:
        app.dependency_overrides.pop(get_current_user, None)

    return restore


def preferences_payload(name: str) -> dict[str, object]:
    return {
        "display_name": name,
        "annual_salary_krw": 45_000_000,
        "monthly_investment_krw": 500_000,
        "investment_years": 20,
        "annual_return_rate_pct": 7,
        "withdrawal_age": 60,
        "strategy_goal": "retirement",
        "risk_profile": "balanced",
        "liquidity_preference": True,
        "fee_sensitivity": True,
        "income_preference": False,
    }


def market_order(key: str) -> dict[str, object]:
    return {
        "symbol": "QQQM",
        "side": "buy",
        "order_type": "market",
        "quantity": 1,
        "idempotency_key": key,
    }


def test_delete_me_requires_exact_confirmation() -> None:
    missing = client.request("DELETE", "/api/v1/me", json={})
    wrong = client.request("DELETE", "/api/v1/me", json={"confirmation": "delete"})

    assert missing.status_code == 422
    assert wrong.status_code == 422


def test_delete_me_removes_only_current_users_local_data() -> None:
    restore = use_user("delete-user-a")
    try:
        assert client.put("/api/v1/me/preferences", json=preferences_payload("사용자 A")).status_code == 200
        assert client.post("/api/v1/paper/orders", json=market_order("delete-a-0001")).status_code == 201

        restore()
        restore = use_user("delete-user-b")
        assert client.put("/api/v1/me/preferences", json=preferences_payload("사용자 B")).status_code == 200
        assert client.post("/api/v1/paper/orders", json=market_order("delete-b-0001")).status_code == 201

        restore()
        restore = use_user("delete-user-a")
        response = client.request("DELETE", "/api/v1/me", json={"confirmation": "DELETE"})
        assert response.status_code == 200
        assert response.json() == {
            "deleted": True,
            "preferences_deleted": 1,
            "paper_accounts_deleted": 1,
            "paper_orders_deleted": 1,
            "broker_orders_deleted": 0,
        }
        assert client.get("/api/v1/me/preferences").status_code == 404
        assert client.get("/api/v1/paper/orders").json() == []

        restore()
        restore = use_user("delete-user-b")
        assert client.get("/api/v1/me/preferences").json()["display_name"] == "사용자 B"
        assert len(client.get("/api/v1/paper/orders").json()) == 1
    finally:
        restore()


def test_delete_me_is_idempotent() -> None:
    restore = use_user("delete-idempotent-user")
    try:
        first = client.request("DELETE", "/api/v1/me", json={"confirmation": "DELETE"})
        second = client.request("DELETE", "/api/v1/me", json={"confirmation": "DELETE"})
    finally:
        restore()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_delete_me_is_blocked_while_broker_order_is_unresolved() -> None:
    user_id = "delete-blocked-user"
    service = BrokerOrderService()

    async def create_broker_order() -> None:
        async with async_session_factory() as session:
            await service.create_order(
                session,
                user_id,
                BrokerOrderCommand(
                    client_order_id="delete-blocked-0001",
                    symbol="QQQM",
                    side="buy",
                    order_type="market",
                    quantity=Decimal("1"),
                ),
            )

    import asyncio

    asyncio.run(create_broker_order())
    restore = use_user(user_id)
    try:
        response = client.request("DELETE", "/api/v1/me", json={"confirmation": "DELETE"})
        accounts = client.get("/api/v1/paper/accounts")
    finally:
        restore()

    assert response.status_code == 409
    assert "브로커 주문" in response.json()["detail"]
    assert accounts.status_code == 200
    assert len(accounts.json()) == 1
