"""
Risk Kalkulyator handleri (FSM):
  1. Balans (USD)
  2. Risk foizi (%)
  3. Stop Loss (pips)
  → Lot hajmi va risk summasi
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from keyboards.main_menu import main_menu_keyboard
from states.calculator_state import CalculatorStates
from utils.validators import parse_positive_float

router = Router()


def _cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


# ── Boshlash ─────────────────────────────────────────────────────

@router.message(F.text == "🧮 Kalkulyator")
async def menu_calculator(message: Message, state: FSMContext) -> None:
    await state.set_state(CalculatorStates.waiting_balance)
    await message.answer(
        "🧮 <b>Risk Kalkulyator</b>\n\n"
        "1️⃣ Hisob balansini kiriting (USD):\n"
        "<i>Masalan: 1000</i>",
        reply_markup=_cancel_keyboard(),
    )


# ── Bekor qilish ─────────────────────────────────────────────────

@router.message(F.text == "❌ Bekor qilish")
async def cancel_calculator(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())


# ── 1-qadam: Balans ──────────────────────────────────────────────

@router.message(CalculatorStates.waiting_balance)
async def process_balance(message: Message, state: FSMContext) -> None:
    balance = parse_positive_float(message.text)
    if balance is None:
        await message.answer("❗ Musbat son kiriting. Masalan: <code>1000</code>")
        return

    await state.update_data(balance=balance)
    await state.set_state(CalculatorStates.waiting_risk_percent)
    await message.answer(
        f"✅ Balans: <b>${balance:,.2f}</b>\n\n"
        "2️⃣ Risk foizini kiriting (1–10%):\n"
        "<i>Masalan: 2</i>"
    )


# ── 2-qadam: Risk foizi ──────────────────────────────────────────

@router.message(CalculatorStates.waiting_risk_percent)
async def process_risk(message: Message, state: FSMContext) -> None:
    risk_pct = parse_positive_float(message.text)
    if risk_pct is None or risk_pct > 100:
        await message.answer("❗ 1 dan 100 gacha son kiriting. Masalan: <code>2</code>")
        return

    await state.update_data(risk_pct=risk_pct)
    await state.set_state(CalculatorStates.waiting_stoploss_pips)
    await message.answer(
        f"✅ Risk: <b>{risk_pct}%</b>\n\n"
        "3️⃣ Stop Loss hajmini kiriting (pips):\n"
        "<i>Masalan: 30</i>"
    )


# ── 3-qadam: SL pips → hisoblash ────────────────────────────────

@router.message(CalculatorStates.waiting_stoploss_pips)
async def process_stoploss(message: Message, state: FSMContext) -> None:
    sl_pips = parse_positive_float(message.text)
    if sl_pips is None:
        await message.answer("❗ Musbat son kiriting. Masalan: <code>30</code>")
        return

    data = await state.get_data()
    balance: float = data["balance"]
    risk_pct: float = data["risk_pct"]

    risk_amount = balance * risk_pct / 100

    # Standart lot hisoblash:
    # 1 pip = $10 (standart lot), lot = risk_amount / (sl_pips * 10)
    pip_value_per_lot = 10.0
    lot_size = risk_amount / (sl_pips * pip_value_per_lot)
    lot_size = max(round(lot_size, 2), 0.01)

    # Tavsiya darajasi
    if risk_pct <= 1:
        advice = "🟢 Konservativ — yangi boshlovchilar uchun ideal"
    elif risk_pct <= 2:
        advice = "🟡 O'rtacha — professional standart"
    elif risk_pct <= 5:
        advice = "🟠 Yuqori risk — tajribali treyderlar uchun"
    else:
        advice = "🔴 Juda yuqori risk — ehtiyot bo'ling!"

    result_text = (
        f"📊 <b>Risk Kalkulyator — Natija</b>\n\n"
        f"💰 Balans: <code>${balance:,.2f}</code>\n"
        f"⚠️ Risk: <code>{risk_pct}%</code>\n"
        f"📉 Stop Loss: <code>{sl_pips:.0f} pips</code>\n\n"
        f"─────────────────\n"
        f"💸 Xavf summasi: <b>${risk_amount:,.2f}</b>\n"
        f"📦 Lot hajmi: <b>{lot_size} lot</b>\n"
        f"─────────────────\n"
        f"💡 Tavsiya: {advice}\n\n"
        f"<i>⚠️ Hisob standart forex lot (100,000 birlik) asosida.</i>"
    )

    await state.clear()
    await message.answer(result_text, reply_markup=main_menu_keyboard())
