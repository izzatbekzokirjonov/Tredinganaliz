from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def premium_info_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Admin bilan bog'lanish", url="https://t.me/admin")
    builder.adjust(1)
    return builder.as_markup()
