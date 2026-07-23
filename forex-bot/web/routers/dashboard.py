from fastapi import APIRouter, Depends
import asyncpg

from web.auth import get_admin_user
from web.dependencies import get_pool

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    pool: asyncpg.Pool = Depends(get_pool),
    _: dict = Depends(get_admin_user),
):
    total_users   = await pool.fetchval("SELECT COUNT(*) FROM users")
    total_analyses= await pool.fetchval("SELECT COUNT(*) FROM analysis_logs")
    today_analyses= await pool.fetchval(
        "SELECT COUNT(*) FROM analysis_logs WHERE created_at::date = NOW()::date"
    )
    screenshots   = await pool.fetchval(
        "SELECT COUNT(*) FROM analysis_logs WHERE pair = 'SCREENSHOT'"
    )

    tiers = await pool.fetch(
        "SELECT subscription, COUNT(*) AS c FROM users GROUP BY subscription"
    )
    tier_map = {r["subscription"]: r["c"] for r in tiers}

    # Oxirgi 10 kun tahlillar
    daily = await pool.fetch(
        """
        SELECT created_at::date AS day, COUNT(*) AS c
        FROM analysis_logs
        WHERE created_at >= NOW() - INTERVAL '10 days'
        GROUP BY day ORDER BY day
        """
    )

    # So'nggi faoliyat
    recent = await pool.fetch(
        """
        SELECT u.first_name, u.username, u.subscription, u.joined_at
        FROM users u ORDER BY u.joined_at DESC LIMIT 5
        """
    )

    signals_count = await pool.fetchval(
        "SELECT COUNT(*) FROM signals WHERE created_at >= NOW() - INTERVAL '24 hours'"
    )

    return {
        "total_users":    total_users,
        "total_analyses": total_analyses,
        "today_analyses": today_analyses,
        "screenshots":    screenshots,
        "signals_24h":    signals_count,
        "tiers": {
            "free":  tier_map.get("free", 0),
            "pro":   tier_map.get("pro",  0),
            "vip":   tier_map.get("vip",  0),
        },
        "daily_analyses": [
            {"day": str(r["day"]), "count": r["c"]} for r in daily
        ],
        "recent_users": [
            {
                "name":       r["first_name"] or "—",
                "username":   r["username"]   or "",
                "tier":       r["subscription"],
                "joined_at":  r["joined_at"].strftime("%d.%m.%Y %H:%M"),
            }
            for r in recent
        ],
    }
