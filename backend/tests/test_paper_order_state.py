from unittest.mock import MagicMock

import pytest

from app.models.paper import PaperOrder
from app.services.paper_order_state import InvalidOrderStateError, transition_order


@pytest.mark.parametrize("status", ["filled", "cancelled", "rejected"])
def test_terminal_order_cannot_transition_again(status: str) -> None:
    order = PaperOrder(status=status)

    with pytest.raises(InvalidOrderStateError):
        transition_order(MagicMock(), order, "filled", reason="invalid_retry")


@pytest.mark.parametrize("status", ["filled", "cancelled", "rejected"])
def test_accepted_order_can_reach_each_terminal_state(status: str) -> None:
    session = MagicMock()
    order = PaperOrder(status="accepted")

    transition_order(session, order, status, reason="test_transition")

    event = session.add.call_args.args[0]
    assert order.status == status
    assert event.sequence == 2
    assert event.previous_status == "accepted"
    assert event.new_status == status
