from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_inline_keyboard(bot_username: str, telegram_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Referal havolam", callback_data="profile:referral")
    builder.button(text="📊 Tahlil tarixi", callback_data="profile:history")
    builder.adjust(1)
    return builder.as_markup()
