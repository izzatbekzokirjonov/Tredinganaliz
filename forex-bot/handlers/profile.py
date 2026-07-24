"""
Profil handleri: foydalanuvchi ma'lumotlari, referal havola, tahlil tarixi.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import queries
from keyboards.profile_menu import profile_inline_keyboard
from services.referral_service import build_referral_link
from utils.helpers import format_datetime, tier_emoji

router = Router()


@router.message(F.text == "👤 Profil")
async def menu_profile(message: Message, bot, pool) -> None:
    user = message.from_user
    db_user = await queries.get_user(pool, user.id)

    if not db_user:
        await message.answer("❌ Profil topilmadi. /start ni bosing.")
        return

    tier = db_user["subscription"]
    expires = format_datetime(db_user["subscription_expires_at"])
    total = await queries.count_analysis_total_by_user(pool, user.id)
    remaining = await queries.get_remaining_limit(pool, user.id)
    limit_txt = "♾️ Cheksiz" if remaining is None else f"{remaining} ta"

    bot_info = await bot.get_me()
    ref_link = build_referral_link(bot_info.username, user.id)

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: {user.first_name or '—'}\n"
        f"🔗 Username: {'@' + user.username if user.username else '—'}\n\n"
        f"💳 Tarif: {tier_emoji(tier)} <b>{tier.upper()}</b>\n"
        f"📅 Tugash sanasi: {expires}\n\n"
        f"📊 Jami tahlillar: <b>{total}</b>\n"
        f"📋 Bugun qoldi: <b>{limit_txt}</b>\n"
        f"👥 Referallar: <b>{db_user['referrals']}</b>\n\n"
        f"🔗 Referal havola:\n<code>{ref_link}</code>"
    )

    bot_info = await bot.get_me()
    await message.answer(
        text,
        reply_markup=profile_inline_keyboard(bot_info.username, user.id),
    )


@router.callback_query(F.data == "profile:referral")
async def cb_referral(callback: CallbackQuery, bot, pool) -> None:
    bot_info = await bot.get_me()
    ref_link = build_referral_link(bot_info.username, callback.from_user.id)
    count = await queries.get_referral_count(pool, callback.from_user.id)

    text = (
        f"🔗 <b>Referal tizimi</b>\n\n"
        f"Havola: <code>{ref_link}</code>\n\n"
        f"👥 Taklif qilganlaringiz: <b>{count}</b>\n\n"
        f"🎁 <b>Mukofotlar:</b>\n"
        f"• 3 ta referal → 1 kunlik Pro\n"
        f"• 10 ta referal → 7 kunlik Pro"
    )
    await callback.answer()
    await callback.message.answer(text)


@router.callback_query(F.data == "profile:history")
async def cb_history(callback: CallbackQuery, pool) -> None:
    total = await queries.count_analysis_total_by_user(pool, callback.from_user.id)
    remaining = await queries.get_remaining_limit(pool, callback.from_user.id)
    limit_txt = "♾️ Cheksiz" if remaining is None else str(remaining)

    await callback.answer()
    await callback.message.answer(
        f"📊 <b>Tahlil statistikasi</b>\n\n"
        f"Jami tahlillar: <b>{total}</b>\n"
        f"Bugun qoldi: <b>{limit_txt}</b>"
    )
