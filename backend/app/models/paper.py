from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

MONEY = Numeric(28, 8)
QUANTITY = Numeric(28, 8)


class PaperAccount(Base):
    __tablename__ = "paper_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_paper_accounts_user_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(100))
    base_currency: Mapped[str] = mapped_column(String(3), default="KRW")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Security(Base):
    __tablename__ = "securities"

    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(3))
    market: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaperOrder(Base):
    __tablename__ = "paper_orders"
    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_paper_orders_account_id_idempotency_key"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_paper_orders_account_created", "account_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    security_symbol: Mapped[str] = mapped_column(ForeignKey("securities.symbol"))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    side: Mapped[str] = mapped_column(String(4))
    order_type: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[Decimal] = mapped_column(QUANTITY)
    requested_price: Mapped[Decimal | None] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(20), default="filled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperExecution(Base):
    __tablename__ = "paper_executions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("price > 0", name="price_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("paper_orders.id"), unique=True)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY)
    price: Mapped[Decimal] = mapped_column(MONEY)
    gross_amount: Mapped[Decimal] = mapped_column(MONEY)
    fee: Mapped[Decimal] = mapped_column(MONEY)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CashLedgerEntry(Base):
    __tablename__ = "cash_ledger_entries"
    __table_args__ = (Index("ix_cash_ledger_account_currency_created", "account_id", "currency", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("paper_orders.id"))
    currency: Mapped[str] = mapped_column(String(3))
    entry_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    balance_after: Mapped[Decimal] = mapped_column(MONEY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("account_id", "security_symbol", name="uq_positions_account_id_security_symbol"),
        CheckConstraint("quantity >= 0", name="quantity_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    security_symbol: Mapped[str] = mapped_column(ForeignKey("securities.symbol"))
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, default=Decimal("0"))
    average_cost: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (Index("ix_portfolio_snapshots_account_created", "account_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    cash_value: Mapped[Decimal] = mapped_column(MONEY)
    positions_value: Mapped[Decimal] = mapped_column(MONEY)
    total_value: Mapped[Decimal] = mapped_column(MONEY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
