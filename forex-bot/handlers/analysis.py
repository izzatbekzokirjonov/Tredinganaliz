from aiogram import F, Router
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    Message, PhotoSize,
)
from database import queries
from services.ai_service import generate_analysis_comment
from services.market_service import MarketDataError, analyze_pair
from services.vision_service import VisionAnalysisError, analyze_chart_image
from utils.helpers import trend_to_uz
from utils.logger import logger
import httpx

router = Router()

CATEGORIES = {
    "forex_major": {
        "name": "💱 Forex Major",
        "pairs": ["EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","NZDUSD","USDCAD"],
    },
    "forex_minor": {
        "name": "🔀 Forex Minor",
        "pairs": ["EURGBP","EURJPY","EURAUD","EURCAD","GBPJPY","GBPAUD","GBPCAD","AUDCAD","AUDCHF","AUDJPY"],
    },
    "metals": {
        "name": "🥇 Metallar",
        "pairs": ["XAUUSD","XAGUSD"],
    },
    "energy": {
        "name": "🛢 Energiya",
        "pairs": ["USOIL","UKOIL"],
    },
    "crypto": {
        "name": "₿ Kripto",
        "pairs": ["BTCUSD","ETHUSD","BNBUSD","XRPUSD","SOLUSD","ADAUSD"],
    },
}

TIMEFRAMES = {
    "1m":"1 daq","5m":"5 daq","15m":"15 daq","30m":"30 daq",
    "1h":"1 soat","4h":"4 soat","1D":"1 kun","1W":"1 hafta",
}

# Binance symbol map
BINANCE_MAP = {
    "BTCUSD":"BTCUSDT","ETHUSD":"ETHUSDT","BNBUSD":"BNBUSDT",
    "XRPUSD":"XRPUSDT","SOLUSD":"SOLUSDT","ADAUSD":"ADAUSDT",
}

# Twelve Data symbol map
TWELVEDATA_MAP = {
    "EURUSD":"EUR/USD","GBPUSD":"GBP/USD","USDJPY":"USD/JPY",
    "USDCHF":"USD/CHF","AUDUSD":"AUD/USD","NZDUSD":"NZD/USD",
    "USDCAD":"USD/CAD","EURGBP":"EUR/GBP","EURJPY":"EUR/JPY",
    "EURAUD":"EUR/AUD","EURCAD":"EUR/CAD","GBPJPY":"GBP/JPY",
    "GBPAUD":"GBP/AUD","GBPCAD":"GBP/CAD","AUDCAD":"AUD/CAD",
    "AUDCHF":"AUD/CHF","AUDJPY":"AUD/JPY","XAUUSD":"XAU/USD",
    "XAGUSD":"XAG/USD","USOIL":"USO/USD","UKOIL":"UKOIL",
}

async def get_price(pair: str) -> str:
    """Juftlik uchun joriy narxni qaytaradi."""
    try:
        if pair in BINANCE_MAP:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(
                    "https://api.binance.com/api/v3/ticker/price",
                    params={"symbol": BINANCE_MAP[pair]}
                )
                data = r.json()
                price = float(data["price"])
                if price > 1000:
                    return f"{price:,.0f}"
                elif price > 1:
                    return f"{price:.4f}"
                else:
                    return f"{price:.5f}"
        elif pair in TWELVEDATA_MAP:
            from config import TWELVE_DATA_API_KEY
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(
                    "https://api.twelvedata.com/price",
                    params={"symbol": TWELVEDATA_MAP[pair], "apikey": TWELVE_DATA_API_KEY}
                )
                data = r.json()
                price = float(data["price"])
                if price > 1000:
                    return f"{price:,.2f}"
                else:
                    return f"{price:.5f}"
    except Exception:
        pass
    return ""

