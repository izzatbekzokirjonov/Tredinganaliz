"""
Forex Analiz Bot V1 — asosiy kirish nuqtasi.

Ishga tushirish:
    python app.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DATABASE_URL
from database.db import close_pool, create_pool, init_db
from handlers import admin, admin_user, analysis, calculator, channels, premium, profile, signals, start
from middlewares.auth import AuthMiddleware
from middlewares.subscription import SubscriptionMiddleware
from utils.logger import logger


# ── Pool ni middleware va handler larga uzatish ──────────────────

class PoolMiddleware:
    """asyncpg pool ni data dict ga qo'shadi."""

    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler, event, data):
        data["pool"] = self.pool
        return await handler(event, data)


# ── Bot va Dispatcher ────────────────────────────────────────────

async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env faylida topilmadi!")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Pool yaratish
    pool = await create_pool(DATABASE_URL)
    await init_db(pool)

    # Middleware lar (tartib muhim!)
    pool_mw = PoolMiddleware(pool)

    # Message middleware lar
    dp.message.outer_middleware(pool_mw)
    dp.callback_query.outer_middleware(pool_mw)

    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Router lar ro'yxatga olish
    dp.include_router(start.router)
    dp.include_router(analysis.router)
    dp.include_router(signals.router)
    dp.include_router(calculator.router)
    dp.include_router(profile.router)
    dp.include_router(premium.router)
    dp.include_router(channels.router)
    dp.include_router(admin_user.router)
    dp.include_router(admin.router)

    logger.info("Bot ishga tushirilmoqda...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await close_pool(pool)
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
