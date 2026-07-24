"""
Tahlil handleri:
  - Juftlik tugmasi yoki matn → bozor ma'lumoti → AI izohi
  - Rasm (screenshot) → GPT-4o Vision → chart tahlili
"""
from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    PhotoSize,
)

from config import SUPPORTED_PAIRS
from database import queries
from services.ai_service import generate_analysis_comment
from services.market_service import MarketDataError, analyze_pair
from services.vision_service import VisionAnalysisError, analyze_chart_image
from utils.helpers import trend_to_uz
from utils.logger import logger
from utils.validators import is_supported_pair, normalize_pair

router = Router()

PAIR_EMOJIS = {"EURUSD": "🇪🇺", "GBPUSD": "🇬🇧", "XAUUSD": "🥇", "BTCUSD": "₿"}


def pair_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{PAIR_EMOJIS.get(p,'')} {p}",
            callback_data=f"analyze:{p}",
        )]
        for p in SUPPORTED_PAIRS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── "📊 Analiz" tugmasi ──────────────────────────────────────────

@router.message(F.text == "📊 Analiz")
async def menu_analysis(message: Message, pool) -> None:
    remaining = await queries.get_remaining_limit(pool, message.from_user.id)
    limit_text = "♾️ Cheksiz" if remaining is None else f"{remaining} ta qoldi"

    await message.answer(
        f"📊 <b>Tahlil qilish</b>\n\n"
        f"1️⃣ Juftlikni tanlang yoki yozing\n"
        f"📸 2️⃣ Chart <b>screenshotini</b> yuboring — AI o'zi tahlil qiladi!\n\n"
        f"📋 Bugungi limit: <b>{limit_text}</b>",
        reply_markup=pair_keyboard(),
    )


# ── Inline tugma: tayyor juftlik ────────────────────────────────

@router.callback_query(F.data.startswith("analyze:"))
async def cb_analyze(callback: CallbackQuery, pool) -> None:
    pair = callback.data.split(":")[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    await _run_market_analysis(callback.message, pool, callback.from_user.id, pair)


# ── Matndan juftlik kiritish ─────────────────────────────────────

@router.message(F.text.regexp(r"^[A-Za-z]{6,8}$"))
async def text_analyze(message: Message, pool) -> None:
    pair = normalize_pair(message.text)
    if not is_supported_pair(pair):
        await message.answer(
            f"❌ <b>{pair}</b> qo'llab-quvvatlanmaydi.\n"
            f"Mavjud: {', '.join(SUPPORTED_PAIRS)}"
        )
        return
    await _run_market_analysis(message, pool, message.from_user.id, pair)


# ── Screenshot tahlili ───────────────────────────────────────────

@router.message(F.photo)
async def photo_analyze(message: Message, pool, bot) -> None:
    # Limit tekshiruvi (screenshot ham limitga kiradi)
    remaining = await queries.get_remaining_limit(pool, message.from_user.id)
    if remaining is not None and remaining <= 0:
        tier = await queries.get_effective_tier(pool, message.from_user.id)
        await message.answer(
            "⛔ <b>Kunlik limit tugadi!</b>\n\n"
            f"💳 Hozirgi tarif: <b>{tier.upper()}</b>\n"
            "💎 Ko'proq tahlil uchun Premium oling — /premium"
        )
        return

    # Eng yuqori sifatli rasmni olamiz
    photo: PhotoSize = message.photo[-1]

    caption = message.caption or ""
    extra_hint = f"\nFoydalanuvchi izohi: {caption}" if caption.strip() else ""

    loading = await message.answer(
        "📸 <b>Chart tahlil qilinmoqda...</b>\n"
        "<i>GPT-4o Vision ishlamoqda, 5-15 soniya kuting...</i>"
    )

    try:
        analysis = await analyze_chart_image(bot, photo.file_id)
    except VisionAnalysisError as e:
        await loading.edit_text(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"Vision xatosi: {e}")
        await loading.edit_text("❌ Kutilmagan xato. Qayta urinib ko'ring.")
        return

    # DB ga yozamiz
    await queries.log_analysis(pool, message.from_user.id, "SCREENSHOT")

    remaining_after = await queries.get_remaining_limit(pool, message.from_user.id)
    limit_line = (
        "\n📋 Bugun qoldi: ♾️"
        if remaining_after is None
        else f"\n📋 Bugun qoldi: <b>{remaining_after} ta</b>"
    )

    result_text = (
        f"📸 <b>Screenshot tahlili</b>\n"
        f"{'─' * 28}\n\n"
        f"{analysis}"
        f"\n{'─' * 28}"
        f"{limit_line}\n"
        f"<i>⚠️ AI tahlili — kafolat emas. Risk menejmentga rioya qiling.</i>"
    )

    await loading.edit_text(result_text)


# ── Bozor ma'lumoti asosida tahlil ──────────────────────────────

async def _run_market_analysis(
    message: Message, pool, telegram_id: int, pair: str
) -> None:
    remaining = await queries.get_remaining_limit(pool, telegram_id)
    if remaining is not None and remaining <= 0:
        tier = await queries.get_effective_tier(pool, telegram_id)
        await message.answer(
            "⛔ <b>Kunlik limit tugadi!</b>\n\n"
            f"💳 Hozirgi tarif: <b>{tier.upper()}</b>\n"
            "💎 Premium oling — /premium"
        )
        return

    loading = await message.answer(f"⏳ <b>{pair}</b> tahlil qilinmoqda...")

    try:
        result = await analyze_pair(pair)
    except MarketDataError as e:
        await loading.edit_text(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"Tahlil xatosi ({pair}): {e}")
        await loading.edit_text("❌ Kutilmagan xato. Qayta urinib ko'ring.")
        return

    ai_comment = await generate_analysis_comment(
        pair=result.pair,
        trend=result.trend,
        entry=result.entry,
        tp=result.tp,
        sl=result.sl,
        current_price=result.current_price,
    )

    await queries.log_analysis(pool, telegram_id, pair)

    remaining_after = await queries.get_remaining_limit(pool, telegram_id)
    limit_line = (
        "\n📋 Bugun qoldi: ♾️"
        if remaining_after is None
        else f"\n📋 Bugun qoldi: <b>{remaining_after} ta</b>"
    )

    text = (
        f"📊 <b>{result.pair} — Tahlil natijasi</b>\n\n"
        f"💹 Joriy narx: <code>{result.current_price}</code>\n"
        f"📈 Trend: <b>{trend_to_uz(result.trend)}</b>\n\n"
        f"📍 Entry: <code>{result.entry}</code>\n"
        f"🎯 TP: <code>{result.tp}</code>\n"
        f"🛑 SL: <code>{result.sl}</code>\n\n"
        f"🤖 <b>AI izohi:</b>\n{ai_comment}"
        f"{limit_line}"
    )

    await loading.edit_text(text)
