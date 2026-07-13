"""ORM models — corresponds to blueprint section 20 (Database Design), MVP subset."""

import datetime

from sqlalchemy import (
    BigInteger, String, Integer, Float, DateTime, Date, Boolean, ForeignKey, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")
    plan: Mapped[str] = mapped_column(String(16), default="free")
    plan_expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    signals_used_today: Mapped[int] = mapped_column(Integer, default=0)
    usage_reset_date: Mapped[datetime.date] = mapped_column(
        Date, default=lambda: datetime.datetime.utcnow().date()
    )

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    signal_history: Mapped[list["SignalHistory"]] = relationship(back_populates="user")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    plan: Mapped[str] = mapped_column(String(16))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="completed")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="payments")


class PromoCode(Base):
    __tablename__ = "promocodes"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    plan: Mapped[str] = mapped_column(String(16))
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class SignalHistory(Base):
    __tablename__ = "signal_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    symbol: Mapped[str] = mapped_column(String(16))
    direction: Mapped[str] = mapped_column(String(8))
    confidence: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="signal_history")
