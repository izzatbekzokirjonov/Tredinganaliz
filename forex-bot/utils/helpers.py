from datetime import datetime
from typing import Optional


def format_datetime(dt: Optional[datetime]) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


def trend_to_uz(trend: str) -> str:
    return {"UP": "📈 Ko'tarilish", "DOWN": "📉 Tushish", "FLAT": "➡️ Yon tomon"}.get(trend, trend)


def tier_emoji(tier: str) -> str:
    return {"free": "🆓", "pro": "⭐", "vip": "💎"}.get(tier, "")
