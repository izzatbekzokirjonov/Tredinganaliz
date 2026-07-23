from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika",       callback_data="admin:stats")
    builder.button(text="📡 Kanallar",         callback_data="admin:channels")
    builder.button(text="🟢 Premium berish",   callback_data="admin:give_premium")
    builder.button(text="🔴 Premium olish",    callback_data="admin:revoke_premium")
    builder.button(text="📢 Broadcast",        callback_data="admin:broadcast")
    builder.button(text="📈 Signal yuborish",  callback_data="admin:signal")
    builder.button(text="🚫 Ban",              callback_data="admin:ban")
    builder.button(text="✅ Unban",            callback_data="admin:unban")
    builder.adjust(2)
    return builder.as_markup()


def tier_select_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Pro",  callback_data=f"{prefix}:pro")
    builder.button(text="💎 VIP", callback_data=f"{prefix}:vip")
    builder.button(text="🆓 Free (olish)", callback_data=f"{prefix}:free")
    builder.adjust(2, 1)
    return builder.as_markup()


def days_select_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in [1, 3, 7, 14, 30]:
        builder.button(text=f"{d} kun", callback_data=f"{prefix}:{d}")
    builder.button(text="♾️ Muddatsiz", callback_data=f"{prefix}:0")
    builder.adjust(3, 2, 1)
    return builder.as_markup()
