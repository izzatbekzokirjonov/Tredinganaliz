"""
/start handleri:
- Foydalanuvchini DB ga yozadi
- Referal havola orqali kelsa mukofot beradi
- Majburiy kanallarni tekshiradi
- Asosiy menyu + Web Panel tugmasini ko'rsatadi
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS, WEB_PANEL_URL
from database import queries
from keyboards.main_menu import main_menu_keyboard
from services.channel_service import (
    check_user_membership,
    format_subscription_required,
)
from services.referral_service import build_referral_link, register_referral
from utils.helpers import tier_emoji
from utils.logger import logger

router = Router()


def _web_panel_keyboard(url: str, role: str) -> InlineKeyboardMarkup | None:
    """Web Panel tugmasi — faqat premium va admin uchun."""
    if not url:
        return None
    if role == "free":
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🌐 Web Panel", web_app={"url": url})
    ]])


@router.message(CommandStart())
async def cmd_start(message: Message, bot, pool) -> None:
    user = message.from_user
    args = message.text.split(maxsplit=1)
    ref_arg = args[1].strip() if len(args) > 1 else ""

    # Refererni aniqlash
    referrer_id = None
    if ref_arg.startswith("ref_"):
        try:
            referrer_id = int(ref_arg[4:])
            if referrer_id == user.id:
                referrer_id = None
        except ValueError:
            pass

    # Foydalanuvchini DB ga yozamiz
    await queries.create_or_update_user(
        pool,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referred_by=referrer_id,
    )

    # Referal mukofoti
    if referrer_id:
        reward_msg = await register_referral(pool, referrer_id, user.id)
        if reward_msg:
            try:
                await bot.send_message(referrer_id, reward_msg)
            except Exception as e:
                logger.warning(f"Referal xabari yuborilmadi ({referrer_id}): {e}")

    # Majburiy kanal tekshiruvi
    result = await check_user_membership(bot, pool, user.id)
    if not result.all_ok:
        msg = format_subscription_required(result.missing)
        await message.answer(msg, disable_web_page_preview=True)
        return

    # Foydalanuvchi ma'lumotlari
    db_user   = await queries.get_user(pool, user.id)
    tier      = db_user["subscription"] if db_user else "free"
    is_admin  = user.id in ADMIN_IDS
    role      = "admin" if is_admin else tier

    tier_labels = {"free": "🆓 Free", "pro": "⭐ Pro", "vip": "💎 VIP"}
    tier_label  = tier_labels.get(tier, tier)

    bot_info  = await bot.get_me()
    ref_link  = build_referral_link(bot_info.username, user.id)

    # ── Xabar matni ──
    if is_admin:
        welcome = (
            f"👑 <b>Salom, Admin!</b>\n\n"
            f"🤖 <b>Forex Analiz Bot</b> boshqaruv paneli\n\n"
            f"📊 Bot ishlayapti\n"
            f"🌐 Web panel: {WEB_PANEL_URL or 'sozlanmagan'}\n\n"
            f"Quyidagi menyudan foydalaning 👇"
        )
    elif tier in ("pro", "vip"):
        welcome = (
            f"👋 Salom, <b>{user.first_name}</b>!\n\n"
            f"💳 Tarifingiz: {tier_label}\n"
            f"🌐 Web panelga kirish uchun quyidagi tugmani bosing!\n\n"
            f"🔗 Referal: <code>{ref_link}</code>"
        )
    else:
        remaining = await queries.get_remaining_limit(pool, user.id)
        welcome = (
            f"👋 Salom, <b>{user.first_name}</b>!\n\n"
            f"📊 <b>Forex Analiz Bot</b> ga xush kelibsiz!\n\n"
            f"💳 Tarifingiz: {tier_label}\n"
            f"📋 Bugun qoldi: <b>{remaining} ta</b> tahlil\n\n"
            f"📈 Real vaqt forex/kripto tahlil\n"
            f"📸 Screenshot tahlili (AI)\n"
            f"📡 Signallar\n"
            f"🧮 Risk kalkulyator\n\n"
            f"💎 Cheksiz tahlil uchun → /premium\n"
            f"🔗 Referal: <code>{ref_link}</code>\n\n"
            f"Quyidagi menyudan foydalaning 👇"
        )

    # ── Klaviatura ──
    # Asosiy reply menyu
    await message.answer(welcome, reply_markup=main_menu_keyboard())

    # Web Panel inline tugmasi (admin va premium uchun)
    web_kb = _web_panel_keyboard(WEB_PANEL_URL, role)
    if web_kb:
        await message.answer(
            "🌐 <b>Web Panel</b> — to'liq boshqaruv paneli:",
            reply_markup=web_kb,
        )
