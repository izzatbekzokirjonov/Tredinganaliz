"""
Bot va Web panelni bir vaqtda ishga tushirish.

    python run.py

Bot: polling rejimida
Web: http://0.0.0.0:8000
"""
import asyncio
import threading

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DATABASE_URL
from database.db import close_pool, create_pool, init_db
from handlers import (
    admin, admin_user, analysis,
    calculator, channels, premium,
    profile, signals, start,
)
from middlewares.auth import AuthMiddleware
from middlewares.subscription import SubscriptionMiddleware
from utils.logger import logger
from web.main import app as web_app


class PoolMiddleware:
    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler, event, data):
        data["pool"] = self.pool
        return await handler(event, data)


# ─── BOT ──────────────────────────────────────────────────────────

async def run_bot(pool, bot):
    dp = Dispatcher(storage=MemoryStorage())

    pool_mw = PoolMiddleware(pool)
    dp.message.outer_middleware(pool_mw)
    dp.callback_query.outer_middleware(pool_mw)
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(start.router)
    dp.include_router(analysis.router)
    dp.include_router(signals.router)
    dp.include_router(calculator.router)
    dp.include_router(profile.router)
    dp.include_router(premium.router)
    dp.include_router(channels.router)
    dp.include_router(admin_user.router)
    dp.include_router(admin.router)

    logger.info("Bot polling boshlandi...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


# ─── WEB ─────────────────────────────────────────────────────────

def run_web():
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


# ─── MAIN ─────────────────────────────────────────────────────────

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env da topilmadi!")

    bot  = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    pool = await create_pool(DATABASE_URL)
    await init_db(pool)

    # Web panel uchun pool va bot ni ulash
    web_app.state.pool = pool
    web_app.state.bot  = bot

    # Web ni alohida threadda ishga tushiramiz
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("Web panel: http://0.0.0.0:8000")

    try:
        await run_bot(pool, bot)
    finally:
        await close_pool(pool)
        await bot.session.close()
        logger.info("Hammasi to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
