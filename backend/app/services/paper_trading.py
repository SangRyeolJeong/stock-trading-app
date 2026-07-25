from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.market import Quote
from app.schemas.paper import PaperOrder, PaperOrderRequest


class PaperTradingService:
    """Temporary immediate-fill service.

    A transactional cash and position ledger replaces this service in Phase 5.
    """

    def execute_immediately(self, order: PaperOrderRequest, quote: Quote) -> PaperOrder:
        fill_price = order.limit_price if order.order_type == "limit" else quote.price
        assert fill_price is not None
        return PaperOrder(
            id=uuid4(),
            idempotency_key=order.idempotency_key,
            status="filled",
            symbol=quote.symbol,
            side=order.side,
            quantity=order.quantity,
            filled_price=fill_price,
            created_at=datetime.now(UTC),
        )


paper_trading_service = PaperTradingService()
