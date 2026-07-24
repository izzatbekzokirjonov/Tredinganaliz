"""
Admin panel handleri.

Buyruqlar:
  /admin          — bosh panel
  /stats          — statistika
  /broadcast      — barcha foydalanuvchilarga xabar
  /signal         — signal yuborish
  /premium_give   — premium berish
  /premium_remove — premium olish
  /ban            — ban
  /unban          — unban
"""
import asyncio
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database import queries
from keyboards.admin_menu import (
    admin_main_keyboard,
    days_select_keyboard,
    tier_select_keyboard,
)
from services.payment_service import grant_premium, revoke_premium
from services.signal_service import broadcast_signal, format_signal
from utils.logger import logger
from utils.validators import parse_positive_float, parse_telegram_id

router = Router()


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


# ═══════════════════════════════════════════
#  FSM HOLATLARI
# ═══════════════════════════════════════════

class BroadcastState(StatesGroup):
    waiting_text = State()


class SignalState(StatesGroup):
    waiting_pair      = State()
    waiting_direction = State()
    waiting_entry     = State()
    waiting_tp        = State()
    waiting_sl        = State()
    waiting_comment   = State()


class PremiumGiveState(StatesGroup):
    waiting_user_id = State()
    waiting_tier    = State()
    waiting_days    = State()


class PremiumRemoveState(StatesGroup):
    waiting_user_id = State()


class BanState(StatesGroup):
    waiting_user_id = State()


class UnbanState(StatesGroup):
    waiting_user_id = State()


# ═══════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════

async def _get_user_or_fail(message: Message, pool, telegram_id: int) -> Optional[dict]:
    user = await queries.get_user(pool, telegram_id)
    if not user:
        await message.answer(f"❌ ID <code>{telegram_id}</code> topilmadi.")
        return None
    return user


def _cancel_text() -> str:
    return "\n\n<i>Bekor qilish uchun /cancel</i>"


# ═══════════════════════════════════════════
#  BEKOR QILISH
# ═══════════════════════════════════════════

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


# ═══════════════════════════════════════════
#  BOSH PANEL
# ═══════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery, pool) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await _send_stats(callback.message, pool)


@router.message(Command("stats"))
async def cmd_stats(message: Message, pool) -> None:
    if not is_admin(message.from_user.id):
        return
    await _send_stats(message, pool)


async def _send_stats(message: Message, pool) -> None:
    total = await queries.count_users(pool)
    by_tier = await queries.count_premium_users(pool)
    analyses = await queries.count_total_analyses(pool)

    free_count = by_tier.get("free", 0)
    pro_count  = by_tier.get("pro", 0)
    vip_count  = by_tier.get("vip", 0)

    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchi: <b>{total}</b>\n"
        f"🆓 Free: <b>{free_count}</b>\n"
        f"⭐ Pro: <b>{pro_count}</b>\n"
        f"💎 VIP: <b>{vip_count}</b>\n\n"
        f"📈 Jami tahlillar: <b>{analyses}</b>"
    )


# ═══════════════════════════════════════════
#  BROADCAST
# ═══════════════════════════════════════════

@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(BroadcastState.waiting_text)
    await callback.message.answer(
        "📢 <b>Broadcast</b>\n\n"
        "Barcha foydalanuvchilarga yuborilajak xabarni yozing:"
        + _cancel_text()
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_text)
    await message.answer("📢 Xabar matnini yozing:" + _cancel_text())


@router.message(BroadcastState.waiting_text)
async def process_broadcast(message: Message, state: FSMContext, bot, pool) -> None:
    text = message.text or message.caption or ""
    if not text:
        await message.answer("❗ Matn kiriting.")
        return

    await state.clear()
    user_ids = await queries.get_all_telegram_ids(pool)
    total = len(user_ids)

    status_msg = await message.answer(f"⏳ Yuborilmoqda... (0 / {total})")
    sent, failed = 0, 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📣 <b>E'lon</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
        if (sent + failed) % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"⏳ Yuborilmoqda... ({sent + failed} / {total})"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ <b>Broadcast tugadi!</b>\n\n"
        f"✅ Yuborildi: <b>{sent}</b>\n"
        f"❌ Xato: <b>{failed}</b>"
    )


# ═══════════════════════════════════════════
#  SIGNAL YUBORISH
# ═══════════════════════════════════════════

