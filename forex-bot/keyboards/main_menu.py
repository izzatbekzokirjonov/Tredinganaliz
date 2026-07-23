from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Analiz")
    builder.button(text="📈 Signallar")
    builder.button(text="🧮 Kalkulyator")
    builder.button(text="👤 Profil")
    builder.button(text="💎 Premium")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
