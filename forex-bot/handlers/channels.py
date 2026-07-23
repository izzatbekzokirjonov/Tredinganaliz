"""
Admin kanallarni boshqarish handleri.

Buyruqlar:
  /addchannel @username yoki channel_id  — kanal qo'shish (tur so'raladi)
  /removechannel @username yoki ID       — kanalni o'chirish (deaktivatsiya)
  /channels                              — barcha kanallar ro'yxati
  /channelstats channel_id               — bitta kanal statistikasi
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_IDS
from database import channel_queries
from services.channel_service import (
    CHANNEL_TYPES,
    TYPE_LABELS,
    register_channel,
)

router = Router()


# ─── FAQAT ADMIN FILTERI ──────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── FSM HOLATLARI ────────────────────────────

class AddChannelStates(StatesGroup):
    waiting_channel = State()
    waiting_type = State()


# ─── KANAL QO'SHISH ───────────────────────────

@router.message(Command("addchannel"))
async def cmd_addchannel(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📌 Kanal username yoki ID ni yuboring:\n"
            "<code>/addchannel @kanalUsername</code>\n"
            "<code>/addchannel -1001234567890</code>"
        )
        await state.set_state(AddChannelStates.waiting_channel)
        return

    await state.update_data(channel_input=args[1].strip())
    await _ask_channel_type(message, state)


@router.message(AddChannelStates.waiting_channel)
async def process_channel_input(message: Message, state: FSMContext) -> None:
    await state.update_data(channel_input=message.text.strip())
    await _ask_channel_type(message, state)


async def _ask_channel_type(message: Message, state: FSMContext) -> None:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"chtype:{key}")]
        for key, label in TYPE_LABELS.items()
    ]
    await message.answer(
        "📂 Kanal turini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await state.set_state(AddChannelStates.waiting_type)


@router.callback_query(F.data.startswith("chtype:"), AddChannelStates.waiting_type)
async def process_channel_type(callback: CallbackQuery, state: FSMContext, bot, pool) -> None:
    type_ = callback.data.split(":")[1]
    data = await state.get_data()
    channel_input = data.get("channel_input", "")

    await callback.message.edit_text("⏳ Kanal tekshirilmoqda...")

    result = await register_channel(bot, pool, channel_input, type_, callback.from_user.id)

    if result["ok"]:
        ch = result["channel"]
        mandatory_txt = "✅ Ha" if ch["is_mandatory"] else "❌ Yo'q"
        await callback.message.edit_text(
            f"✅ <b>Kanal qo'shildi!</b>\n\n"
            f"📌 <b>Nomi:</b> {ch['title']}\n"
            f"🔗 <b>Username:</b> {ch['username'] or '—'}\n"
            f"📂 <b>Tur:</b> {TYPE_LABELS.get(ch['type'], ch['type'])}\n"
            f"🔒 <b>Majburiy:</b> {mandatory_txt}"
        )
    else:
        await callback.message.edit_text(f"❌ Xato: {result['error']}")

    await state.clear()


# ─── KANAL O'CHIRISH ──────────────────────────

@router.message(Command("removechannel"))
async def cmd_removechannel(message: Message, bot, pool) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❗ Foydalanish: <code>/removechannel @username yoki -100ID</code>")
        return

    inp = args[1].strip()

    # Avval DB dan topamiz
    channels = await channel_queries.get_all_channels(pool)
    target = None
    for ch in channels:
        if inp.lstrip("@") == (ch["username"] or "").lstrip("@") or inp == str(ch["channel_id"]):
            target = ch
            break

    if not target:
        await message.answer("❌ Kanal topilmadi. /channels ro'yxatini ko'ring.")
        return

    ok = await channel_queries.remove_channel(pool, target["channel_id"])
    if ok:
        await message.answer(f"✅ <b>{target['title']}</b> o'chirildi (deaktivatsiya qilindi).")
    else:
        await message.answer("❌ O'chirishda xato.")


# ─── KANALLAR RO'YXATI ────────────────────────

@router.message(Command("channels"))
async def cmd_channels(message: Message, pool) -> None:
    if not is_admin(message.from_user.id):
        return

    channels = await channel_queries.get_all_channels(pool, only_active=False)
    if not channels:
        await message.answer("📭 Hech qanday kanal yo'q.\n/addchannel bilan qo'shing.")
        return

    lines = ["📋 <b>Barcha kanallar:</b>\n"]
    for ch in channels:
        status = "🟢" if ch["is_active"] else "🔴"
        mandatory = " 🔒" if ch["is_mandatory"] else ""
        label = TYPE_LABELS.get(ch["type"], ch["type"])
        username = f" · {ch['username']}" if ch["username"] else ""
        lines.append(
            f"{status} <b>{ch['title']}</b>{username}{mandatory}\n"
            f"   └ {label} · ID: <code>{ch['channel_id']}</code>"
        )

    await message.answer("\n".join(lines))


# ─── BITTA KANAL STATISTIKASI ─────────────────

@router.message(Command("channelstats"))
async def cmd_channel_stats(message: Message, pool) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❗ Foydalanish: <code>/channelstats -100ID</code>")
        return

    inp = args[1].strip()
    try:
        channel_id = int(inp)
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak.")
        return

    ch = await channel_queries.get_channel_by_id(pool, channel_id)
    if not ch:
        await message.answer("❌ Kanal topilmadi.")
        return

    stats = await channel_queries.get_channel_members_count(pool, channel_id)
    total = stats["checked"]
    members = stats["members"]
    non_members = stats["non_members"]
    pct = round(members / total * 100) if total else 0

    await message.answer(
        f"📊 <b>{ch['title']}</b> statistikasi:\n\n"
        f"✅ A'zo: <b>{members}</b>\n"
        f"❌ A'zo emas: <b>{non_members}</b>\n"
        f"📋 Tekshirilgan: <b>{total}</b>\n"
        f"📈 A'zolik darajasi: <b>{pct}%</b>"
    )
