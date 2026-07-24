from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncpg

from config import ADMIN_IDS, BOT_TOKEN
from web.auth import (
    create_token,
    get_admin_user,
    get_current_user,
    verify_telegram_auth,
    _role_from_tier,
)
from web.dependencies import get_pool
from database.queries import get_user

router = APIRouter(prefix="/api", tags=["auth & settings"])


# ─── AUTH ────────────────────────────────────────────────────────

class TelegramAuthData(BaseModel):
    id:         int
    first_name: str
    username:   str | None = None
    photo_url:  str | None = None
    auth_date:  int
    hash:       str


@router.post("/auth/telegram")
async def telegram_login(
    data: TelegramAuthData,
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Telegram Login Widget dan kelgan ma'lumotlarni tekshiradi va JWT beradi."""
    data_dict = data.model_dump()
    if not verify_telegram_auth(data_dict):
        raise HTTPException(401, "Telegram autentifikatsiya xato")

    db_user = await get_user(pool, data.id)
    tier    = db_user["subscription"] if db_user else "free"
    role    = _role_from_tier(tier, data.id)

    token = create_token(data.id, role)
    return {
        "token": token,
        "role":  role,
        "name":  data.first_name,
        "username": data.username or "",
    }


@router.get("/auth/me")
async def get_me(
    user: dict = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    tid = int(user["sub"])
    db_user = await get_user(pool, tid)
    return {
        "telegram_id": tid,
        "role":        user["role"],
        "name":        db_user["first_name"] if db_user else "—",
        "username":    db_user["username"]   if db_user else "",
        "tier":        db_user["subscription"] if db_user else "free",
    }


# ─── SETTINGS ────────────────────────────────────────────────────

class LimitsUpdate(BaseModel):
    free: int
    pro:  int


@router.get("/settings")
async def get_settings(_: dict = Depends(get_admin_user)):
    from config import TIER_DAILY_LIMITS, REFERRAL_REWARDS, SUPPORTED_PAIRS
    return {
        "limits":          TIER_DAILY_LIMITS,
        "referral_rewards":REFERRAL_REWARDS,
        "supported_pairs": SUPPORTED_PAIRS,
    }