@router.callback_query(F.data == "admin:signal")
async def cb_signal(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await _start_signal(callback.message, state)


@router.message(Command("signal"))
async def cmd_signal(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await _start_signal(message, state)


async def _start_signal(message: Message, state: FSMContext) -> None:
    await state.set_state(SignalState.waiting_pair)
    await message.answer(
        "📈 <b>Yangi signal</b>\n\nJuftlik kiriting (masalan: EURUSD, XAUUSD):"
        + _cancel_text()
    )


@router.message(SignalState.waiting_pair)
async def signal_pair(message: Message, state: FSMContext) -> None:
    pair = message.text.strip().upper().replace("/", "")
    await state.update_data(pair=pair)
    await state.set_state(SignalState.waiting_direction)
    await message.answer("Yo'nalish: <b>BUY</b> yoki <b>SELL</b>?")


@router.message(SignalState.waiting_direction, F.text.upper().in_({"BUY", "SELL"}))
async def signal_direction(message: Message, state: FSMContext) -> None:
    await state.update_data(direction=message.text.upper())
    await state.set_state(SignalState.waiting_entry)
    await message.answer("Entry narxini kiriting:")


@router.message(SignalState.waiting_entry)
async def signal_entry(message: Message, state: FSMContext) -> None:
    val = parse_positive_float(message.text)
    if val is None:
        await message.answer("❗ To'g'ri narx kiriting.")
        return
    await state.update_data(entry=val)
    await state.set_state(SignalState.waiting_tp)
    await message.answer("Take Profit (TP) narxini kiriting:")


@router.message(SignalState.waiting_tp)
async def signal_tp(message: Message, state: FSMContext) -> None:
    val = parse_positive_float(message.text)
    if val is None:
        await message.answer("❗ To'g'ri narx kiriting.")
        return
    await state.update_data(tp=val)
    await state.set_state(SignalState.waiting_sl)
    await message.answer("Stop Loss (SL) narxini kiriting:")


@router.message(SignalState.waiting_sl)
async def signal_sl(message: Message, state: FSMContext) -> None:
    val = parse_positive_float(message.text)
    if val is None:
        await message.answer("❗ To'g'ri narx kiriting.")
        return
    await state.update_data(sl=val)
    await state.set_state(SignalState.waiting_comment)
    await message.answer("Izoh kiriting (yoki — yozing, o'tkazib yuborish uchun):")


@router.message(SignalState.waiting_comment)
async def signal_comment(message: Message, state: FSMContext, bot, pool) -> None:
    comment = "" if message.text.strip() == "—" else message.text.strip()
    data = await state.get_data()
    await state.clear()

    signal = await queries.add_signal(
        pool,
        pair=data["pair"],
        direction=data["direction"],
        entry=data["entry"],
        tp=data["tp"],
        sl=data["sl"],
        comment=comment,
        created_by=message.from_user.id,
    )

    preview = format_signal(signal)
    await message.answer(f"✅ <b>Signal saqlandi!</b>\n\n{preview}")

    sent, failed = await broadcast_signal(bot, pool, signal)
    await message.answer(
        f"📢 <b>Tarqatildi:</b> ✅ {sent} ta · ❌ {failed} ta xato"
    )


# ═══════════════════════════════════════════
#  PREMIUM BERISH
# ═══════════════════════════════════════════

@router.callback_query(F.data == "admin:give_premium")
async def cb_give_premium(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await _start_give_premium(callback.message, state)


@router.message(Command("premium_give"))
async def cmd_give_premium(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await _start_give_premium(message, state)


async def _start_give_premium(message: Message, state: FSMContext) -> None:
    await state.set_state(PremiumGiveState.waiting_user_id)
    await message.answer(
        "🟢 <b>Premium berish</b>\n\nFoydalanuvchi Telegram ID sini kiriting:"
        + _cancel_text()
    )


@router.message(PremiumGiveState.waiting_user_id)
async def give_premium_user(message: Message, state: FSMContext, pool) -> None:
    uid = parse_telegram_id(message.text)
    if uid is None:
        await message.answer("❗ To'g'ri Telegram ID kiriting.")
        return
    user = await _get_user_or_fail(message, pool, uid)
    if not user:
        return
    await state.update_data(target_id=uid)
    await state.set_state(PremiumGiveState.waiting_tier)
    await message.answer(
        f"👤 Foydalanuvchi: <b>{user['first_name'] or uid}</b>\n\nTarifni tanlang:",
        reply_markup=tier_select_keyboard("give_tier"),
    )


@router.callback_query(F.data.startswith("give_tier:"), PremiumGiveState.waiting_tier)
async def give_premium_tier(callback: CallbackQuery, state: FSMContext) -> None:
    tier = callback.data.split(":")[1]
    if tier == "free":
        data = await state.get_data()
        await state.clear()
        # To'g'ridan-to'g'ri free ga qaytaramiz
        from database import queries as q
        # pool ni callback dan olamiz — bu yerda pool mavjud emas, keyingi bosqichda olamiz
        await callback.answer()
        await state.update_data(target_id=data["target_id"], tier="free", days=None)
        await state.set_state(PremiumGiveState.waiting_days)
        # Free uchun kun so'ramasdan to'g'ri bajaramiz
        await state.update_data(tier="free")
        await callback.message.edit_text("Tasdiqlash...")
        # Davom ettirish uchun days=None bilan chaqiramiz
        await _finalize_premium(callback.message, state, None, data["target_id"], "free")
        return

    await state.update_data(tier=tier)
    await state.set_state(PremiumGiveState.waiting_days)
    await callback.answer()
    await callback.message.edit_text(
        f"Tarif: <b>{tier.upper()}</b>\n\nNecha kunga?",
        reply_markup=days_select_keyboard("give_days"),
    )


@router.callback_query(F.data.startswith("give_days:"), PremiumGiveState.waiting_days)
async def give_premium_days(callback: CallbackQuery, state: FSMContext, pool) -> None:
    days_str = callback.data.split(":")[1]
    days = None if days_str == "0" else int(days_str)
    data = await state.get_data()
    await callback.answer()
    await _finalize_premium(callback.message, state, pool, data["target_id"], data["tier"], days)


async def _finalize_premium(
    message: Message, state: FSMContext, pool, target_id: int, tier: str, days=None
) -> None:
    await state.clear()
    if pool is None:
        await message.edit_text("❌ Pool topilmadi.")
        return
    try:
        await grant_premium(pool, target_id, tier, days)
    except Exception as e:
        await message.edit_text(f"❌ Xato: {e}")
        return

    days_txt = "Muddatsiz" if days is None else f"{days} kun"
    await message.edit_text(
        f"✅ <b>Premium berildi!</b>\n\n"
        f"👤 ID: <code>{target_id}</code>\n"
        f"💳 Tarif: <b>{tier.upper()}</b>\n"
        f"📅 Muddat: <b>{days_txt}</b>"
    )


# ═══════════════════════════════════════════
#  PREMIUM OLISH
# ═══════════════════════════════════════════

@router.callback_query(F.data == "admin:revoke_premium")
async def cb_revoke_premium(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(PremiumRemoveState.waiting_user_id)
    await callback.message.answer(
        "🔴 <b>Premium olish</b>\n\nFoydalanuvchi Telegram ID sini kiriting:"
        + _cancel_text()
    )


@router.message(Command("premium_remove"))
async def cmd_revoke_premium(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.set_state(PremiumRemoveState.waiting_user_id)
    await message.answer("🔴 Foydalanuvchi ID sini kiriting:" + _cancel_text())


@router.message(PremiumRemoveState.waiting_user_id)
async def process_revoke_premium(message: Message, state: FSMContext, pool) -> None:
    uid = parse_telegram_id(message.text)
    if uid is None:
        await message.answer("❗ To'g'ri ID kiriting.")
        return
    user = await _get_user_or_fail(message, pool, uid)
    if not user:
        return
    await state.clear()
    await revoke_premium(pool, uid)
    await message.answer(
        f"✅ <b>{user['first_name'] or uid}</b> ning premiumi olib tashlandi."
    )


# ═══════════════════════════════════════════
#  BAN / UNBAN
# ═══════════════════════════════════════════

@router.callback_query(F.data == "admin:ban")
async def cb_ban(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(BanState.waiting_user_id)
    await callback.message.answer("🚫 Ban: foydalanuvchi ID sini kiriting:" + _cancel_text())


@router.message(Command("ban"))
async def cmd_ban(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        uid = parse_telegram_id(args[1])
        if uid:
            await _do_ban(message, None, uid)
            return

    await state.set_state(BanState.waiting_user_id)
    await message.answer("🚫 Ban: foydalanuvchi ID sini kiriting:" + _cancel_text())


@router.message(BanState.waiting_user_id)
async def process_ban(message: Message, state: FSMContext, pool) -> None:
    uid = parse_telegram_id(message.text)
    if uid is None:
        await message.answer("❗ To'g'ri ID kiriting.")
        return
    await state.clear()
    await _do_ban(message, pool, uid)


async def _do_ban(message: Message, pool, uid: int) -> None:
    ok = await queries.ban_user(pool, uid)
    if ok:
        await message.answer(f"🚫 <code>{uid}</code> ban qilindi.")
    else:
        await message.answer(f"❌ <code>{uid}</code> topilmadi.")


@router.callback_query(F.data == "admin:unban")
async def cb_unban(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(UnbanState.waiting_user_id)
    await callback.message.answer("✅ Unban: foydalanuvchi ID sini kiriting:" + _cancel_text())


@router.message(Command("unban"))
async def cmd_unban(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        uid = parse_telegram_id(args[1])
        if uid:
            await _do_unban(message, None, uid)
            return
    await state.set_state(UnbanState.waiting_user_id)
    await message.answer("✅ Unban: ID kiriting:" + _cancel_text())


@router.message(UnbanState.waiting_user_id)
async def process_unban(message: Message, state: FSMContext, pool) -> None:
    uid = parse_telegram_id(message.text)
    if uid is None:
        await message.answer("❗ To'g'ri ID kiriting.")
        return
    await state.clear()
    await _do_unban(message, pool, uid)


async def _do_unban(message: Message, pool, uid: int) -> None:
    ok = await queries.unban_user(pool, uid)
    if ok:
        await message.answer(f"✅ <code>{uid}</code> unban qilindi.")
    else:
        await message.answer(f"❌ <code>{uid}</code> topilmadi.")
