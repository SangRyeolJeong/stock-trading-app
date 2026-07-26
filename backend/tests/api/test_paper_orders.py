from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def base_order() -> dict[str, object]:
    return {
        "symbol": "QQQM",
        "side": "buy",
        "order_type": "market",
        "quantity": 1,
        "idempotency_key": "test-order-0001",
    }


def test_zero_quantity_is_rejected() -> None:
    payload = base_order()
    payload["quantity"] = 0

    response = client.post("/api/v1/paper/orders", json=payload)

    assert response.status_code == 422


def test_limit_order_without_price_is_rejected() -> None:
    payload = base_order()
    payload["order_type"] = "limit"

    response = client.post("/api/v1/paper/orders", json=payload)

    assert response.status_code == 422


def test_accounts_start_with_krw_and_usd_cash() -> None:
    response = client.get("/api/v1/paper/accounts")

    assert response.status_code == 200
    account = response.json()[0]
    assert account["id"] == "demo-account"
    assert {item["currency"]: item["amount"] for item in account["cash_balances"]} == {
        "KRW": "10000000.00000000",
        "USD": "10000.00000000",
    }


def test_buy_is_rejected_when_cash_is_insufficient() -> None:
    payload = base_order()
    payload["quantity"] = 100_000

    response = client.post("/api/v1/paper/orders", json=payload)

    assert response.status_code == 422
    assert "현금이 부족" in response.json()["detail"]


def test_sell_is_rejected_when_quantity_exceeds_position() -> None:
    payload = base_order()
    payload.update({"side": "sell", "quantity": 1})

    response = client.post("/api/v1/paper/orders", json=payload)

    assert response.status_code == 422
    assert "보유 수량이 부족" in response.json()["detail"]


def test_weighted_average_cost_and_average_is_unchanged_after_sell() -> None:
    first = base_order()
    first.update({"quantity": 2, "order_type": "limit", "limit_price": "200"})
    second = base_order()
    second.update(
        {
            "quantity": 2,
            "order_type": "limit",
            "limit_price": "240",
            "idempotency_key": "test-order-0002",
        }
    )
    sell = base_order()
    sell.update(
        {
            "side": "sell",
            "quantity": 1,
            "order_type": "limit",
            "limit_price": "250",
            "idempotency_key": "test-order-0003",
        }
    )

    assert client.post("/api/v1/paper/orders", json=first).status_code == 201
    assert client.post("/api/v1/paper/orders", json=second).status_code == 201
    before_sell = client.get("/api/v1/paper/positions").json()[0]
    sell_response = client.post("/api/v1/paper/orders", json=sell)
    after_sell = client.get("/api/v1/paper/positions").json()[0]

    assert before_sell["average_cost"] == "220.00000000"
    assert sell_response.status_code == 201
    assert after_sell["quantity"] == "3.00000000"
    assert after_sell["average_cost"] == before_sell["average_cost"]
    assert sell_response.json()["realized_pnl"] == "29.75000000"


def test_idempotency_key_does_not_duplicate_order_or_ledger_effects() -> None:
    payload = base_order()

    first = client.post("/api/v1/paper/orders", json=payload)
    cash_after_first = client.get("/api/v1/paper/accounts").json()[0]["cash_balances"]
    second = client.post("/api/v1/paper/orders", json=payload)
    cash_after_second = client.get("/api/v1/paper/accounts").json()[0]["cash_balances"]
    orders = client.get("/api/v1/paper/orders").json()
    positions = client.get("/api/v1/paper/positions").json()

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert cash_after_first == cash_after_second
    assert len(orders) == 1
    assert positions[0]["quantity"] == "1.00000000"


def test_reusing_idempotency_key_for_different_order_is_rejected() -> None:
    first = base_order()
    changed = base_order()
    changed["quantity"] = 2

    assert client.post("/api/v1/paper/orders", json=first).status_code == 201
    response = client.post("/api/v1/paper/orders", json=changed)

    assert response.status_code == 409


def test_portfolio_summary_uses_ledger_positions_and_cash() -> None:
    payload = base_order()
    payload.update({"quantity": 2, "order_type": "limit", "limit_price": "200"})
    assert client.post("/api/v1/paper/orders", json=payload).status_code == 201

    response = client.get("/api/v1/portfolios/summary")

    assert response.status_code == 200
    summary = response.json()
    usd = next(item for item in summary["currencies"] if item["currency"] == "USD")
    assert summary["positions"][0]["symbol"] == "QQQM"
    assert summary["positions"][0]["quantity"] == "2.00000000"
    assert usd["cash"] == "9599.60000000"
    assert usd["positions_value"] == "463.44000000"
