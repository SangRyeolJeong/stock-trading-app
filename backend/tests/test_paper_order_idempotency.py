from decimal import Decimal

from app.schemas.paper import PaperOrderRequest
from app.services.paper_trading import order_request_fingerprint


def request(*, quantity: str = "1", limit_price: str | None = None) -> PaperOrderRequest:
    return PaperOrderRequest(
        symbol=" qqqm ",
        side="buy",
        order_type="limit" if limit_price is not None else "market",
        quantity=Decimal(quantity),
        limit_price=Decimal(limit_price) if limit_price is not None else None,
        idempotency_key="fingerprint-test-0001",
    )


def test_order_fingerprint_normalizes_symbol_and_decimal_storage_values() -> None:
    left = request(quantity="1.0", limit_price="200")
    right = request(quantity="1.000000000", limit_price="200.000000000")

    assert order_request_fingerprint(left) == order_request_fingerprint(right)
    assert len(order_request_fingerprint(left)) == 64


def test_order_fingerprint_changes_with_request_content_but_not_idempotency_key() -> None:
    original = request(quantity="1")
    different_quantity = request(quantity="2")
    different_key = original.model_copy(update={"idempotency_key": "fingerprint-test-0002"})

    assert order_request_fingerprint(original) != order_request_fingerprint(different_quantity)
    assert order_request_fingerprint(original) == order_request_fingerprint(different_key)
