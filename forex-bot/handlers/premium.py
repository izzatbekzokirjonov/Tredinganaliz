"""
Premium handleri: tariflarni ko'rsatish.
"""
from aiogram import F, Router
from aiogram.types import Message

from database import queries
from keyboards.premium_menu import premium_info_keyboard
from utils.helpers import format_datetime, tier_emoji

router = Router()

PREMIUM_TEXT = """
💎 <b>Premium tariflar</b>

┌─────────────────────────
│ 🆓 <b>Free</b> — Bepul
│ • Kuniga 5 ta tahlil
│ • Signallar ko'rish
│ • Risk kalkulyator
└─────────────────────────

┌─────────────────────────
│ ⭐ <b>Pro</b> — $9.99/oy
│ • Kuniga 50 ta tahlil
│ • AI izohi (batafsil)
│ • Barcha juftliklar
│ • Referal mukofotlari
└─────────────────────────

┌─────────────────────────
│ 💎 <b>VIP</b> — $24.99/oy
│ • ♾️ Cheksiz tahlil
│ • AI Premium sifati
│ • Maxsus signallar
│ • Ustuvor qo'llab-quvvatlash
└─────────────────────────

📞 Premium olish uchun admin bilan bog'laning.
"""


@router.message(F.text == "💎 Premium")
async def menu_premium(message: Message, pool) -> None:
    db_user = await queries.get_user(pool, message.from_user.id)
    tier = db_user["subscription"] if db_user else "free"
    expires = format_datetime(db_user["subscription_expires_at"]) if db_user else "—"

    status_line = (
        f"\n✅ <b>Hozirgi tarifingiz:</b> {tier_emoji(tier)} {tier.upper()}"
        + (f"\n📅 Tugash sanasi: {expires}" if tier != "free" else "")
        + "\n"
    )

    await message.answer(
        status_line + PREMIUM_TEXT,
        reply_markup=premium_info_keyboard(),
    )