async def categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=v["name"], callback_data=f"cat:{k}")]
        for k, v in CATEGORIES.items()
    ]
    buttons.append([InlineKeyboardButton(text="📸 Screenshot tahlil", callback_data="cat:screenshot")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def pairs_keyboard(cat_key: str) -> InlineKeyboardMarkup:
    cat = CATEGORIES[cat_key]
    buttons = []
    row = []
    for pair in cat["pairs"]:
        price = await get_price(pair)
        label = f"{pair} {price}" if price else pair
        row.append(InlineKeyboardButton(text=label, callback_data=f"pair:{cat_key}:{pair}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cat:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def timeframe_keyboard(pair: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for tf, label in TIMEFRAMES.items():
        row.append(InlineKeyboardButton(text=tf, callback_data=f"analyze:{pair}:{tf}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cat:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "📊 Analiz")
async def menu_analysis(message: Message, pool) -> None:
    remaining = await queries.get_remaining_limit(pool, message.from_user.id)
    limit_text = "♾️ Cheksiz" if remaining is None else f"{remaining} ta qoldi"
    await message.answer(
        f"📊 <b>Tahlil qilish</b>\n\n"
        f"Kategoriyani tanlang:\n"
        f"📋 Bugungi limit: <b>{limit_text}</b>",
        reply_markup=await categories_keyboard(),
    )

@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery, pool) -> None:
    key = callback.data.split(":")[1]
    if key == "back":
        remaining = await queries.get_remaining_limit(pool, callback.from_user.id)
        limit_text = "♾️ Cheksiz" if remaining is None else f"{remaining} ta qoldi"
        await callback.message.edit_text(
            f"📊 <b>Tahlil qilish</b>\n\nKategoriyani tanlang:\n📋 Limit: <b>{limit_text}</b>",
            reply_markup=await categories_keyboard(),
        )
    elif key == "screenshot":
        await callback.message.edit_text(
            "📸 <b>Screenshot tahlili</b>\n\n"
            "Chart rasmini yuboring — AI tahlil qiladi!\n\n"
            "<i>TradingView, MetaTrader yoki Binance screenshoti</i>",
        )
    elif key in CATEGORIES:
        cat = CATEGORIES[key]
        await callback.message.edit_text(
            f"⏳ Narxlar yuklanmoqda...",
        )
        kb = await pairs_keyboard(key)
        await callback.message.edit_text(
            f"{cat['name']}\n\nJuftlikni tanlang:",
            reply_markup=kb,
        )
    await callback.answer()

@router.callback_query(F.data.startswith("pair:"))
async def cb_pair(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    pair = parts[2]
    await callback.message.edit_text(
        f"📊 <b>{pair}</b>\n\nTimeframe tanlang:",
        reply_markup=timeframe_keyboard(pair),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("analyze:"))
async def cb_analyze(callback: CallbackQuery, pool) -> None:
    parts = callback.data.split(":")
    pair = parts[1]
    tf = parts[2] if len(parts) > 2 else "1h"
    await callback.message.edit_reply_markup(reply_markup=None)
    await _run_analysis(callback.message, pool, callback.from_user.id, pair, tf)
    await callback.answer()

@router.message(F.photo)
async def photo_analyze(message: Message, pool, bot) -> None:
    remaining = await queries.get_remaining_limit(pool, message.from_user.id)
    if remaining is not None and remaining <= 0:
        await message.answer("⛔ Kunlik limit tugadi! /premium")
        return
    photo: PhotoSize = message.photo[-1]
    loading = await message.answer("📸 Chart tahlil qilinmoqda...\n<i>10-15 soniya kuting</i>")
    try:
        analysis = await analyze_chart_image(bot, photo.file_id)
    except VisionAnalysisError as e:
        await loading.edit_text(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"Vision xatosi: {e}")
        await loading.edit_text("❌ Xato yuz berdi.")
        return
    await queries.log_analysis(pool, message.from_user.id, "SCREENSHOT")
    remaining_after = await queries.get_remaining_limit(pool, message.from_user.id)
    limit_line = "\n📋 Bugun qoldi: ♾️" if remaining_after is None else f"\n📋 Bugun qoldi: <b>{remaining_after} ta</b>"
    await loading.edit_text(
        f"📸 <b>Screenshot tahlili</b>\n{'─'*28}\n\n{analysis}"
        f"\n{'─'*28}{limit_line}\n<i>⚠️ AI tahlili — kafolat emas!</i>"
    )

async def _run_analysis(message: Message, pool, telegram_id: int, pair: str, tf: str = "1h") -> None:
    remaining = await queries.get_remaining_limit(pool, telegram_id)
    if remaining is not None and remaining <= 0:
        await message.answer("⛔ Kunlik limit tugadi! /premium")
        return
    tf_label = TIMEFRAMES.get(tf, tf)
    loading = await message.answer(f"⏳ <b>{pair}</b> · {tf_label} tahlil qilinmoqda...")
    try:
        result = await analyze_pair(pair, interval=tf)
    except MarketDataError as e:
        await loading.edit_text(f"❌ {e}")
        return
    except Exception as e:
        logger.error(f"Tahlil xatosi ({pair}): {e}")
        await loading.edit_text("❌ Xato yuz berdi.")
        return
    ai_comment = await generate_analysis_comment(
        pair=result.pair, trend=result.trend,
        entry=result.entry, tp=result.tp,
        sl=result.sl, current_price=result.current_price,
    )
    await queries.log_analysis(pool, telegram_id, pair)
    remaining_after = await queries.get_remaining_limit(pool, telegram_id)
    limit_line = "\n📋 Bugun qoldi: ♾️" if remaining_after is None else f"\n📋 Bugun qoldi: <b>{remaining_after} ta</b>"
    await loading.edit_text(
        f"📊 <b>{result.pair}</b> · <b>{tf}</b>\n\n"
        f"💹 Narx: <code>{result.current_price}</code>\n"
        f"📈 Trend: <b>{trend_to_uz(result.trend)}</b>\n\n"
        f"📍 Entry: <code>{result.entry}</code>\n"
        f"🎯 TP: <code>{result.tp}</code>\n"
        f"🛑 SL: <code>{result.sl}</code>\n\n"
        f"🤖 <b>AI izohi:</b>\n{ai_comment}"
        f"{limit_line}"
    )
