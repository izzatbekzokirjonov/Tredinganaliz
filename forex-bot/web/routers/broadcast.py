import asyncio
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool
from database.queries import get_all_telegram_ids
from utils.logger import logger

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])


class BroadcastBody(BaseModel):
    text: str


@router.post("")
async def send_broadcast(
    body:    BroadcastBody,
    request: Request,
    pool:    asyncpg.Pool = Depends(get_pool),
    _:       dict = Depends(get_admin_user),
):
    if not body.text.strip():
        return {"ok": False, "error": "Matn bo'sh"}

    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        return {"ok": False, "error": "Bot ulangan emas"}

    user_ids = await get_all_telegram_ids(pool)
    sent = failed = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📣 <b>E'lon</b>\n\n{body.text}")
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast xato ({uid}): {e}")
        await asyncio.sleep(0.05)

    return {"ok": True, "sent": sent, "failed": failed, "total": len(user_ids)}
