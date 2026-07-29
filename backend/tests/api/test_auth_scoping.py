from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

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


def market_order(idempotency_key: str) -> dict[str, object]:
    return {
        "symbol": "QQQM",
        "side": "buy",
        "order_type": "market",
        "quantity": 1,
        "idempotency_key": idempotency_key,
    }


def test_users_have_isolated_accounts_orders_and_positions() -> None:
    restore = use_user("user-a")
    try:
        account_a = client.get("/api/v1/paper/accounts").json()[0]
        order_a = client.post(
            "/api/v1/paper/orders",
            json=market_order("user-a-order-0001"),
        )
        assert order_a.status_code == 201
        assert order_a.json()["account_id"] == account_a["id"]
        assert len(client.get("/api/v1/paper/positions").json()) == 1

        restore()
        restore = use_user("user-b")
        account_b = client.get("/api/v1/paper/accounts").json()[0]
        assert account_b["id"] != account_a["id"]
        assert client.get("/api/v1/paper/orders").json() == []
        assert client.get("/api/v1/paper/positions").json() == []

        restore()
        restore = use_user("user-a")
        assert len(client.get("/api/v1/paper/orders").json()) == 1
        assert len(client.get("/api/v1/paper/positions").json()) == 1
    finally:
        restore()


def test_order_request_rejects_client_selected_account() -> None:
    payload = market_order("account-injection-0001")
    payload["account_id"] = "another-users-account"

    response = client.post("/api/v1/paper/orders", json=payload)

    assert response.status_code == 422


def test_concurrent_first_requests_create_one_initial_ledger() -> None:
    restore = use_user("concurrent-user")
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(
                executor.map(
                    lambda _index: client.get("/api/v1/paper/accounts"),
                    range(2),
                )
            )

        assert all(response.status_code == 200 for response in responses)
        accounts = [response.json()[0] for response in responses]
        assert accounts[0]["id"] == accounts[1]["id"]
        assert {
            item["currency"]: item["amount"]
            for item in accounts[0]["cash_balances"]
        } == {
            "KRW": "10000000.00000000",
            "USD": "10000.00000000",
        }
    finally:
        restore()
