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
