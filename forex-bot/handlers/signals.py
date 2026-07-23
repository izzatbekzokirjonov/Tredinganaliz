"""
Signallar handleri: admin yuborgan signallarni ko'rsatish.
"""
from aiogram import F, Router
from aiogram.types import Message

from database.queries import get_recent_signals
from services.signal_service import format_signal

router = Router()


@router.message(F.text == "📈 Signallar")
async def menu_signals(message: Message, pool) -> None:
    signals = await get_recent_signals(pool, limit=10)

    if not signals:
        await message.answer(
            "📭 Hozircha signal yo'q.\n\n"
            "📣 Signal kanalimizga a'zo bo'ling — u yerda real vaqt signallar chiqadi!"
        )
        return

    await message.answer(f"📈 <b>So'nggi {len(signals)} ta signal:</b>")
    for sig in signals:
        await message.answer(format_signal(sig))
