from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BrokerOrder(Base):
    __tablename__ = "broker_orders"
    __table_args__ = (
        UniqueConstraint("account_id", "client_order_id", name="uq_broker_orders_account_client_order"),
        CheckConstraint("side IN ('buy', 'sell')", name="side_valid"),
        CheckConstraint("order_type IN ('market', 'limit')", name="order_type_valid"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "status IN ('pending_submission', 'submitted', 'cancel_pending', "
            "'cancelled', 'reconciliation_required')",
            name="status_valid",
        ),
        Index("ix_broker_orders_account_created", "account_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    client_order_id: Mapped[str] = mapped_column(String(128))
    broker_order_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[str] = mapped_column(String(4))
    order_type: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8))
    status: Mapped[str] = mapped_column(String(30), default="pending_submission")
    last_error: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BrokerOutboxEvent(Base):
    __tablename__ = "broker_outbox_events"
    __table_args__ = (
        CheckConstraint("event_type IN ('submit_order', 'cancel_order')", name="event_type_valid"),
        CheckConstraint("status IN ('pending', 'processed', 'failed')", name="status_valid"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_nonnegative"),
        Index("ix_broker_outbox_due", "status", "next_attempt_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("broker_orders.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempt_count: Mapped[int] = mapped_column(default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_error: Mapped[str | None] = mapped_column(String(200))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
