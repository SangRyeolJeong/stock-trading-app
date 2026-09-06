import logging
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import OperationalError

from app.services.paper_trading import InsufficientCashError
from app.services.transaction_retry import (
    TransactionRetryPolicy,
    run_with_transaction_retry,
    transaction_retry_metrics,
)
from app.services.transaction_retry import (
    logger as retry_logger,
)


class PostgreSQLDriverError(RuntimeError):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(sqlstate)
        self.sqlstate = sqlstate


def database_error(sqlstate: str) -> OperationalError:
    return OperationalError("statement", {}, PostgreSQLDriverError(sqlstate))


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    transaction_retry_metrics.reset()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sqlstate", "reason"),
    [("40P01", "deadlock_detected"), ("40001", "serialization_failure")],
)
async def test_retryable_postgresql_transaction_error_is_retried(
    sqlstate: str,
    reason: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(retry_logger, "disabled", False)
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.transaction_retry.asyncio.sleep", sleep)
    monkeypatch.setattr("app.services.transaction_retry.random.uniform", lambda _start, end: end)
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise database_error(sqlstate)
        return "committed"

    with caplog.at_level(logging.WARNING, logger=retry_logger.name):
        result = await run_with_transaction_retry(
            "test_order",
            operation,
            policy=TransactionRetryPolicy(
                max_attempts=3,
                base_delay_seconds=0.01,
                max_delay_seconds=0.1,
            ),
        )

    assert result == "committed"
    assert attempts == 3
    assert [call.args[0] for call in sleep.await_args_list] == [0.01, 0.02]
    assert transaction_retry_metrics.snapshot().retries_total == {reason: 2}
    assert [record.retry_reason for record in caplog.records] == [reason, reason]
    assert [record.retry_attempt for record in caplog.records] == [1, 2]


@pytest.mark.asyncio
async def test_retry_stops_at_attempt_limit_and_records_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.transaction_retry.asyncio.sleep", AsyncMock())
    attempts = 0

    async def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise database_error("40P01")

    with pytest.raises(OperationalError):
        await run_with_transaction_retry(
            "test_order",
            operation,
            policy=TransactionRetryPolicy(max_attempts=2, base_delay_seconds=0),
        )

    snapshot = transaction_retry_metrics.snapshot()
    assert attempts == 2
    assert snapshot.retries_total == {"deadlock_detected": 1}
    assert snapshot.exhausted_total == {"deadlock_detected": 1}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [database_error("08006"), InsufficientCashError("insufficient cash")],
)
async def test_non_retryable_errors_are_returned_immediately(error: Exception) -> None:
    attempts = 0

    async def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise error

    with pytest.raises(type(error)):
        await run_with_transaction_retry(
            "test_order",
            operation,
            policy=TransactionRetryPolicy(max_attempts=3, base_delay_seconds=0),
        )

    assert attempts == 1
    assert transaction_retry_metrics.snapshot().retries_total == {}
