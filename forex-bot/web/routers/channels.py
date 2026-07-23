from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool
from database import channel_queries

router = APIRouter(prefix="/api/channels", tags=["channels"])


class ChannelCreate(BaseModel):
    channel_input: str   # @username yoki -100ID
    type: str            # mandatory | signal | lesson | info


class ChannelUpdate(BaseModel):
    type:         str
    is_mandatory: bool


@router.get("")
async def list_channels(
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    rows = await channel_queries.get_all_channels(pool, only_active=False)
    result = []
    for r in rows:
        stats = await channel_queries.get_channel_members_count(pool, r["channel_id"])
        result.append({
            "id":           r["id"],
            "channel_id":   r["channel_id"],
            "title":        r["title"],
            "username":     r["username"] or "",
            "type":         r["type"],
            "is_mandatory": r["is_mandatory"],
            "is_active":    r["is_active"],
            "added_at":     r["added_at"].strftime("%d.%m.%Y"),
            "members":      stats["members"],
            "non_members":  stats["non_members"],
            "checked":      stats["checked"],
        })
    return result


@router.post("")
async def add_channel(
    body:    ChannelCreate,
    request: Request,
    pool:    asyncpg.Pool = Depends(get_pool),
    user:    dict = Depends(get_admin_user),
):
    from services.channel_service import register_channel
    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(503, "Bot ulangan emas")

    result = await register_channel(
        bot, pool, body.channel_input, body.type, int(user["sub"])
    )
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return {"ok": True}


@router.patch("/{channel_id}")
async def update_channel(
    channel_id: int,
    body:       ChannelUpdate,
    pool:       asyncpg.Pool = Depends(get_pool),
    _:          dict = Depends(get_admin_user),
):
    ok = await channel_queries.update_channel_type(
        pool, channel_id, body.type, body.is_mandatory
    )
    if not ok:
        raise HTTPException(404, "Kanal topilmadi")
    return {"ok": True}


@router.delete("/{channel_id}")
async def remove_channel(
    channel_id: int,
    pool:       asyncpg.Pool = Depends(get_pool),
    _:          dict = Depends(get_admin_user),
):
    ok = await channel_queries.remove_channel(pool, channel_id)
    if not ok:
        raise HTTPException(404, "Kanal topilmadi")
    return {"ok": True}
