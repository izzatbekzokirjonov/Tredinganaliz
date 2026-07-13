"""Subscription plan logic: daily limits, plan activation, promo codes."""

import datetime

from config import PLAN_LIMITS
from db.database import async_session
from db.models import User, PromoCode, Payment


async def get_or_create_user(telegram_id: int, username: str | None) -> User:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user is None:
            user = User(id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


def _reset_if_new_day(user: User) -> None:
    today = datetime.datetime.utcnow().date()
    if user.usage_reset_date != today:
        user.usage_reset_date = today
        user.signals_used_today = 0


def _plan_active(user: User) -> str:
    """Returns the effective plan, downgrading to 'free' if expired."""
    if user.plan != "free" and user.plan_expires_at:
        if user.plan_expires_at < datetime.datetime.utcnow():
            return "free"
    return user.plan


async def check_and_consume_quota(telegram_id: int) -> tuple[bool, str, int, int]:
    """
    Checks whether the user still has signal quota left today, and if so,
    consumes one unit. Returns (allowed, effective_plan, used, limit).
    """
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user is None:
            return False, "free", 0, PLAN_LIMITS["free"]

        _reset_if_new_day(user)
        effective_plan = _plan_active(user)
        if effective_plan != user.plan:
            user.plan = effective_plan
            user.plan_expires_at = None

        limit = PLAN_LIMITS.get(effective_plan, PLAN_LIMITS["free"])

        if user.signals_used_today >= limit:
            await session.commit()
            return False, effective_plan, user.signals_used_today, limit

        user.signals_used_today += 1
        await session.commit()
        return True, effective_plan, user.signals_used_today, limit


async def activate_plan(telegram_id: int, plan: str, days: int) -> None:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user is None:
            return
        now = datetime.datetime.utcnow()
        base = user.plan_expires_at if (user.plan_expires_at and user.plan_expires_at > now) else now
        user.plan = plan
        user.plan_expires_at = base + datetime.timedelta(days=days)
        await session.commit()


async def record_payment(telegram_id: int, plan: str, amount: float, currency: str,
                          provider_payment_id: str | None) -> None:
    async with async_session() as session:
        payment = Payment(
            user_id=telegram_id, plan=plan, amount=amount,
            currency=currency, provider_payment_id=provider_payment_id,
            status="completed",
        )
        session.add(payment)
        await session.commit()


async def redeem_promocode(telegram_id: int, code: str) -> tuple[bool, str]:
    async with async_session() as session:
        promo = await session.get(PromoCode, code.strip().upper())
        if promo is None or not promo.active:
            return False, "Promo kod topilmadi yoki faol emas."
        if promo.used_count >= promo.max_uses:
            return False, "Promo kod limiti tugagan."

        promo.used_count += 1
        await session.commit()

    await activate_plan(telegram_id, promo.plan, promo.duration_days)
    return True, f"'{promo.plan}' rejasi {promo.duration_days} kunga faollashtirildi!"
