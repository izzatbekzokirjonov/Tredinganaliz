"""
Auth middleware: foydalanuvchi ban holatini tekshiradi.
SubscriptionMiddleware bilan birga ishlatiladi.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import ADMIN_IDS
from database import queries


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if user is None or user.id in ADMIN_IDS:
            return await handler(event, data)

        pool = data.get("pool")
        if pool is None:
            return await handler(event, data)

        db_user = await queries.get_user(pool, user.id)
        if db_user and db_user["is_banned"]:
            await event.answer("🚫 Siz botdan bloklangansiz. Admin bilan bog'laning.")
            return

        return await handler(event, data)
