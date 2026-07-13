"""NexForexAI MVP - Telegram bot entrypoint."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    PreCheckoutQuery,
)

from config import (
    TELEGRAM_BOT_TOKEN, SUPPORTED_PAIRS, RISK_DISCLAIMER,
    PLAN_LIMITS, PLAN_PRICES_USD, ADMIN_IDS,
)
from db.database import init_db
from services.market_data import fetch_candles, MarketDataError
from services.indicators import analyze
from services.ai_analysis import explain_signal
from services import subscription as sub
from services import payments as pay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


def pairs_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=pair, callback_data=f"pair:{pair}")]
        for pair in SUPPORTED_PAIRS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def plans_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{plan.capitalize()} - ${price}/oy",
            callback_data=f"buy:{plan}",
        )]
        for plan, price in PLAN_PRICES_USD.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await sub.get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 <b>NexForexAI</b> — AI asosidagi savdo tahlil boti (MVP)\n\n"
        "Quyidagi valyuta juftligini tanlang, men texnik indikatorlar va "
        "AI yordamida qisqa tahlil beraman.\n\n"
        "Buyruqlar: /premium — reja sotib olish, /promo — promo kod, /status — hisobim",
        reply_markup=pairs_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    user = await sub.get_or_create_user(message.from_user.id, message.from_user.username)
    limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
    expires = user.plan_expires_at.strftime("%Y-%m-%d") if user.plan_expires_at else "—"
    await message.answer(
        f"📋 <b>Hisobingiz</b>\n"
        f"Reja: {user.plan.capitalize()}\n"
        f"Bugungi ishlatilgan signal: {user.signals_used_today}/{limit}\n"
        f"Reja tugash sanasi: {expires}",
        parse_mode="HTML",
    )


@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    await message.answer(
        "💎 <b>Rejalarni tanlang</b>\n\n"
        "Premium/Pro reja kunlik signal limitini oshiradi.",
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("buy:"))
async def handle_buy(callback: CallbackQuery):
    plan = callback.data.split("buy:", 1)[1]
    await callback.answer()

    if not pay.PAYMENT_PROVIDER_TOKEN:
        await callback.message.answer(
            "⚠️ To'lov provayderi hali ulanmagan. @BotFather → Payments orqali "
            "provider token sozlang, keyin bu tugma ishlaydi.\n\n"
            "Hozircha /promo orqali promo kod bilan faollashtirishingiz mumkin."
        )
        return

    params = pay.build_invoice_params(plan)
    await bot.send_invoice(chat_id=callback.message.chat.id, **params)


@dp.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    sp = message.successful_payment
    plan, days = pay.parse_payload(sp.invoice_payload)

    await sub.activate_plan(message.from_user.id, plan, days)
    await sub.record_payment(
        telegram_id=message.from_user.id,
        plan=plan,
        amount=sp.total_amount / 100,
        currency=sp.currency,
        provider_payment_id=sp.provider_payment_charge_id,
    )
    await message.answer(f"✅ To'lov qabul qilindi! '{plan.capitalize()}' reja {days} kunga faollashdi.")


@dp.message(Command("promo"))
async def cmd_promo(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Promo kodni shunday kiriting: <code>/promo KODINGIZ</code>", parse_mode="HTML")
        return

    code = parts[1]
    ok, msg = await sub.redeem_promocode(message.from_user.id, code)
    await message.answer(("✅ " if ok else "❌ ") + msg)


@dp.message(Command("grant"))
async def cmd_admin_grant(message: Message):
    """Admin-only: /grant <telegram_id> <plan> <days>"""
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("Foydalanish: /grant <telegram_id> <plan> <days>")
        return
    _, uid, plan, days = parts
    await sub.activate_plan(int(uid), plan, int(days))
    await message.answer(f"✅ {uid} foydalanuvchiga {plan} ({days} kun) berildi.")


@dp.callback_query(F.data.startswith("pair:"))
async def handle_pair_selection(callback: CallbackQuery):
    symbol = callback.data.split("pair:", 1)[1]
    await callback.answer()

    allowed, plan, used, limit = await sub.check_and_consume_quota(callback.from_user.id)
    if not allowed:
        await callback.message.answer(
            f"🚫 Kunlik signal limitingiz tugadi ({used}/{limit}, {plan} reja).\n"
            f"Ko'proq signal uchun /premium buyrug'ini ishlating."
        )
        return

    status_msg = await callback.message.answer(f"⏳ {symbol} tahlil qilinmoqda...")

    try:
        df = await fetch_candles(symbol)
        analysis = analyze(df)
        explanation = await explain_signal(symbol, analysis, lang="uz")

        latest = analysis["latest"]
        text = (
            f"📊 <b>{symbol}</b> — Narx: {latest['price']}\n\n"
            f"<b>Signal: {analysis['direction']}</b> ({analysis['confidence']}% ishonch)\n\n"
            f"{explanation}\n\n"
            f"<i>RSI: {latest['rsi']} | EMA20: {latest['ema_20']} | EMA50: {latest['ema_50']} | "
            f"MACD: {latest['macd']}</i>\n\n"
            f"📈 Bugungi ishlatilgan: {used}/{limit}\n\n"
            f"{RISK_DISCLAIMER}"
        )
        await status_msg.edit_text(text, parse_mode="HTML")

    except MarketDataError as e:
        await status_msg.edit_text(f"❌ Xatolik: {e}")
    except Exception:
        logger.exception("Signal generation failed")
        await status_msg.edit_text(
            "❌ Tahlil qilishda kutilmagan xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
        )


async def main():
    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()
    logger.info("NexForexAI bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
