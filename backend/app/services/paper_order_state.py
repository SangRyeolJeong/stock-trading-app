from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import PaperOrder, PaperOrderStatusEvent

OrderStatus = Literal["accepted", "filled", "cancelled", "rejected"]
TERMINAL_ORDER_STATUSES = frozenset({"filled", "cancelled", "rejected"})
ALLOWED_ORDER_TRANSITIONS: dict[str, frozenset[str]] = {
    "accepted": TERMINAL_ORDER_STATUSES,
    "filled": frozenset(),
    "cancelled": frozenset(),
    "rejected": frozenset(),
}


class InvalidOrderStateError(RuntimeError):
    status_code = 409


def record_order_creation(
    session: AsyncSession,
    order: PaperOrder,
    *,
    reason: str = "order_created",
) -> None:
    if order.status != "accepted":
        raise InvalidOrderStateError("주문은 accepted 상태로만 생성할 수 있습니다.")
    session.add(
        PaperOrderStatusEvent(
            order_id=order.id,
            sequence=1,
            previous_status=None,
            new_status="accepted",
            reason=reason,
        )
    )


def transition_order(
    session: AsyncSession,
    order: PaperOrder,
    new_status: OrderStatus,
    *,
    reason: str,
) -> None:
    previous_status = order.status
    if new_status not in ALLOWED_ORDER_TRANSITIONS.get(previous_status, frozenset()):
        raise InvalidOrderStateError(
            f"허용되지 않은 주문 상태 전이입니다: {previous_status} -> {new_status}"
        )
    order.status = new_status
    session.add(
        PaperOrderStatusEvent(
            order_id=order.id,
            sequence=2,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
        )
    )
