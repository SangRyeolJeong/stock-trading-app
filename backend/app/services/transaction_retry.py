import asyncio
import logging
import random
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import ParamSpec, TypeVar

from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)

RETRYABLE_POSTGRESQL_STATES = {
    "40P01": "deadlock_detected",
    "40001": "serialization_failure",
}


@dataclass(frozen=True, slots=True)
class TransactionRetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.01
    max_delay_seconds: float = 0.25


@dataclass(frozen=True, slots=True)
class TransactionRetryMetricsSnapshot:
    retries_total: dict[str, int]
    exhausted_total: dict[str, int]


class TransactionRetryMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._retries: Counter[str] = Counter()
        self._exhausted: Counter[str] = Counter()

    def record_retry(self, reason: str) -> None:
        with self._lock:
            self._retries[reason] += 1

    def record_exhausted(self, reason: str) -> None:
        with self._lock:
            self._exhausted[reason] += 1

    def snapshot(self) -> TransactionRetryMetricsSnapshot:
        with self._lock:
            return TransactionRetryMetricsSnapshot(
                retries_total=dict(self._retries),
                exhausted_total=dict(self._exhausted),
            )

    def reset(self) -> None:
        with self._lock:
            self._retries.clear()
            self._exhausted.clear()


transaction_retry_metrics = TransactionRetryMetrics()


def postgresql_retry_reason(error: BaseException) -> str | None:
    if not isinstance(error, DBAPIError):
        return None
    sqlstate = getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)
    return RETRYABLE_POSTGRESQL_STATES.get(sqlstate)


async def run_with_transaction_retry(
    operation: str,
    callback: Callable[[], Awaitable[R]],
    *,
    policy: TransactionRetryPolicy,
) -> R:
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await callback()
        except DBAPIError as exc:
            reason = postgresql_retry_reason(exc)
            if reason is None:
                raise
            if attempt >= policy.max_attempts:
                transaction_retry_metrics.record_exhausted(reason)
                logger.error(
                    "transaction_retry_exhausted",
                    extra={
                        "retry_operation": operation,
                        "retry_reason": reason,
                        "retry_attempt": attempt,
                        "retry_max_attempts": policy.max_attempts,
                    },
                )
                raise

            delay_ceiling = min(
                policy.max_delay_seconds,
                policy.base_delay_seconds * (2 ** (attempt - 1)),
            )
            delay_seconds = random.uniform(0, delay_ceiling)
            transaction_retry_metrics.record_retry(reason)
            logger.warning(
                "transaction_retry_scheduled",
                extra={
                    "retry_operation": operation,
                    "retry_reason": reason,
                    "retry_attempt": attempt,
                    "retry_max_attempts": policy.max_attempts,
                    "retry_delay_seconds": delay_seconds,
                },
            )
            await asyncio.sleep(delay_seconds)

    raise AssertionError("transaction retry loop exited unexpectedly")


def retryable_transaction(
    operation: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(callback: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(callback)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            settings = get_settings()
            policy = TransactionRetryPolicy(
                max_attempts=settings.transaction_retry_max_attempts,
                base_delay_seconds=settings.transaction_retry_base_delay_seconds,
                max_delay_seconds=settings.transaction_retry_max_delay_seconds,
            )
            return await run_with_transaction_retry(
                operation,
                lambda: callback(*args, **kwargs),
                policy=policy,
            )

        return wrapped

    return decorator
