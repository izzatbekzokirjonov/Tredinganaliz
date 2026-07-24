"""
/user [telegram_id] — foydalanuvchining to'liq profili va kanal holati (admin uchun).
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from database import queries
from database.channel_queries import get_user_channel_statuses
from services.channel_service import TYPE_LABELS, get_user_membership_report
from utils.helpers import format_datetime, tier_emoji

router = Router()


@router.message(Command("user"))
async def cmd_user(message: Message, bot, pool) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer("❗ Foydalanish: <code>/user 123456789</code>")
        return

    target_id = int(args[1].strip())
    user = await queries.get_user(pool, target_id)

    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    # Asosiy ma'lumotlar
    tier = user["subscription"]
    expires = format_datetime(user["subscription_expires_at"])
    banned = "🚫 Ha" if user["is_banned"] else "✅ Yo'q"
    joined = format_datetime(user["joined_at"])
    total_analyses = await queries.count_analysis_total_by_user(pool, target_id)

    text = (
        f"👤 <b>Foydalanuvchi profili</b>\n\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n"
        f"👤 Ism: {user['first_name'] or '—'}\n"
        f"🔗 Username: {('@' + user['username']) if user['username'] else '—'}\n"
        f"💳 Tarif: {tier_emoji(tier)} <b>{tier.upper()}</b>\n"
        f"📅 Tarif tugaydi: {expires}\n"
        f"👥 Referallar: {user['referrals']}\n"
        f"📊 Tahlillar: {total_analyses}\n"
        f"🚫 Ban: {banned}\n"
        f"📅 Qo'shilgan: {joined}\n\n"
    )

    # Kanal holatlari
    membership_report = await get_user_membership_report(bot, pool, target_id)
    text += f"📡 <b>Kanal holati:</b>\n{membership_report}"

    await message.answer(text)


@router.message(Command("members"))
async def cmd_members(message: Message, pool) -> None:
    """
    /members — barcha foydalanuvchilar va ularning kanal holati (soddalashtirilgan).
    """
    if message.from_user.id not in ADMIN_IDS:
        return

    users_ids = await queries.get_all_telegram_ids(pool)
    if not users_ids:
        await message.answer("📭 Foydalanuvchilar yo'q.")
        return

    # Kanal ro'yxatini olamiz
    from database.channel_queries import get_all_channels
    channels = await get_all_channels(pool)
    if not channels:
        await message.answer("📭 Hech qanday kanal sozlanmagan.")
        return

    lines = [f"📋 <b>Foydalanuvchilar a'zolik holati ({len(users_ids)} kishi):</b>\n"]
    ch_titles = [f"[{ch['title'][:10]}]" for ch in channels]
    lines.append("ID              " + "  ".join(ch_titles))
    lines.append("─" * 40)

    for uid in users_ids[:50]:  # birinchi 50 tasi (ko'p bo'lsa pagination kerak)
        statuses = await get_user_channel_statuses(pool, uid)
        icons = []
        for s in statuses:
            icons.append("✅" if s["is_member"] else "❌")
        lines.append(f"<code>{uid}</code>  " + "   ".join(icons))

    if len(users_ids) > 50:
        lines.append(f"\n... va yana {len(users_ids) - 50} ta foydalanuvchi")

    await message.answer("\n".join(lines))
