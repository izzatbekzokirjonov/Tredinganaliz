import asyncio
from aiogram import Bot
from database import queries
from utils.logger import logger


def format_signal(signal) -> str:
    emoji = "🟢" if signal["direction"].upper() == "BUY" else "🔴"
    text = (
        f"{emoji} <b>{signal['pair']}</b> — {signal['direction'].upper()}\n\n"
        f"📍 Entry: <code>{signal['entry']}</code>\n"
        f"🎯 TP:    <code>{signal['tp']}</code>\n"
        f"🛑 SL:    <code>{signal['sl']}</code>\n"
    )
    if signal["comment"]:
        text += f"\n💬 {signal['comment']}"
    return text


async def broadcast_signal(bot: Bot, pool, signal) -> tuple[int, int]:
    text = "🆕 <b>Yangi signal!</b>\n\n" + format_signal(signal)
    user_ids = await queries.get_all_telegram_ids(pool)
    sent = failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Signal yuborilmadi ({uid}): {e}")
        await asyncio.sleep(0.05)
    return sent, failed
