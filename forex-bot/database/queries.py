"""
Barcha SQL so'rovlari.
"""
from datetime import datetime, timedelta
from typing import Optional

import asyncpg

from config import TIER_DAILY_LIMITS


# ─── USERS ───────────────────────────────────────────────────────

async def create_or_update_user(
    pool: asyncpg.Pool,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    referred_by: Optional[int] = None,
) -> None:
    await pool.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, referred_by)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (telegram_id) DO UPDATE
        SET username = EXCLUDED.username,
            first_name = EXCLUDED.first_name
        """,
        telegram_id, username, first_name, referred_by,
    )


async def get_user(pool: asyncpg.Pool, telegram_id: int) -> Optional[asyncpg.Record]:
    await pool.execute(
        """
        UPDATE users SET subscription = 'free', subscription_expires_at = NULL
        WHERE telegram_id = $1
          AND subscription_expires_at IS NOT NULL
          AND subscription_expires_at < NOW()
        """,
        telegram_id,
    )
    return await pool.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)


async def ban_user(pool: asyncpg.Pool, telegram_id: int) -> bool:
    r = await pool.execute(
        "UPDATE users SET is_banned = TRUE WHERE telegram_id = $1", telegram_id
    )
    return r != "UPDATE 0"


async def unban_user(pool: asyncpg.Pool, telegram_id: int) -> bool:
    r = await pool.execute(
        "UPDATE users SET is_banned = FALSE WHERE telegram_id = $1", telegram_id
    )
    return r != "UPDATE 0"


async def get_effective_tier(pool: asyncpg.Pool, telegram_id: int) -> str:
    user = await get_user(pool, telegram_id)
    return user["subscription"] if user else "free"


# ─── SUBSCRIPTIONS ───────────────────────────────────────────────

async def set_subscription(
    pool: asyncpg.Pool,
    telegram_id: int,
    tier: str,
    days: Optional[int],
    granted_by: str,
    extend: bool = False,
) -> None:
    expires_at = None
    if days is not None:
        if extend:
            user = await get_user(pool, telegram_id)
            now = datetime.utcnow()
            base = (
                user["subscription_expires_at"]
                if user
                and user["subscription_expires_at"]
                and user["subscription_expires_at"] > now
                else now
            )
            expires_at = base + timedelta(days=days)
        else:
            expires_at = datetime.utcnow() + timedelta(days=days)

    await pool.execute(
        """
        UPDATE users SET subscription = $1, subscription_expires_at = $2
        WHERE telegram_id = $3
        """,
        tier, expires_at, telegram_id,
    )
    await pool.execute(
        """
        INSERT INTO subscriptions (telegram_id, tier, granted_by, expires_at)
        VALUES ($1, $2, $3, $4)
        """,
        telegram_id, tier, granted_by, expires_at,
    )


# ─── ANALYSIS LOGS ───────────────────────────────────────────────

async def log_analysis(pool: asyncpg.Pool, telegram_id: int, pair: str) -> None:
    await pool.execute(
        "INSERT INTO analysis_logs (telegram_id, pair) VALUES ($1, $2)",
        telegram_id, pair,
    )


async def count_analysis_today(pool: asyncpg.Pool, telegram_id: int) -> int:
    return await pool.fetchval(
        """
        SELECT COUNT(*) FROM analysis_logs
        WHERE telegram_id = $1 AND created_at::date = NOW()::date
        """,
        telegram_id,
    )


async def count_analysis_total_by_user(pool: asyncpg.Pool, telegram_id: int) -> int:
    return await pool.fetchval(
        "SELECT COUNT(*) FROM analysis_logs WHERE telegram_id = $1", telegram_id
    )


async def get_remaining_limit(pool: asyncpg.Pool, telegram_id: int) -> Optional[int]:
    tier = await get_effective_tier(pool, telegram_id)
    limit = TIER_DAILY_LIMITS.get(tier)
    if limit is None:
        return None
    used = await count_analysis_today(pool, telegram_id)
    return max(limit - used, 0)


# ─── SIGNALS ─────────────────────────────────────────────────────

async def add_signal(
    pool: asyncpg.Pool,
    pair: str,
    direction: str,
    entry: float,
    tp: float,
    sl: float,
    comment: str,
    created_by: int,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO signals (pair, direction, entry, tp, sl, comment, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        pair, direction, entry, tp, sl, comment, created_by,
    )


async def get_recent_signals(pool: asyncpg.Pool, limit: int = 10) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM signals ORDER BY created_at DESC LIMIT $1", limit
    )


# ─── REFERRALS ───────────────────────────────────────────────────

async def add_referral(
    pool: asyncpg.Pool, referrer_id: int, referred_id: int
) -> Optional[int]:
    try:
        await pool.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES ($1, $2)",
            referrer_id, referred_id,
        )
    except asyncpg.UniqueViolationError:
        return None

    return await pool.fetchval(
        """
        UPDATE users SET referrals = referrals + 1
        WHERE telegram_id = $1 RETURNING referrals
        """,
        referrer_id,
    )


async def get_referral_count(pool: asyncpg.Pool, telegram_id: int) -> int:
    user = await get_user(pool, telegram_id)
    return user["referrals"] if user else 0


# ─── ADMIN STATS ─────────────────────────────────────────────────

async def count_users(pool: asyncpg.Pool) -> int:
    return await pool.fetchval("SELECT COUNT(*) FROM users")


async def count_premium_users(pool: asyncpg.Pool) -> dict[str, int]:
    rows = await pool.fetch(
        "SELECT subscription, COUNT(*) AS c FROM users GROUP BY subscription"
    )
    return {row["subscription"]: row["c"] for row in rows}


async def count_total_analyses(pool: asyncpg.Pool) -> int:
    return await pool.fetchval("SELECT COUNT(*) FROM analysis_logs")


async def get_all_telegram_ids(pool: asyncpg.Pool) -> list[int]:
    rows = await pool.fetch(
        "SELECT telegram_id FROM users WHERE is_banned = FALSE"
    )
    return [row["telegram_id"] for row in rows]
