from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool
from database import queries

router = APIRouter(prefix="/api/signals", tags=["signals"])


class SignalCreate(BaseModel):
    pair:      str
    direction: str
    entry:     float
    tp:        float
    sl:        float
    comment:   Optional[str] = ""


@router.get("")
async def list_signals(
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    rows = await queries.get_recent_signals(pool, limit=50)
    return [
        {
            "id":         r["id"],
            "pair":       r["pair"],
            "direction":  r["direction"],
            "entry":      float(r["entry"]),
            "tp":         float(r["tp"]),
            "sl":         float(r["sl"]),
            "comment":    r["comment"] or "",
            "created_at": r["created_at"].strftime("%d.%m.%Y %H:%M"),
        }
        for r in rows
    ]


@router.post("")
async def create_signal(
    body:    SignalCreate,
    pool:    asyncpg.Pool = Depends(get_pool),
    user:    dict = Depends(get_admin_user),
):
    signal = await queries.add_signal(
        pool,
        pair=body.pair.upper(),
        direction=body.direction.upper(),
        entry=body.entry,
        tp=body.tp,
        sl=body.sl,
        comment=body.comment or "",
        created_by=int(user["sub"]),
    )
    return {"ok": True, "id": signal["id"]}


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    pool:      asyncpg.Pool = Depends(get_pool),
    _:         dict = Depends(get_admin_user),
):
    result = await pool.execute(
        "DELETE FROM signals WHERE id = $1", signal_id
    )
    if result == "DELETE 0":
        raise HTTPException(404, "Signal topilmadi")
    return {"ok": True}
