from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.market import Quote
from app.services.market import market_data_service

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


@pytest.mark.parametrize("symbol", ["DGRO", "SGOV"])
def test_rebalancing_example_etfs_can_be_bought(symbol: str) -> None:
    payload = base_order()
    payload.update(
        {
            "symbol": symbol,
            "idempotency_key": f"test-rebalancing-{symbol.lower()}",
        }
    )

    response = client.post("/api/v1/paper/orders", json=payload)
    positions = client.get("/api/v1/paper/positions").json()

    assert response.status_code == 201
    assert response.json()["status"] == "filled"
    assert positions[0]["symbol"] == symbol


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


def test_weighted_average_cost_and_average_is_unchanged_after_sell(monkeypatch) -> None:
    prices = iter((Decimal("200"), Decimal("240"), Decimal("250")))

    async def changing_quote(symbol: str) -> Quote:
        price = next(prices)
        return Quote(
            symbol=symbol,
            name="인베스코 나스닥 100 ETF",
            currency="USD",
            price=price,
            change=Decimal("0"),
            change_rate=Decimal("0"),
            market_open=True,
            as_of=datetime.now(UTC),
        )

    monkeypatch.setattr(market_data_service, "get_quote", changing_quote)
    first = base_order()
    first.update({"quantity": 2})
    second = base_order()
    second.update(
        {
            "quantity": 2,
            "idempotency_key": "test-order-0002",
        }
    )
    sell = base_order()
    sell.update(
        {
            "side": "sell",
            "quantity": 1,
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


def test_unmarketable_limit_order_waits_without_changing_cash_or_positions() -> None:
    payload = base_order()
    payload.update({"order_type": "limit", "limit_price": "200"})

    before_cash = client.get("/api/v1/paper/accounts").json()[0]["cash_balances"]
    response = client.post("/api/v1/paper/orders", json=payload)
    after_cash = client.get("/api/v1/paper/accounts").json()[0]["cash_balances"]

    assert response.status_code == 201
    assert response.json()["status"] == "accepted"
    assert response.json()["limit_price"] == "200.00000000"
    assert response.json()["filled_price"] is None
    assert before_cash == after_cash
    assert client.get("/api/v1/paper/positions").json() == []


def test_pending_limit_order_fills_when_market_reaches_limit(monkeypatch) -> None:
    payload = base_order()
    payload.update({"order_type": "limit", "limit_price": "200"})
    assert client.post("/api/v1/paper/orders", json=payload).json()["status"] == "accepted"

    async def reached_quote(symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            name="인베스코 나스닥 100 ETF",
            currency="USD",
            price=Decimal("199"),
            change=Decimal("0"),
            change_rate=Decimal("0"),
            market_open=True,
            as_of=datetime.now(UTC),
        )

    monkeypatch.setattr(market_data_service, "get_quote", reached_quote)
    order = client.get("/api/v1/paper/orders").json()[0]

    assert order["status"] == "filled"
    assert order["filled_price"] == "199.00000000"
    assert client.get("/api/v1/paper/positions").json()[0]["quantity"] == "1.00000000"


def test_pending_limit_order_can_be_cancelled() -> None:
    payload = base_order()
    payload.update({"order_type": "limit", "limit_price": "200"})
    order = client.post("/api/v1/paper/orders", json=payload).json()

    response = client.delete(f"/api/v1/paper/orders/{order['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get("/api/v1/paper/orders").json()[0]["status"] == "cancelled"

    repeated = client.delete(f"/api/v1/paper/orders/{order['id']}")
    events = client.get(f"/api/v1/paper/orders/{order['id']}/events").json()

    assert repeated.status_code == 200
    assert repeated.json()["status"] == "cancelled"
    assert [(event["previous_status"], event["new_status"]) for event in events] == [
        (None, "accepted"),
        ("accepted", "cancelled"),
    ]
    assert [event["reason"] for event in events] == ["order_created", "user_cancelled"]


def test_filled_order_has_auditable_history_and_cannot_be_cancelled() -> None:
    order = client.post("/api/v1/paper/orders", json=base_order()).json()

    cancel = client.delete(f"/api/v1/paper/orders/{order['id']}")
    events = client.get(f"/api/v1/paper/orders/{order['id']}/events")

    assert cancel.status_code == 409
    assert events.status_code == 200
    assert [(event["sequence"], event["new_status"]) for event in events.json()] == [
        (1, "accepted"),
        (2, "filled"),
    ]


def test_order_history_is_scoped_to_current_users_orders() -> None:
    response = client.get("/api/v1/paper/orders/11111111-1111-1111-1111-111111111111/events")

    assert response.status_code == 404


def test_pending_buy_reserves_cash_until_cancelled() -> None:
    pending = base_order()
    pending.update({"order_type": "limit", "limit_price": "200", "quantity": 40})
    accepted = client.post("/api/v1/paper/orders", json=pending).json()
    assert accepted["status"] == "accepted"

    market = base_order()
    market.update({"quantity": 9, "idempotency_key": "test-order-market-after-reserve"})
    blocked = client.post("/api/v1/paper/orders", json=market)
    assert blocked.status_code == 422
    assert "가용" in blocked.json()["detail"]

    assert client.delete(f"/api/v1/paper/orders/{accepted['id']}").status_code == 200
    assert client.post("/api/v1/paper/orders", json=market).status_code == 201


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


def test_completed_order_retry_does_not_call_unavailable_market_data(monkeypatch) -> None:
    payload = base_order()
    first = client.post("/api/v1/paper/orders", json=payload)

    async def unavailable_quote(symbol: str) -> Quote:
        raise AssertionError(f"완료 주문 재조회에서 시세를 호출했습니다: {symbol}")

    monkeypatch.setattr(market_data_service, "get_quote", unavailable_quote)
    retried = client.post("/api/v1/paper/orders", json=payload)

    assert first.status_code == retried.status_code == 201
    assert retried.json() == first.json()


def test_idempotency_conflict_is_returned_before_market_data_call(monkeypatch) -> None:
    original = base_order()
    changed = base_order()
    changed["quantity"] = 2
    assert client.post("/api/v1/paper/orders", json=original).status_code == 201

    async def unavailable_quote(symbol: str) -> Quote:
        raise AssertionError(f"멱등성 충돌에서 시세를 호출했습니다: {symbol}")

    monkeypatch.setattr(market_data_service, "get_quote", unavailable_quote)
    response = client.post("/api/v1/paper/orders", json=changed)

    assert response.status_code == 409
    assert "다른 주문" in response.json()["detail"]


def test_reusing_idempotency_key_for_different_order_is_rejected() -> None:
    first = base_order()
    changed = base_order()
    changed["quantity"] = 2

    assert client.post("/api/v1/paper/orders", json=first).status_code == 201
    response = client.post("/api/v1/paper/orders", json=changed)

    assert response.status_code == 409


def test_portfolio_summary_uses_ledger_positions_and_cash() -> None:
    payload = base_order()
    payload.update({"quantity": 2})
    assert client.post("/api/v1/paper/orders", json=payload).status_code == 201

    response = client.get("/api/v1/portfolios/summary")

    assert response.status_code == 200
    summary = response.json()
    usd = next(item for item in summary["currencies"] if item["currency"] == "USD")
    assert summary["positions"][0]["symbol"] == "QQQM"
    assert summary["positions"][0]["quantity"] == "2.00000000"
    assert usd["cash"] == "9536.09656000"
    assert usd["positions_value"] == "463.44000000"
