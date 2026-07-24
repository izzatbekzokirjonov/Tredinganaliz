"""
Kanal a'zoligini tekshirish va kanallarni boshqarish servisi.

Bot kanalda admin bo'lishi SHART — aks holda get_chat_member() ishlmaydi.
"""
from dataclasses import dataclass
from typing import Optional

import asyncpg
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database import channel_queries
from utils.logger import logger

CHANNEL_TYPES = {
    "mandatory": ("🔒 Majburiy", True),
    "signal":    ("📈 Signal kanali", False),
    "lesson":    ("📚 Darslik kanali", False),
    "info":      ("ℹ️ Ma'lumot kanali", False),
}

TYPE_LABELS = {k: v[0] for k, v in CHANNEL_TYPES.items()}


@dataclass
class MembershipResult:
    all_ok: bool                           # Barcha majburiy kanallarga a'zomi?
    missing: list[dict]                    # A'zo bo'lmagan majburiy kanallar


# ─────────────────────────────────────────────
#  A'ZOLIKNI TEKSHIRISH
# ─────────────────────────────────────────────

async def check_user_membership(
    bot: Bot,
    pool: asyncpg.Pool,
    telegram_id: int,
) -> MembershipResult:
    """
    Foydalanuvchini barcha faol kanallarda tekshiradi,
    natijani DB ga yozadi va MembershipResult qaytaradi.
    """
    channels = await channel_queries.get_all_channels(pool)
    missing = []

    for ch in channels:
        is_member = await _check_single(bot, telegram_id, ch["channel_id"])
        await channel_queries.upsert_user_channel_status(
            pool, telegram_id, ch["channel_id"], is_member
        )
        if ch["is_mandatory"] and not is_member:
            missing.append({
                "channel_id": ch["channel_id"],
                "title":      ch["title"],
                "username":   ch["username"],
            })

    return MembershipResult(all_ok=len(missing) == 0, missing=missing)


async def _check_single(bot: Bot, telegram_id: int, channel_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=telegram_id)
        return member.status not in ("left", "kicked", "banned")
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logger.warning(f"Kanal tekshirishda xato (ch={channel_id}, user={telegram_id}): {e}")
        return True   # Xato bo'lsa, bloklashdan saqlanish uchun True
    except Exception as e:
        logger.error(f"Kutilmagan xato (ch={channel_id}): {e}")
        return True


# ─────────────────────────────────────────────
#  KANAL QO'SHISH
# ─────────────────────────────────────────────

async def register_channel(
    bot: Bot,
    pool: asyncpg.Pool,
    channel_input: str,   # "@username" yoki "-100xxxxxxxxxx"
    type_: str,
    added_by: int,
) -> dict:
    """
    Kanal ma'lumotlarini Telegram API dan olib DB ga yozadi.
    {'ok': True, 'channel': record} yoki {'ok': False, 'error': str}
    """
    type_ = type_.lower()
    if type_ not in CHANNEL_TYPES:
        return {"ok": False, "error": f"Noma'lum tur: {type_}"}

    is_mandatory = CHANNEL_TYPES[type_][1]

    # channel_id yoki @username ni aniqlash
    if channel_input.lstrip("-").isdigit():
        chat_id: int | str = int(channel_input)
    else:
        chat_id = channel_input if channel_input.startswith("@") else f"@{channel_input}"

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        logger.error(f"Kanal topilmadi ({channel_input}): {e}")
        return {"ok": False, "error": f"Kanal topilmadi: {e}"}

    username = f"@{chat.username}" if chat.username else None
    record = await channel_queries.add_channel(
        pool,
        channel_id=chat.id,
        username=username,
        title=chat.title or channel_input,
        type_=type_,
        is_mandatory=is_mandatory,
        added_by=added_by,
    )
    return {"ok": True, "channel": record}


# ─────────────────────────────────────────────
#  FOYDALANUVCHI TO'LIQ HOLATI (ADMIN UCHUN)
# ─────────────────────────────────────────────

async def get_user_membership_report(
    bot: Bot,
    pool: asyncpg.Pool,
    telegram_id: int,
) -> str:
    """Admin uchun: foydalanuvchining barcha kanallardagi holati matnli hisoboti."""
    # Yangi tekshirish o'tkazamiz
    await check_user_membership(bot, pool, telegram_id)
    statuses = await channel_queries.get_user_channel_statuses(pool, telegram_id)

    if not statuses:
        return "⚠️ Hech qanday faol kanal yo'q."

    lines = []
    for s in statuses:
        icon = "✅" if s["is_member"] else "❌"
        mandatory = " 🔒" if s["is_mandatory"] else ""
        label = TYPE_LABELS.get(s["type"], s["type"])
        username = f" ({s['username']})" if s["username"] else ""
        lines.append(f"{icon} {s['title']}{username}{mandatory}\n   └ {label}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
#  MAJBURIY KANALLAR XABARI (FOYDALANUVCHI UCHUN)
# ─────────────────────────────────────────────

def format_subscription_required(missing: list[dict]) -> str:
    lines = ["⛔ <b>Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:</b>\n"]
    for ch in missing:
        link = f"https://t.me/{ch['username'].lstrip('@')}" if ch["username"] else f"tg://resolve?domain={ch['channel_id']}"
        lines.append(f"📌 <a href='{link}'>{ch['title']}</a>")
    lines.append("\n✅ A'zo bo'lgach, /start ni bosing.")
    return "\n".join(lines)
