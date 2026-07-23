from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool

router = APIRouter(prefix="/api/premium", tags=["premium"])


class GrantBody(BaseModel):
    telegram_id: int
    tier:        str
    days:        Optional[int] = None


@router.get("")
async def list_premium_users(
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    rows = await pool.fetch(
        """
        SELECT u.telegram_id, u.first_name, u.username,
               u.subscription, u.subscription_expires_at, u.joined_at,
               s.granted_by, s.created_at AS granted_at
        FROM users u
        LEFT JOIN LATERAL (
            SELECT granted_by, created_at FROM subscriptions
            WHERE telegram_id = u.telegram_id
            ORDER BY created_at DESC LIMIT 1
        ) s ON TRUE
        WHERE u.subscription != 'free'
        ORDER BY u.subscription DESC, u.subscription_expires_at ASC NULLS LAST
        """
    )
    return [
        {
            "telegram_id":  r["telegram_id"],
            "name":         r["first_name"] or "—",
            "username":     r["username"]   or "",
            "tier":         r["subscription"],
            "expires_at":   r["subscription_expires_at"].strftime("%d.%m.%Y") if r["subscription_expires_at"] else "Muddatsiz",
            "granted_by":   r["granted_by"] or "—",
            "granted_at":   r["granted_at"].strftime("%d.%m.%Y") if r["granted_at"] else "—",
        }
        for r in rows
    ]


@router.post("/grant")
async def grant_premium(
    body: GrantBody,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    from services.payment_service import grant_premium as _grant
    await _grant(pool, body.telegram_id, body.tier, body.days)
    return {"ok": True}


@router.post("/revoke/{telegram_id}")
async def revoke_premium(
    telegram_id: int,
    pool:        asyncpg.Pool = Depends(get_pool),
    _:           dict = Depends(get_admin_user),
):
    from services.payment_service import revoke_premium as _revoke
    await _revoke(pool, telegram_id)
    return {"ok": True}
