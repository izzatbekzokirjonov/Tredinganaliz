"""
Majburiy kanal obuna middleware.

Har bir xabar/callback kelganda:
1. Foydalanuvchi ban listida emasligini tekshiradi.
2. Barcha majburiy kanallarga a'zoligini tekshiradi.
3. A'zo bo'lmasa — xabar yuborib, so'rovni to'xtatadi.

Adminlar va /start buyrug'i doimo o'tib ketadi.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import ADMIN_IDS
from database import queries
from services.channel_service import (
    check_user_membership,
    format_subscription_required,
)


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Foydalanuvchi va bot obyektlarini olamiz
        if isinstance(event, Message):
            user = event.from_user
            reply = event.answer
            text = event.text or ""
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            reply = event.message.answer
            text = ""
        else:
            return await handler(event, data)

        if user is None:
            return await handler(event, data)

        # Adminlar tekshirishdan o'tib ketadi
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        # /start har doim o'tadi (kanal tugmasidan keyin foydalanuvchi qaytadi)
        if text.startswith("/start"):
            return await handler(event, data)

        pool = data.get("pool")
        bot = data.get("bot")
        if pool is None or bot is None:
            return await handler(event, data)

        # Ban tekshiruvi
        db_user = await queries.get_user(pool, user.id)
        if db_user and db_user["is_banned"]:
            await reply("🚫 Siz botdan bloklangansiz.")
            return

        # Majburiy kanal tekshiruvi
        result = await check_user_membership(bot, pool, user.id)
        if not result.all_ok:
            msg = format_subscription_required(result.missing)
            await reply(msg, disable_web_page_preview=True)
            return

        return await handler(event, data)
