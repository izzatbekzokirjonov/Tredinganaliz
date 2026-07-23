from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool
from database import queries

router = APIRouter(prefix="/api/users", tags=["users"])


class PremiumGrantRequest(BaseModel):
    tier: str
    days: Optional[int] = None


@router.get("")
async def list_users(
    search:  str = Query("", max_length=64),
    tier:    str = Query("all"),
    page:    int = Query(1, ge=1),
    limit:   int = Query(20, ge=1, le=100),
    pool:    asyncpg.Pool = Depends(get_pool),
    _:       dict = Depends(get_admin_user),
):
    offset = (page - 1) * limit
    conditions = ["1=1"]
    params: list = []

    if search:
        params.append(f"%{search}%")
        idx = len(params)
        conditions.append(
            f"(first_name ILIKE ${idx} OR username ILIKE ${idx} "
            f"OR telegram_id::text LIKE ${idx})"
        )

    if tier != "all":
        params.append(tier)
        conditions.append(f"subscription = ${len(params)}")

    where = " AND ".join(conditions)

    total = await pool.fetchval(f"SELECT COUNT(*) FROM users WHERE {where}", *params)
    rows  = await pool.fetch(
        f"""
        SELECT u.*,
               (SELECT COUNT(*) FROM analysis_logs WHERE telegram_id = u.telegram_id) AS total_analyses
        FROM users u
        WHERE {where}
        ORDER BY joined_at DESC
        LIMIT {limit} OFFSET {offset}
        """,
        *params,
    )

    def fmt(r):
        return {
            "telegram_id":   r["telegram_id"],
            "first_name":    r["first_name"] or "—",
            "username":      r["username"]   or "",
            "subscription":  r["subscription"],
            "expires_at":    r["subscription_expires_at"].strftime("%d.%m.%Y") if r["subscription_expires_at"] else None,
            "referrals":     r["referrals"],
            "total_analyses":r["total_analyses"],
            "is_banned":     r["is_banned"],
            "joined_at":     r["joined_at"].strftime("%d.%m.%Y"),
        }

    return {"total": total, "page": page, "users": [fmt(r) for r in rows]}


@router.get("/{telegram_id}")
async def get_user(
    telegram_id: int,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    user = await queries.get_user(pool, telegram_id)
    if not user:
        raise HTTPException(404, "Topilmadi")

    total = await queries.count_analysis_total_by_user(pool, telegram_id)

    from database.channel_queries import get_user_channel_statuses
    ch_statuses = await get_user_channel_statuses(pool, telegram_id)

    return {
        "telegram_id":   user["telegram_id"],
        "first_name":    user["first_name"]  or "—",
        "username":      user["username"]    or "",
        "subscription":  user["subscription"],
        "expires_at":    user["subscription_expires_at"].strftime("%d.%m.%Y %H:%M") if user["subscription_expires_at"] else None,
        "referrals":     user["referrals"],
        "referred_by":   user["referred_by"],
        "total_analyses":total,
        "is_banned":     user["is_banned"],
        "joined_at":     user["joined_at"].strftime("%d.%m.%Y %H:%M"),
        "channels": [
            {
                "title":        s["title"],
                "username":     s["username"] or "",
                "is_mandatory": s["is_mandatory"],
                "is_member":    s["is_member"],
            }
            for s in ch_statuses
        ],
    }


@router.post("/{telegram_id}/premium")
async def give_premium(
    telegram_id: int,
    body: PremiumGrantRequest,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    user = await queries.get_user(pool, telegram_id)
    if not user:
        raise HTTPException(404, "Topilmadi")
    await queries.set_subscription(pool, telegram_id, body.tier, body.days, granted_by="web_admin")
    return {"ok": True}


@router.delete("/{telegram_id}/premium")
async def revoke_premium(
    telegram_id: int,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    await queries.set_subscription(pool, telegram_id, "free", None, granted_by="web_admin")
    return {"ok": True}


@router.post("/{telegram_id}/ban")
async def ban_user(
    telegram_id: int,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    ok = await queries.ban_user(pool, telegram_id)
    if not ok:
        raise HTTPException(404, "Topilmadi")
    return {"ok": True}


@router.post("/{telegram_id}/unban")
async def unban_user(
    telegram_id: int,
    pool: asyncpg.Pool = Depends(get_pool),
    _:    dict = Depends(get_admin_user),
):
    ok = await queries.unban_user(pool, telegram_id)
    if not ok:
        raise HTTPException(404, "Topilmadi")
    return {"ok": True}
